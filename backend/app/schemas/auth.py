from typing import Optional
from pydantic import BaseModel, EmailStr

from app.models.user import SkillLevel


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    skill_level: Optional[SkillLevel] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str
    name: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    skill_level: Optional[str] = None
    lesson_credits: int

    class Config:
        from_attributes = True
