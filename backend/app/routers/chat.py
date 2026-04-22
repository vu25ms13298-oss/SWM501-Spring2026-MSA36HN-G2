from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.chat import ChatMessage
from app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatHistoryItem,
    EscalateRequest,
)
from app.services import chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await chat_service.process_message(
        db=db,
        conversation_id=request.conversation_id,
        message=request.message,
        user=current_user,
    )


@router.get("/history/{conversation_id}", response_model=List[ChatHistoryItem])
async def get_history(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at)
    )
    messages = result.scalars().all()
    return [
        ChatHistoryItem(
            id=m.id,
            role=m.role.value,
            content=m.content,
            created_at=m.created_at,
        )
        for m in messages
    ]


@router.post("/escalate")
async def escalate(
    request: EscalateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await chat_service.escalate_conversation(
        db=db,
        conversation_id=request.conversation_id,
        reason=request.reason,
        user=current_user,
    )
