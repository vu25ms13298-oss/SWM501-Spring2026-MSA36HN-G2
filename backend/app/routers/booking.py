from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.user import User
from app.schemas.booking import SlotResponse, CreateBookingRequest, BookingResponse
from app.services import booking_service

router = APIRouter(tags=["booking"])


@router.get("/slots", response_model=List[SlotResponse])
async def get_slots(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.user import UserRole
    skill = current_user.skill_level if current_user.role == UserRole.learner else None
    return await booking_service.get_available_slots(db, date, skill)


@router.post("/bookings", response_model=BookingResponse, status_code=201)
async def create_booking(
    request: CreateBookingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("learner")),
):
    booking = await booking_service.create_booking(db, current_user, request.session_id)
    return BookingResponse(
        id=booking.id,
        session_id=booking.session_id,
        learner_id=booking.learner_id,
        status=booking.status.value,
        booked_at=booking.booked_at,
    )


@router.delete("/bookings/{booking_id}", response_model=BookingResponse)
async def cancel_booking(
    booking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("learner")),
):
    return await booking_service.cancel_booking(db, booking_id, current_user)


@router.get("/bookings/me", response_model=List[BookingResponse])
async def get_my_bookings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("learner")),
):
    return await booking_service.get_my_bookings(db, current_user.id)
