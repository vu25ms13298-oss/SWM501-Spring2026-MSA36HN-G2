import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import require_roles
from app.models.user import User
from app.models.session import Session, InstructorAvailability, AvailabilityStatus, SessionStatus
from app.models.booking import Booking, BookingStatus
from app.schemas.instructor import AvailabilityCreateRequest, AvailabilityResponse, ScheduleSessionResponse

router = APIRouter(prefix="/instructor", tags=["instructor"])


@router.get("/schedule", response_model=List[ScheduleSessionResponse])
async def get_instructor_schedule(
    week: str = Query(..., description="ISO week in YYYY-WW format"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("instructor", "admin")),
):
    from datetime import datetime, timedelta, timezone
    import re

    match = re.match(r"(\d{4})-(\d{2})", week)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid week format. Use YYYY-WW")

    year, week_num = int(match.group(1)), int(match.group(2))
    week_start = datetime.fromisocalendar(year, week_num, 1).replace(tzinfo=timezone.utc)
    week_end = week_start + timedelta(days=7)

    instructor_id = current_user.id
    result = await db.execute(
        select(Session)
        .options(
            selectinload(Session.vehicle),
            selectinload(Session.bookings).selectinload(Booking.learner),
        )
        .where(
            and_(
                Session.instructor_id == instructor_id,
                Session.slot_start >= week_start,
                Session.slot_start < week_end,
                Session.status != SessionStatus.cancelled,
            )
        )
        .order_by(Session.slot_start)
    )
    sessions = result.scalars().all()

    return [
        ScheduleSessionResponse(
            session_id=s.id,
            slot_start=s.slot_start,
            slot_end=s.slot_end,
            vehicle_plate=s.vehicle.plate,
            vehicle_type=s.vehicle.type.value,
            learner_count=sum(1 for b in s.bookings if b.status == BookingStatus.confirmed),
            status=s.status.value,
            skill_levels=[
                b.learner.skill_level.value
                for b in s.bookings
                if b.status == BookingStatus.confirmed and b.learner and b.learner.skill_level
            ],
        )
        for s in sessions
    ]


@router.post("/availability", response_model=List[AvailabilityResponse], status_code=201)
async def create_availability(
    slots: List[AvailabilityCreateRequest],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("instructor")),
):
    created = []
    for slot_req in slots:
        slot = InstructorAvailability(
            id=str(uuid.uuid4()),
            instructor_id=current_user.id,
            slot_start=slot_req.slot_start,
            slot_end=slot_req.slot_end,
            status=AvailabilityStatus.available,
        )
        db.add(slot)
        created.append(slot)

    await db.commit()
    for s in created:
        await db.refresh(s)

    return [
        AvailabilityResponse(
            id=s.id,
            instructor_id=s.instructor_id,
            slot_start=s.slot_start,
            slot_end=s.slot_end,
            status=s.status.value,
        )
        for s in created
    ]


@router.delete("/availability/{slot_id}", status_code=204)
async def delete_availability(
    slot_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("instructor")),
):
    result = await db.execute(
        select(InstructorAvailability).where(
            and_(
                InstructorAvailability.id == slot_id,
                InstructorAvailability.instructor_id == current_user.id,
            )
        )
    )
    slot = result.scalar_one_or_none()
    if not slot:
        raise HTTPException(status_code=404, detail="Availability slot not found")

    if slot.status == AvailabilityStatus.booked:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete slot with existing bookings (BR-09)",
        )

    await db.delete(slot)
    await db.commit()
