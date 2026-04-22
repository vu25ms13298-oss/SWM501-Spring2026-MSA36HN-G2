from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import require_roles
from app.models.user import User
from app.models.session import Session, SessionStatus
from app.models.booking import Booking, BookingStatus
from app.models.vehicle import Vehicle
from app.schemas.admin import ForecastWeek, SessionOverrideRequest, AdminSessionResponse
from app.services import forecast_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/forecast", response_model=List[ForecastWeek])
async def get_forecast(
    weeks: int = Query(default=2, ge=1, le=8),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    return await forecast_service.get_forecast(db, weeks)


@router.get("/sessions", response_model=List[AdminSessionResponse])
async def list_sessions(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    query = (
        select(Session)
        .options(
            selectinload(Session.instructor),
            selectinload(Session.vehicle),
            selectinload(Session.bookings),
        )
        .order_by(Session.slot_start.desc())
    )
    if status:
        try:
            status_enum = SessionStatus(status)
            query = query.where(Session.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status value")

    result = await db.execute(query)
    sessions = result.scalars().all()

    return [
        AdminSessionResponse(
            id=s.id,
            instructor_id=s.instructor_id,
            instructor_name=s.instructor.name,
            vehicle_id=s.vehicle_id,
            vehicle_plate=s.vehicle.plate,
            slot_start=s.slot_start,
            slot_end=s.slot_end,
            status=s.status.value,
            booking_count=sum(1 for b in s.bookings if b.status == BookingStatus.confirmed),
        )
        for s in sessions
    ]


@router.put("/sessions/{session_id}", response_model=AdminSessionResponse)
async def override_session(
    session_id: str,
    request: SessionOverrideRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    result = await db.execute(
        select(Session)
        .options(
            selectinload(Session.instructor),
            selectinload(Session.vehicle),
            selectinload(Session.bookings),
        )
        .where(Session.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if request.instructor_id:
        instructor_result = await db.execute(
            select(User).where(User.id == request.instructor_id)
        )
        instructor = instructor_result.scalar_one_or_none()
        if not instructor:
            raise HTTPException(status_code=404, detail="Instructor not found")
        session.instructor_id = request.instructor_id
        session.instructor = instructor

    if request.status:
        try:
            session.status = SessionStatus(request.status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")

    await db.commit()
    await db.refresh(session)

    return AdminSessionResponse(
        id=session.id,
        instructor_id=session.instructor_id,
        instructor_name=session.instructor.name,
        vehicle_id=session.vehicle_id,
        vehicle_plate=session.vehicle.plate,
        slot_start=session.slot_start,
        slot_end=session.slot_end,
        status=session.status.value,
        booking_count=sum(1 for b in session.bookings if b.status == BookingStatus.confirmed),
    )
