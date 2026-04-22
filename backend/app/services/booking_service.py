from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.models.booking import Booking, BookingStatus
from app.models.session import Session, SessionStatus
from app.models.user import User, SkillLevel

MAX_CAPACITY = 3
MIN_ADVANCE_HOURS = 12


async def get_available_slots(
    db: AsyncSession,
    date: str,
    skill_level: Optional[SkillLevel] = None,
):
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    start = target_date.replace(tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    min_slot_start = datetime.now(timezone.utc) + timedelta(hours=MIN_ADVANCE_HOURS)

    result = await db.execute(
        select(Session)
        .options(
            selectinload(Session.instructor),
            selectinload(Session.vehicle),
            selectinload(Session.bookings).selectinload(Booking.learner),
        )
        .where(
            and_(
                Session.slot_start >= start,
                Session.slot_start < end,
                Session.slot_start >= min_slot_start,
                Session.status == SessionStatus.confirmed,
            )
        )
        .order_by(Session.slot_start)
    )
    sessions = result.scalars().all()

    slots = []
    for session in sessions:
        confirmed = [b for b in session.bookings if b.status == BookingStatus.confirmed]
        available = MAX_CAPACITY - len(confirmed)
        if available <= 0:
            continue

        same_skill = 0
        if skill_level and confirmed:
            same_skill = sum(
                1 for b in confirmed if b.learner and b.learner.skill_level == skill_level
            )
            score = same_skill / len(confirmed)
        elif not confirmed:
            score = 0.5
        else:
            score = 0.0

        slots.append(
            {
                "session_id": session.id,
                "instructor_id": session.instructor_id,
                "instructor_name": session.instructor.name,
                "vehicle_id": session.vehicle_id,
                "vehicle_type": session.vehicle.type.value,
                "vehicle_plate": session.vehicle.plate,
                "slot_start": session.slot_start,
                "slot_end": session.slot_end,
                "available_spots": available,
                "total_capacity": MAX_CAPACITY,
                "best_match_score": score,
                "learner_count_same_skill": same_skill,
            }
        )

    slots.sort(key=lambda x: x["best_match_score"], reverse=True)
    return slots


async def create_booking(db: AsyncSession, learner: User, session_id: str) -> Booking:
    result = await db.execute(
        select(Session).where(Session.id == session_id).with_for_update()
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != SessionStatus.confirmed:
        raise HTTPException(status_code=400, detail="Session is not available")

    now = datetime.now(timezone.utc)
    slot_start = session.slot_start
    if slot_start.tzinfo is None:
        slot_start = slot_start.replace(tzinfo=timezone.utc)

    if slot_start < now + timedelta(hours=MIN_ADVANCE_HOURS):
        raise HTTPException(
            status_code=400,
            detail="Booking must be made at least 12 hours in advance (FR-01)",
        )

    count_result = await db.execute(
        select(func.count())
        .select_from(Booking)
        .where(
            and_(
                Booking.session_id == session_id,
                Booking.status == BookingStatus.confirmed,
            )
        )
    )
    if count_result.scalar() >= MAX_CAPACITY:
        raise HTTPException(status_code=400, detail="Session is at full capacity (FR-02)")

    existing_result = await db.execute(
        select(Booking).where(
            and_(
                Booking.learner_id == learner.id,
                Booking.session_id == session_id,
                Booking.status == BookingStatus.confirmed,
            )
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already booked this session")

    if learner.lesson_credits <= 0:
        raise HTTPException(status_code=400, detail="Insufficient lesson credits")

    booking = Booking(
        learner_id=learner.id,
        session_id=session_id,
        status=BookingStatus.confirmed,
        booked_at=now,
    )
    db.add(booking)
    learner.lesson_credits -= 1
    db.add(learner)
    await db.commit()
    await db.refresh(booking)
    return booking


async def cancel_booking(db: AsyncSession, booking_id: str, learner: User) -> dict:
    result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.session))
        .where(
            and_(
                Booking.id == booking_id,
                Booking.learner_id == learner.id,
                Booking.status == BookingStatus.confirmed,
            )
        )
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    now = datetime.now(timezone.utc)
    slot_start = booking.session.slot_start
    if slot_start.tzinfo is None:
        slot_start = slot_start.replace(tzinfo=timezone.utc)

    hours_until = (slot_start - now).total_seconds() / 3600

    # BR-03: Penalty logic
    if hours_until > 12:
        credit_adjustment = 1  # Full refund
    elif hours_until > 2:
        credit_adjustment = 0  # No refund
    else:
        credit_adjustment = -1  # Penalty

    booking.status = BookingStatus.cancelled
    booking.cancelled_at = now
    learner.lesson_credits = max(0, learner.lesson_credits + credit_adjustment)
    db.add(learner)
    await db.commit()

    return {
        "id": booking.id,
        "session_id": booking.session_id,
        "learner_id": booking.learner_id,
        "status": "cancelled",
        "booked_at": booking.booked_at,
        "cancelled_at": booking.cancelled_at,
        "credit_adjustment": credit_adjustment,
    }


async def get_my_bookings(db: AsyncSession, learner_id: str) -> list:
    result = await db.execute(
        select(Booking)
        .options(
            selectinload(Booking.session).selectinload(Session.instructor),
            selectinload(Booking.session).selectinload(Session.vehicle),
        )
        .where(Booking.learner_id == learner_id)
        .order_by(Booking.booked_at.desc())
    )
    bookings = result.scalars().all()

    return [
        {
            "id": b.id,
            "session_id": b.session_id,
            "learner_id": b.learner_id,
            "status": b.status.value,
            "booked_at": b.booked_at,
            "cancelled_at": b.cancelled_at,
            "session_start": b.session.slot_start,
            "session_end": b.session.slot_end,
            "instructor_name": b.session.instructor.name,
            "vehicle_plate": b.session.vehicle.plate,
        }
        for b in bookings
    ]
