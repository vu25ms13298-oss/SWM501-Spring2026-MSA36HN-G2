import uuid
from enum import Enum
from datetime import datetime

from sqlalchemy import ForeignKey, Enum as SAEnum, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class AvailabilityStatus(str, Enum):
    available = "available"
    booked = "booked"
    cancelled = "cancelled"


class SessionStatus(str, Enum):
    confirmed = "confirmed"
    pending_reassignment = "pending_reassignment"
    cancelled = "cancelled"


class InstructorAvailability(Base):
    __tablename__ = "instructor_availability"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    instructor_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    slot_start: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    slot_end: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    status: Mapped[AvailabilityStatus] = mapped_column(
        SAEnum(AvailabilityStatus, name="availability_status"),
        default=AvailabilityStatus.available,
    )

    instructor: Mapped["User"] = relationship("User", back_populates="availability_slots")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    instructor_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=False
    )
    vehicle_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("vehicles.id"), nullable=False
    )
    slot_start: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    slot_end: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    status: Mapped[SessionStatus] = mapped_column(
        SAEnum(SessionStatus, name="session_status"),
        default=SessionStatus.confirmed,
    )

    instructor: Mapped["User"] = relationship("User", back_populates="taught_sessions")
    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="sessions")
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="session")
