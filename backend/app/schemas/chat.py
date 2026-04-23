from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class ChatMessageRequest(BaseModel):
    conversation_id: str
    message: str


class ChatMessageResponse(BaseModel):
    conversation_id: str
    response: str
    intent: Optional[str] = None
    escalated: bool = False
    api_limited: bool = False
    suggested_questions: List[str] = []


class ChatHistoryItem(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class EscalateRequest(BaseModel):
    conversation_id: str
    reason: Optional[str] = None
