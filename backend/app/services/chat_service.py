import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.chat import ChatMessage, MessageRole
from app.models.user import User
from app.services import rag_service

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Bạn là trợ lý AI của trường lái xe thông minh SDS (Smart Driving School).
Chỉ trả lời dựa trên thông tin được cung cấp trong context bên dưới.

Quy tắc bắt buộc (BR-05):
- Nếu context không đủ thông tin, BẮT BUỘC trả lời: "Xin lỗi, tôi không có thông tin về vấn đề này. Vui lòng liên hệ nhân viên hỗ trợ."
- KHÔNG được bịa thêm thông tin ngoài context.
- Trả lời bằng tiếng Việt, ngắn gọn và thân thiện.
"""

INTENT_PROMPT = """Phân loại câu hỏi sau vào một trong các intent:
- booking_query: hỏi về lịch học, đặt lịch, hủy lịch của học viên
- progress_query: hỏi về tiến độ học, bài học đã hoàn thành
- fee_query: hỏi về học phí, tín chỉ, thanh toán
- general_faq: câu hỏi chung về trường lái xe, quy định, thủ tục

Chỉ trả về đúng một trong bốn từ: booking_query, progress_query, fee_query, general_faq

Câu hỏi: {message}"""


def _get_llm():
    if not settings.GEMINI_API_KEY:
        return None
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.3,
        )
    except Exception as e:
        logger.warning(f"Could not init LLM: {e}")
        return None


async def _detect_intent(llm, message: str) -> str:
    try:
        from langchain_core.messages import HumanMessage
        response = await llm.ainvoke([HumanMessage(content=INTENT_PROMPT.format(message=message))])
        intent = response.content.strip().lower()
        valid = {"booking_query", "progress_query", "fee_query", "general_faq"}
        return intent if intent in valid else "general_faq"
    except Exception as e:
        logger.warning(f"Intent detection failed: {e}")
        return "general_faq"


async def _log_message(db: AsyncSession, conversation_id: str, role: MessageRole, content: str):
    msg = ChatMessage(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        role=role,
        content=content,
        created_at=datetime.now(timezone.utc),
    )
    db.add(msg)
    await db.commit()


async def process_message(
    db: AsyncSession,
    conversation_id: str,
    message: str,
    user: User,
) -> dict:
    # Log user message
    await _log_message(db, conversation_id, MessageRole.user, message)

    llm = _get_llm()

    if llm is None:
        response_text = (
            "Xin lỗi, dịch vụ AI hiện chưa được cấu hình. "
            "Vui lòng liên hệ nhân viên hỗ trợ hoặc thiết lập GEMINI_API_KEY."
        )
        await _log_message(db, conversation_id, MessageRole.assistant, response_text)
        return {
            "conversation_id": conversation_id,
            "response": response_text,
            "intent": None,
            "escalated": False,
        }

    intent = await _detect_intent(llm, message)
    context_text = ""
    escalated = False

    if intent == "booking_query":
        # Pull user's bookings from DB
        from app.services.booking_service import get_my_bookings
        from app.models.user import UserRole
        if user.role == UserRole.learner:
            bookings = await get_my_bookings(db, user.id)
            if bookings:
                lines = []
                for b in bookings[:5]:
                    start = b["session_start"].strftime("%d/%m/%Y %H:%M") if b.get("session_start") else "?"
                    lines.append(
                        f"- Buổi {start} với GV {b.get('instructor_name', '?')}, xe {b.get('vehicle_plate', '?')}, trạng thái: {b['status']}"
                    )
                context_text = "Lịch học của học viên:\n" + "\n".join(lines)
            else:
                context_text = "Học viên chưa có lịch học nào."
        else:
            context_text = "Bạn không phải học viên nên không có thông tin lịch học cá nhân."
    else:
        # RAG retrieval
        chunks = await rag_service.retrieve_similar_chunks(db, message, top_k=5)
        if chunks:
            context_text = "\n\n".join(c.chunk_text for c in chunks)

    # Generate response
    try:
        from langchain_core.messages import SystemMessage, HumanMessage
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=f"Context:\n{context_text}\n\nCâu hỏi: {message}"
            ),
        ]
        response = await llm.ainvoke(messages)
        response_text = response.content.strip()

        # BR-05 confidence check: escalate if response is the fallback
        if "không có thông tin" in response_text and "nhân viên hỗ trợ" in response_text:
            escalated = True
    except Exception as e:
        logger.error(f"LLM generation error: {e}")
        response_text = (
            "Xin lỗi, tôi không có thông tin về vấn đề này. Vui lòng liên hệ nhân viên hỗ trợ."
        )
        escalated = True

    await _log_message(db, conversation_id, MessageRole.assistant, response_text)

    return {
        "conversation_id": conversation_id,
        "response": response_text,
        "intent": intent,
        "escalated": escalated,
    }


async def escalate_conversation(
    db: AsyncSession,
    conversation_id: str,
    reason: Optional[str],
    user: User,
) -> dict:
    note = reason or "Học viên yêu cầu hỗ trợ từ nhân viên"
    content = f"[ESCALATED] {note}"
    await _log_message(db, conversation_id, MessageRole.staff, content)
    return {
        "conversation_id": conversation_id,
        "status": "escalated",
        "message": "Cuộc hội thoại đã được chuyển cho nhân viên hỗ trợ.",
    }
