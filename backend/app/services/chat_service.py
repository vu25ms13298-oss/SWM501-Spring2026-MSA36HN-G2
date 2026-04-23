import uuid
import logging
import unicodedata
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
            model="gemini-2.5-flash",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.3,
        )
    except Exception as e:
        logger.warning(f"Could not init LLM: {e}")
        return None


def _is_rate_limit_error(error: Exception) -> bool:
    error_str = str(error).lower()
    return any(
        phrase in error_str
        for phrase in ["rate_limit", "quota", "429", "too_many_requests", "resource_exhausted", "request limit"]
    )


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower().strip())
    without_marks = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    without_marks = without_marks.replace("đ", "d").replace("Đ", "D")
    return " ".join(without_marks.split())


def _is_asking_name(message: str) -> bool:
    normalized = _normalize_text(message)
    patterns = [
        "ten toi",
        "toi la ai",
        "my name",
    ]
    return any(p in normalized for p in patterns)


def _is_asking_next_session(message: str) -> bool:
    normalized = _normalize_text(message)
    direct_patterns = [
        "khoa hoc tiep theo",
        "buoi hoc tiep theo",
        "lich hoc tiep theo",
        "lich hoc sap toi",
        "ca hoc tiep theo",
    ]
    if any(p in normalized for p in direct_patterns):
        return True

    has_course_or_schedule = any(
        token in normalized
        for token in ["khoa hoc", "buoi hoc", "lich hoc", "ca hoc"]
    )
    has_next_time = any(token in normalized for token in ["tiep theo", "sap toi", "ke tiep"])
    return has_course_or_schedule and has_next_time


def _is_asking_today_schedule(message: str) -> bool:
    normalized = _normalize_text(message)
    has_schedule = any(token in normalized for token in ["lich", "lich hoc", "buoi hoc", "ca hoc", "khoa hoc"])
    has_today = any(token in normalized for token in ["hom nay", "ngay hom nay", "today"])
    return has_schedule and has_today


def _is_asking_reschedule_contact(message: str) -> bool:
    normalized = _normalize_text(message)
    has_reschedule_phrase = any(
        token in normalized
        for token in ["doi lich", "chuyen lich", "doi buoi", "reschedule", "huy lich"]
    )
    has_reschedule_by_words = (
        any(token in normalized for token in ["doi", "chuyen", "huy", "doi lich", "reschedule"])
        and any(token in normalized for token in ["lich", "buoi", "ca hoc", "khoa hoc"])
    )
    has_reschedule = has_reschedule_phrase or has_reschedule_by_words
    has_contact = any(
        token in normalized
        for token in ["nhan ai", "lien he ai", "chat ai", "goi ai", "nhan vien", "ho tro"]
    )
    has_schedule_ref = any(
        token in normalized
        for token in ["lich tiep theo", "buoi tiep theo", "khoa hoc tiep theo", "lich hoc"]
    )
    return has_reschedule and (has_contact or has_schedule_ref)


