import uuid
from enum import Enum

from sqlalchemy import String, Integer, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class UserRole(str, Enum):
    learner = "learner"
    instructor = "instructor"
    admin = "admin"
    support = "support"


class SkillLevel(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole, name="user_role"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    skill_level: Mapped[SkillLevel | None] = mapped_column(
        SAEnum(SkillLevel, name="skill_level"), nullable=True
    )
    lesson_credits: Mapped[int] = mapped_column(Integer, default=0)

    bookings: Mapped[list["Booking"]] = relationship(
        "Booking", back_populates="learner", foreign_keys="Booking.learner_id"
    )
    availability_slots: Mapped[list["InstructorAvailability"]] = relationship(
        "InstructorAvailability", back_populates="instructor"
    )
    taught_sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="instructor"
    )
