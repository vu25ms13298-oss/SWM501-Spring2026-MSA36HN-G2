import uuid
from enum import Enum

from sqlalchemy import String, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class VehicleType(str, Enum):
    manual = "manual"
    automatic = "automatic"


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    type: Mapped[VehicleType] = mapped_column(SAEnum(VehicleType, name="vehicle_type"), nullable=False)
    plate: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)

    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="vehicle")