async def _handle_personal_query(db: AsyncSession, message: str, user: User) -> Optional[dict]:
    from app.models.user import UserRole
    from app.services.booking_service import get_my_bookings

    if _is_asking_name(message):
        response = f"Bạn là {user.name} ({user.email}). Mình đang hỗ trợ bạn trong vai trò {user.role.value}."
        return {
            "response": response,
            "intent": "profile_query",
            "escalated": False,
            "api_limited": False,
            "suggested_questions": [],
        }

    if _is_asking_next_session(message):
        if user.role != UserRole.learner:
            return {
                "response": "Bạn không phải học viên nên không có lịch học cá nhân. Hãy xem lịch giảng dạy ở trang phù hợp với vai trò của bạn.",
                "intent": "booking_query",
                "escalated": False,
                "api_limited": False,
                "suggested_questions": [],
            }

        bookings = await get_my_bookings(db, user.id)
        now = datetime.now(timezone.utc)
        upcoming = []
        for b in bookings:
            if b.get("status") != "confirmed":
                continue
            start = b.get("session_start")
            if start is None:
                continue
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            if start >= now:
                upcoming.append((start, b))

        if not upcoming:
            return {
                "response": "Hiện tại bạn chưa có buổi học sắp tới. Bạn có thể vào trang Đặt lịch để chọn ca học mới.",
                "intent": "booking_query",
                "escalated": False,
                "api_limited": False,
                "suggested_questions": [],
            }

        upcoming.sort(key=lambda item: item[0])
        start, item = upcoming[0]
        response = (
            f"Buổi học gần nhất của bạn là lúc {start.strftime('%H:%M %d/%m/%Y')} "
            f"với GV {item.get('instructor_name', '?')}, xe {item.get('vehicle_plate', '?')}."
        )
        return {
            "response": response,
            "intent": "booking_query",
            "escalated": False,
            "api_limited": False,
            "suggested_questions": [],
        }

    if _is_asking_today_schedule(message):
        if user.role != UserRole.learner:
            return {
                "response": "Bạn không phải học viên nên không có lịch học cá nhân hôm nay.",
                "intent": "booking_query",
                "escalated": False,
                "api_limited": False,
                "suggested_questions": [],
            }

        bookings = await get_my_bookings(db, user.id)
        today = datetime.now(timezone.utc).date()
        today_items = []

        for b in bookings:
            if b.get("status") != "confirmed":
                continue
            start = b.get("session_start")
            if start is None:
                continue
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            if start.date() == today:
                today_items.append((start, b))

        if not today_items:
            return {
                "response": "Hôm nay bạn chưa có buổi học nào. Bạn có thể kiểm tra lịch sắp tới hoặc đặt thêm ca học mới.",
                "intent": "booking_query",
                "escalated": False,
                "api_limited": False,
                "suggested_questions": [],
            }

        today_items.sort(key=lambda item: item[0])
        lines = []
        for start, item in today_items[:3]:
            lines.append(
                f"- {start.strftime('%H:%M')} với GV {item.get('instructor_name', '?')}, xe {item.get('vehicle_plate', '?')}"
            )
        response = "Lịch học hôm nay của bạn:\n" + "\n".join(lines)
        return {
            "response": response,
            "intent": "booking_query",
            "escalated": False,
            "api_limited": False,
            "suggested_questions": [],
        }

    if _is_asking_reschedule_contact(message):
        response = (
            "Nếu bạn muốn đổi lịch học sắp tới, hãy nhắn Nhân viên hỗ trợ ngay trong khung chat này "
            "(nút 'Nhân viên' ở góc trên). Bạn cũng có thể hủy lịch trong trang 'Lịch học của tôi' "
            "rồi đặt lại ca mới phù hợp."
        )
        return {
            "response": response,
            "intent": "booking_query",
            "escalated": False,
            "api_limited": False,
            "suggested_questions": [],
        }

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

    # Fast path for personalized questions to avoid unnecessary fallback.
    personal_result = await _handle_personal_query(db, message, user)
    if personal_result:
        await _log_message(db, conversation_id, MessageRole.assistant, personal_result["response"])
        return {
            "conversation_id": conversation_id,
            **personal_result,
        }

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
    api_limited = False
    suggested_questions = []

    user_context = (
        f"Nguoi dung hien tai: {user.name} ({user.email}), vai tro: {user.role.value}, "
        f"trinh do: {user.skill_level.value if user.skill_level else 'N/A'}, tin chi con lai: {user.lesson_credits}."
    )

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

    context_text = f"{user_context}\n\n{context_text}" if context_text else user_context

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
        if _is_rate_limit_error(e):
            api_limited = True
            response_text = (
                "He thong dang ban. Vui long chon mot trong cac cau hoi thuong gap ben duoi hoac thu lai sau it phut."
            )
            suggested_questions = [
                "Lam sao de dat lich hoc?",
                "Toi con bao nhieu tin chi?",
                "Toi co the huy lich khong?",
            ]
        else:
            response_text = (
                "Xin loi, toi khong co thong tin ve van de nay. Vui long lien he nhan vien ho tro."
            )
            escalated = True

    await _log_message(db, conversation_id, MessageRole.assistant, response_text)

    return {
        "conversation_id": conversation_id,
        "response": response_text,
        "intent": intent,
        "escalated": escalated,
        "api_limited": api_limited,
        "suggested_questions": suggested_questions,
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
