"""
Seed script — creates demo data if database is empty.
Users, vehicles, sessions, bookings, chat history, knowledge base.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

logger = logging.getLogger(__name__)

ADMIN_ID = "00000000-0000-0000-0000-000000000001"
SUPPORT_ID = "00000000-0000-0000-0000-000000000002"
INSTR_IDS = [
    "00000000-0000-0000-0001-000000000001",
    "00000000-0000-0000-0001-000000000002",
    "00000000-0000-0000-0001-000000000003",
]
LEARNER_IDS = [
    "00000000-0000-0000-0002-000000000001",
    "00000000-0000-0000-0002-000000000002",
    "00000000-0000-0000-0002-000000000003",
    "00000000-0000-0000-0002-000000000004",
    "00000000-0000-0000-0002-000000000005",
    "00000000-0000-0000-0002-000000000006",
    "00000000-0000-0000-0002-000000000007",
    "00000000-0000-0000-0002-000000000008",
    "00000000-0000-0000-0002-000000000009",
    "00000000-0000-0000-0002-000000000010",
]
VEHICLE_IDS = [
    "00000000-0000-0000-0003-000000000001",
    "00000000-0000-0000-0003-000000000002",
    "00000000-0000-0000-0003-000000000003",
    "00000000-0000-0000-0003-000000000004",
    "00000000-0000-0000-0003-000000000005",
]


async def seed_if_empty():
    from app.core.database import AsyncSessionLocal
    from app.models.user import User

    async with AsyncSessionLocal() as db:
        count = (await db.execute(select(func.count()).select_from(User))).scalar()
        if count and count > 0:
            logger.info("Database already seeded, skipping.")
            return

        logger.info("Seeding database...")
        await _do_seed(db)
        logger.info("Seeding complete.")


async def _do_seed(db):
    from app.core.security import get_password_hash
    from app.models.booking import Booking, BookingStatus
    from app.models.chat import ChatMessage, MessageRole
    from app.models.knowledge import KnowledgeChunk
    from app.models.session import AvailabilityStatus, InstructorAvailability, Session, SessionStatus
    from app.models.user import SkillLevel, User, UserRole
    from app.models.vehicle import Vehicle, VehicleType

    now = datetime.now(timezone.utc)

    users = [
        User(id=ADMIN_ID, role=UserRole.admin, name="Admin SDS", email="admin@sds.vn", password_hash=get_password_hash("admin123"), lesson_credits=0),
        User(id=SUPPORT_ID, role=UserRole.support, name="Nhan vien Ho tro", email="support@sds.vn", password_hash=get_password_hash("support123"), lesson_credits=0),
        User(id=INSTR_IDS[0], role=UserRole.instructor, name="Nguyen Van An", email="instructor1@sds.vn", password_hash=get_password_hash("instructor123")),
        User(id=INSTR_IDS[1], role=UserRole.instructor, name="Tran Thi Bich", email="instructor2@sds.vn", password_hash=get_password_hash("instructor123")),
        User(id=INSTR_IDS[2], role=UserRole.instructor, name="Le Van Cuong", email="instructor3@sds.vn", password_hash=get_password_hash("instructor123")),
        User(id=LEARNER_IDS[0], role=UserRole.learner, name="Pham Thi Dung", email="learner1@sds.vn", password_hash=get_password_hash("learner123"), skill_level=SkillLevel.beginner, lesson_credits=10),
        User(id=LEARNER_IDS[1], role=UserRole.learner, name="Hoang Van Em", email="learner2@sds.vn", password_hash=get_password_hash("learner123"), skill_level=SkillLevel.beginner, lesson_credits=8),
        User(id=LEARNER_IDS[2], role=UserRole.learner, name="Nguyen Thi Phuong", email="learner3@sds.vn", password_hash=get_password_hash("learner123"), skill_level=SkillLevel.intermediate, lesson_credits=12),
        User(id=LEARNER_IDS[3], role=UserRole.learner, name="Tran Van Giang", email="learner4@sds.vn", password_hash=get_password_hash("learner123"), skill_level=SkillLevel.intermediate, lesson_credits=5),
        User(id=LEARNER_IDS[4], role=UserRole.learner, name="Le Thi Hong", email="learner5@sds.vn", password_hash=get_password_hash("learner123"), skill_level=SkillLevel.advanced, lesson_credits=15),
        User(id=LEARNER_IDS[5], role=UserRole.learner, name="Vo Thanh Tuan", email="learner6@sds.vn", password_hash=get_password_hash("learner123"), skill_level=SkillLevel.beginner, lesson_credits=10),
        User(id=LEARNER_IDS[6], role=UserRole.learner, name="Dang Thi Linh", email="learner7@sds.vn", password_hash=get_password_hash("learner123"), skill_level=SkillLevel.intermediate, lesson_credits=14),
        User(id=LEARNER_IDS[7], role=UserRole.learner, name="Bui Van Huy", email="learner8@sds.vn", password_hash=get_password_hash("learner123"), skill_level=SkillLevel.beginner, lesson_credits=6),
        User(id=LEARNER_IDS[8], role=UserRole.learner, name="Truong Ngoc Anh", email="learner9@sds.vn", password_hash=get_password_hash("learner123"), skill_level=SkillLevel.advanced, lesson_credits=20),
        User(id=LEARNER_IDS[9], role=UserRole.learner, name="Dinh Quoc Cuong", email="learner10@sds.vn", password_hash=get_password_hash("learner123"), skill_level=SkillLevel.intermediate, lesson_credits=8),
    ]
    db.add_all(users)
    await db.flush()

    vehicles = [
        Vehicle(id=VEHICLE_IDS[0], type=VehicleType.manual, plate="51A-12345"),
        Vehicle(id=VEHICLE_IDS[1], type=VehicleType.manual, plate="51A-12346"),
        Vehicle(id=VEHICLE_IDS[2], type=VehicleType.manual, plate="51A-12347"),
        Vehicle(id=VEHICLE_IDS[3], type=VehicleType.automatic, plate="51B-54321"),
        Vehicle(id=VEHICLE_IDS[4], type=VehicleType.automatic, plate="51B-54322"),
    ]
    db.add_all(vehicles)
    await db.flush()

    days_until_monday = (7 - now.weekday()) % 7 or 7
    next_monday = (now + timedelta(days=days_until_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
    times = [(8, 0), (10, 0), (14, 0)]
    instructor_cycle = [INSTR_IDS[0], INSTR_IDS[1], INSTR_IDS[2]]
    vehicle_cycle = [VEHICLE_IDS[0], VEHICLE_IDS[1], VEHICLE_IDS[2], VEHICLE_IDS[3], VEHICLE_IDS[4]]

    session_slots = []
    idx = 0
    for week in range(3):
        for day in range(6):
            for hour, minute in times:
                slot_start = next_monday + timedelta(weeks=week, days=day, hours=hour, minutes=minute)
                slot_end = slot_start + timedelta(hours=1)
                session_slots.append(
                    Session(
                        id=f"00000000-0000-0000-0004-{idx + 1:012d}",
                        instructor_id=instructor_cycle[idx % len(instructor_cycle)],
                        vehicle_id=vehicle_cycle[idx % len(vehicle_cycle)],
                        slot_start=slot_start,
                        slot_end=slot_end,
                        status=SessionStatus.confirmed,
                    )
                )
                idx += 1

    db.add_all(session_slots)
    await db.flush()

    past_sessions = []
    for week_offset in range(1, 5):
        for day_offset in range(3):
            past_start = (now - timedelta(weeks=week_offset, days=day_offset)).replace(hour=8, minute=0, second=0, microsecond=0)
            past_sessions.append(
                Session(
                    id=str(uuid.uuid4()),
                    instructor_id=instructor_cycle[day_offset % len(instructor_cycle)],
                    vehicle_id=vehicle_cycle[day_offset % len(vehicle_cycle)],
                    slot_start=past_start,
                    slot_end=past_start + timedelta(hours=1),
                    status=SessionStatus.confirmed,
                )
            )

    db.add_all(past_sessions)
    await db.flush()

    db.add_all([
        InstructorAvailability(
            id=str(uuid.uuid4()),
            instructor_id=session.instructor_id,
            slot_start=session.slot_start,
            slot_end=session.slot_end,
            status=AvailabilityStatus.available,
        )
        for session in session_slots
    ])
    await db.flush()

    booking_plan = [
        (LEARNER_IDS[0], 0), (LEARNER_IDS[0], 1), (LEARNER_IDS[0], 8),
        (LEARNER_IDS[1], 0), (LEARNER_IDS[1], 2), (LEARNER_IDS[1], 12),
        (LEARNER_IDS[2], 1), (LEARNER_IDS[2], 3), (LEARNER_IDS[2], 15),
        (LEARNER_IDS[3], 0), (LEARNER_IDS[3], 4), (LEARNER_IDS[3], 18),
        (LEARNER_IDS[4], 2), (LEARNER_IDS[4], 5), (LEARNER_IDS[4], 20),
        (LEARNER_IDS[5], 6), (LEARNER_IDS[5], 9), (LEARNER_IDS[5], 24),
        (LEARNER_IDS[6], 7), (LEARNER_IDS[6], 10), (LEARNER_IDS[6], 26),
        (LEARNER_IDS[7], 3), (LEARNER_IDS[7], 11), (LEARNER_IDS[7], 28),
        (LEARNER_IDS[8], 4), (LEARNER_IDS[8], 13), (LEARNER_IDS[8], 30),
        (LEARNER_IDS[9], 5), (LEARNER_IDS[9], 14), (LEARNER_IDS[9], 32),
        (LEARNER_IDS[0], 16), (LEARNER_IDS[1], 17), (LEARNER_IDS[2], 19),
        (LEARNER_IDS[3], 21), (LEARNER_IDS[4], 22), (LEARNER_IDS[5], 23),
        (LEARNER_IDS[6], 25), (LEARNER_IDS[7], 27), (LEARNER_IDS[8], 29),
        (LEARNER_IDS[9], 31), (LEARNER_IDS[0], 33), (LEARNER_IDS[1], 34),
        (LEARNER_IDS[2], 35), (LEARNER_IDS[3], 36), (LEARNER_IDS[4], 37),
        (LEARNER_IDS[5], 38), (LEARNER_IDS[6], 39), (LEARNER_IDS[7], 40),
    ]
    bookings = [
        Booking(
            id=str(uuid.uuid4()),
            learner_id=learner_id,
            session_id=session_slots[session_idx].id,
            status=BookingStatus.confirmed,
            booked_at=now - timedelta(days=1),
        )
        for learner_id, session_idx in booking_plan
    ]

    for index, session in enumerate(past_sessions):
        bookings.append(
            Booking(
                id=str(uuid.uuid4()),
                learner_id=LEARNER_IDS[index % len(LEARNER_IDS)],
                session_id=session.id,
                status=BookingStatus.confirmed,
                booked_at=session.slot_start - timedelta(days=2),
            )
        )

    db.add_all(bookings)
    await db.flush()

    sample_conv_id = str(uuid.uuid4())
    db.add_all([
        ChatMessage(id=str(uuid.uuid4()), conversation_id=sample_conv_id, role=MessageRole.user, content="Hoc phi mot buoi hoc la bao nhieu?", created_at=now - timedelta(hours=2)),
        ChatMessage(id=str(uuid.uuid4()), conversation_id=sample_conv_id, role=MessageRole.assistant, content="Mot tin chi tuong duong mot buoi hoc 60 phut. Ban co the xem so tin chi con lai trong trang hoc vien.", created_at=now - timedelta(hours=1, minutes=59)),
        ChatMessage(id=str(uuid.uuid4()), conversation_id=sample_conv_id, role=MessageRole.user, content="Toi co the huy lich hoc khong?", created_at=now - timedelta(hours=1)),
        ChatMessage(id=str(uuid.uuid4()), conversation_id=sample_conv_id, role=MessageRole.assistant, content="Ban co the huy lich hoc truoc 12 gio de duoc hoan tin chi day du. Huy qua sat gio hoc se khong duoc hoan tin chi.", created_at=now - timedelta(minutes=59)),
    ])
    await db.flush()

    kb_text = _get_sample_kb_text()
    for index, chunk in enumerate(_simple_chunk(kb_text)):
        db.add(
            KnowledgeChunk(
                id=str(uuid.uuid4()),
                source_file="driving_school_policy.md",
                chunk_text=chunk,
                embedding=None,
                metadata_={"chunk_index": index, "total_chunks": len(_simple_chunk(kb_text))},
            )
        )

    await db.commit()


def _simple_chunk(text: str, size: int = 400) -> list[str]:
    words = text.split()
    return [" ".join(words[index:index + size]) for index in range(0, len(words), size)]


def _get_sample_kb_text() -> str:
    return """
