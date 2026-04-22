from typing import List
from datetime import datetime
from pydantic import BaseModel


class AvailabilityCreateRequest(BaseModel):
    slot_start: datetime
    slot_end: datetime


class AvailabilityResponse(BaseModel):
    id: str
    instructor_id: str
    slot_start: datetime
    slot_end: datetime
    status: str

    class Config:
        from_attributes = True


class ScheduleSessionResponse(BaseModel):
    session_id: str
    slot_start: datetime
    slot_end: datetime
    vehicle_plate: str
    vehicle_type: str
    learner_count: int
    status: str
    skill_levels: List[str] = []
