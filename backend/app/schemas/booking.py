from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class SlotResponse(BaseModel):
    session_id: str
    instructor_id: str
    instructor_name: str
    vehicle_id: str
    vehicle_type: str
    vehicle_plate: str
    slot_start: datetime
    slot_end: datetime
    available_spots: int
    total_capacity: int
    best_match_score: float
    learner_count_same_skill: int


class CreateBookingRequest(BaseModel):
    session_id: str


class BookingResponse(BaseModel):
    id: str
    session_id: str
    learner_id: str
    status: str
    booked_at: datetime
    cancelled_at: Optional[datetime] = None
    session_start: Optional[datetime] = None
    session_end: Optional[datetime] = None
    instructor_name: Optional[str] = None
    vehicle_plate: Optional[str] = None
    credit_adjustment: Optional[int] = None

    class Config:
        from_attributes = True