# Chinh sach Truong Lai xe Thong minh SDS

## 1. Dat lich hoc
- Hoc vien phai dat lich truoc it nhat 12 gio so voi gio hoc.
- Moi buoi hoc keo dai 60 phut.
- Moi ca hoc toi da 3 hoc vien cung trinh do.
- He thong tu dong ghep hoc vien cung trinh do de toi uu hoc tap.

## 2. Huy lich va hoan tin chi
- Huy truoc hon 12 gio: hoan lai 1 tin chi day du.
- Huy trong vong 2 den 12 gio: khong hoan tin chi.
- Huy trong vong 2 gio cuoi: mat them 1 tin chi.

## 3. Tin chi hoc
- Moi tin chi tuong duong 1 buoi hoc 60 phut.
- Hoc vien moi nhan 10 tin chi mien phi khi dang ky.
- Tin chi co the mua them tai quay ho tro.

## 4. Trinh do hoc vien
- Beginner: hoc tu co ban.
- Intermediate: hoan thien ky nang.
- Advanced: hoc ky nang nang cao.

## 5. Xe hoc
- Xe so san phu hop cho thi bang B2.
- Xe so tu dong phu hop cho nhu cau di lai hang ngay.
- Hoc vien khong duoc chon xe, he thong tu phan cong.

## 6. Giao vien
- Moi giao vien huong dan toi da 3 hoc vien moi ca.
- Giao vien co the dang ky lich ranh va huy lich chua co hoc vien.
- Khong the huy lich da co hoc vien dang ky.

## 7. Ho tro
- Email: support@sds.vn
- Hotline: 1900-SDS-001.
"""
