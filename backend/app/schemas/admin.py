from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class ForecastWeek(BaseModel):
    week: str
    predicted_bookings: float
    instructor_capacity: int
    alert: bool


class SessionOverrideRequest(BaseModel):
    instructor_id: Optional[str] = None
    status: Optional[str] = None


class AdminSessionResponse(BaseModel):
    id: str
    instructor_id: str
    instructor_name: str
    vehicle_id: str
    vehicle_plate: str
    slot_start: datetime
    slot_end: datetime
    status: str
    booking_count: int


class KBDocumentResponse(BaseModel):
    id: str
    source_file: str
    chunk_count: int
