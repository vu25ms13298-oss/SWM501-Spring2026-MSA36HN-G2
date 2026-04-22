from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.booking import Booking, BookingStatus
from app.models.user import User, UserRole


async def get_forecast(db: AsyncSession, weeks: int = 2) -> List[dict]:
    now = datetime.now(timezone.utc)

    # Get instructor count
    instructor_count_result = await db.execute(
        select(func.count()).select_from(User).where(User.role == UserRole.instructor)
    )
    instructor_count = instructor_count_result.scalar() or 0
    # Assume each instructor handles ~5 sessions/week, each session holds 3 learners
    slots_per_instructor_per_week = 5
    capacity_per_week = instructor_count * slots_per_instructor_per_week * 3

    # Collect booking counts for last 8 weeks to compute moving average
    history = []
    for i in range(8, 0, -1):
        week_start = now - timedelta(weeks=i)
        week_end = week_start + timedelta(weeks=1)
        count_result = await db.execute(
            select(func.count())
            .select_from(Booking)
            .where(
                and_(
                    Booking.booked_at >= week_start,
                    Booking.booked_at < week_end,
                    Booking.status == BookingStatus.confirmed,
                )
            )
        )
        history.append(count_result.scalar() or 0)

    # Moving average of last 4 weeks as base prediction
    window = history[-4:] if len(history) >= 4 else history
    avg = sum(window) / len(window) if window else 0

    forecast = []
    for i in range(1, weeks + 1):
        future_start = now + timedelta(weeks=i - 1)
        iso_year, iso_week, _ = future_start.isocalendar()
        predicted = round(avg * (1 + 0.05 * i), 1)  # slight growth trend
        alert = predicted > capacity_per_week

        forecast.append(
            {
                "week": f"{iso_year}-{iso_week:02d}",
                "predicted_bookings": predicted,
                "instructor_capacity": capacity_per_week,
                "alert": alert,
            }
        )

    return forecast
