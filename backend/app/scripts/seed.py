"""
Seed script — creates demo data if database is empty.
Users, vehicles, sessions, bookings, chat history, knowledge base.
"""

import uuid
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func

logger = logging.getLogger(__name__)

# ── fixed IDs for deterministic seeding ──────────────────────────────────────
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
    from app.models.user import User, UserRole, SkillLevel
    from app.models.vehicle import Vehicle, VehicleType
    from app.models.session import Session, SessionStatus, InstructorAvailability, AvailabilityStatus
    from app.models.booking import Booking, BookingStatus
    from app.models.chat import ChatMessage, MessageRole
    from app.models.knowledge import KnowledgeChunk

    now = datetime.now(timezone.utc)

    # ── Users ─────────────────────────────────────────────────────────────────
    users = [
        User(id=ADMIN_ID, role=UserRole.admin, name="Admin SDS", email="admin@sds.vn",
             password_hash=get_password_hash("admin123"), lesson_credits=0),
        User(id=SUPPORT_ID, role=UserRole.support, name="Nhân viên Hỗ trợ", email="support@sds.vn",
             password_hash=get_password_hash("support123"), lesson_credits=0),
        User(id=INSTR_IDS[0], role=UserRole.instructor, name="Nguyễn Văn An",
             email="instructor1@sds.vn", password_hash=get_password_hash("instructor123")),
        User(id=INSTR_IDS[1], role=UserRole.instructor, name="Trần Thị Bích",
             email="instructor2@sds.vn", password_hash=get_password_hash("instructor123")),
        User(id=INSTR_IDS[2], role=UserRole.instructor, name="Lê Văn Cường",
             email="instructor3@sds.vn", password_hash=get_password_hash("instructor123")),
        User(id=LEARNER_IDS[0], role=UserRole.learner, name="Phạm Thị Dung",
             email="learner1@sds.vn", password_hash=get_password_hash("learner123"),
             skill_level=SkillLevel.beginner, lesson_credits=10),
        User(id=LEARNER_IDS[1], role=UserRole.learner, name="Hoàng Văn Em",
             email="learner2@sds.vn", password_hash=get_password_hash("learner123"),
             skill_level=SkillLevel.beginner, lesson_credits=8),
        User(id=LEARNER_IDS[2], role=UserRole.learner, name="Nguyễn Thị Phương",
             email="learner3@sds.vn", password_hash=get_password_hash("learner123"),
             skill_level=SkillLevel.intermediate, lesson_credits=12),
        User(id=LEARNER_IDS[3], role=UserRole.learner, name="Trần Văn Giang",
             email="learner4@sds.vn", password_hash=get_password_hash("learner123"),
             skill_level=SkillLevel.intermediate, lesson_credits=5),
        User(id=LEARNER_IDS[4], role=UserRole.learner, name="Lê Thị Hồng",
             email="learner5@sds.vn", password_hash=get_password_hash("learner123"),
             skill_level=SkillLevel.advanced, lesson_credits=15),
    ]
    db.add_all(users)
    await db.flush()

    # ── Vehicles ──────────────────────────────────────────────────────────────
    vehicles = [
        Vehicle(id=VEHICLE_IDS[0], type=VehicleType.manual, plate="51A-12345"),
        Vehicle(id=VEHICLE_IDS[1], type=VehicleType.manual, plate="51A-12346"),
        Vehicle(id=VEHICLE_IDS[2], type=VehicleType.manual, plate="51A-12347"),
        Vehicle(id=VEHICLE_IDS[3], type=VehicleType.automatic, plate="51B-54321"),
        Vehicle(id=VEHICLE_IDS[4], type=VehicleType.automatic, plate="51B-54322"),
    ]
    db.add_all(vehicles)
    await db.flush()

    # ── Sessions: 20 sessions over next 14 days ───────────────────────────────
    session_slots = []
    # Find next Monday
    days_until_monday = (7 - now.weekday()) % 7 or 7
    next_monday = (now + timedelta(days=days_until_monday)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    # 2 weeks of sessions, Mon-Sat, 3 time slots per day
    times = [(8, 0), (10, 0), (14, 0)]
    instructor_cycle = [INSTR_IDS[0], INSTR_IDS[1], INSTR_IDS[2]]
    vehicle_cycle = [VEHICLE_IDS[0], VEHICLE_IDS[1], VEHICLE_IDS[2], VEHICLE_IDS[3], VEHICLE_IDS[4]]

    idx = 0
    for week in range(2):
        for day in range(6):  # Mon-Sat
            if idx >= 20:
                break
            for hour, minute in times:
                if idx >= 20:
                    break
                slot_start = next_monday + timedelta(weeks=week, days=day, hours=hour, minutes=minute)
                slot_end = slot_start + timedelta(hours=1)
                session = Session(
                    id=f"00000000-0000-0000-0004-{idx + 1:012d}",
                    instructor_id=instructor_cycle[idx % 3],
                    vehicle_id=vehicle_cycle[idx % 5],
                    slot_start=slot_start,
                    slot_end=slot_end,
                    status=SessionStatus.confirmed,
                )
                session_slots.append(session)
                idx += 1

    db.add_all(session_slots)
    await db.flush()

    # ── Past sessions for forecast data ──────────────────────────────────────
    past_sessions = []
    for pw in range(4):
        for pd in range(3):
            past_start = now - timedelta(weeks=pw + 1, days=pd, hours=0)
            past_start = past_start.replace(hour=8, minute=0, second=0, microsecond=0)
            ps = Session(
                id=str(uuid.uuid4()),
                instructor_id=instructor_cycle[pd % 3],
                vehicle_id=vehicle_cycle[pd % 5],
                slot_start=past_start,
                slot_end=past_start + timedelta(hours=1),
                status=SessionStatus.confirmed,
            )
            past_sessions.append(ps)
    db.add_all(past_sessions)
    await db.flush()

    # ── InstructorAvailability ────────────────────────────────────────────────
    avail_slots = []
    for s in session_slots:
        avail = InstructorAvailability(
            id=str(uuid.uuid4()),
            instructor_id=s.instructor_id,
            slot_start=s.slot_start,
            slot_end=s.slot_end,
            status=AvailabilityStatus.available,
        )
        avail_slots.append(avail)
    db.add_all(avail_slots)
    await db.flush()

    # ── Bookings: 15 bookings distributed across sessions ─────────────────────
    booking_plan = [
        (LEARNER_IDS[0], 0), (LEARNER_IDS[0], 1),
        (LEARNER_IDS[1], 0), (LEARNER_IDS[1], 2),
        (LEARNER_IDS[2], 1), (LEARNER_IDS[2], 3),
        (LEARNER_IDS[3], 0), (LEARNER_IDS[3], 4),
        (LEARNER_IDS[4], 2), (LEARNER_IDS[4], 5),
        (LEARNER_IDS[0], 6), (LEARNER_IDS[1], 7),
        (LEARNER_IDS[2], 8), (LEARNER_IDS[3], 9),
        (LEARNER_IDS[4], 10),
    ]
    bookings = []
    for learner_id, session_idx in booking_plan:
        b = Booking(
            id=str(uuid.uuid4()),
            learner_id=learner_id,
            session_id=session_slots[session_idx].id,
            status=BookingStatus.confirmed,
            booked_at=now - timedelta(days=1),
        )
        bookings.append(b)

    # Past bookings for forecast history
    for i, ps in enumerate(past_sessions):
        learner_id = LEARNER_IDS[i % 5]
        pb = Booking(
            id=str(uuid.uuid4()),
            learner_id=learner_id,
            session_id=ps.id,
            status=BookingStatus.confirmed,
            booked_at=ps.slot_start - timedelta(days=2),
        )
        bookings.append(pb)

    db.add_all(bookings)
    await db.flush()

    # ── Sample chat history ───────────────────────────────────────────────────
    sample_conv_id = str(uuid.uuid4())
    chat_msgs = [
        ChatMessage(id=str(uuid.uuid4()), conversation_id=sample_conv_id,
                    role=MessageRole.user, content="Học phí một buổi học là bao nhiêu?",
                    created_at=now - timedelta(hours=2)),
        ChatMessage(id=str(uuid.uuid4()), conversation_id=sample_conv_id,
                    role=MessageRole.assistant,
                    content="Một tín chỉ học tương đương một buổi học 60 phút. Bạn có thể xem số tín chỉ còn lại trong trang học viên.",
                    created_at=now - timedelta(hours=2, minutes=-1)),
        ChatMessage(id=str(uuid.uuid4()), conversation_id=sample_conv_id,
                    role=MessageRole.user, content="Tôi có thể hủy lịch học không?",
                    created_at=now - timedelta(hours=1)),
        ChatMessage(id=str(uuid.uuid4()), conversation_id=sample_conv_id,
                    role=MessageRole.assistant,
                    content="Bạn có thể hủy lịch học trước 12 giờ để được hoàn trả tín chỉ đầy đủ. Hủy trước 2 giờ sẽ không được hoàn tín chỉ.",
                    created_at=now - timedelta(hours=1, minutes=-1)),
    ]
    db.add_all(chat_msgs)
    await db.flush()

    # ── Sample knowledge base (no embeddings — Gemini key may not be set) ─────
    kb_text = _get_sample_kb_text()
    chunks = _simple_chunk(kb_text)
    for i, chunk in enumerate(chunks):
        kc = KnowledgeChunk(
            id=str(uuid.uuid4()),
            source_file="driving_school_policy.md",
            chunk_text=chunk,
            embedding=None,
            metadata_={"chunk_index": i, "total_chunks": len(chunks)},
        )
        db.add(kc)

    await db.commit()


def _simple_chunk(text: str, size: int = 400) -> list[str]:
    words = text.split()
    return [" ".join(words[i:i + size]) for i in range(0, len(words), size)]


def _get_sample_kb_text() -> str:
    return """
# Chính sách Trường Lái xe Thông minh SDS

## 1. Đặt lịch học
- Học viên phải đặt lịch trước ít nhất 12 giờ so với giờ học.
- Mỗi buổi học kéo dài 60 phút (1 tiếng).
- Mỗi ca học tối đa 3 học viên cùng trình độ.
- Hệ thống tự động ghép học viên cùng trình độ để tối ưu học tập.

## 2. Hủy lịch và hoàn tín chỉ (BR-03)
- Hủy trước hơn 12 giờ: Hoàn lại 1 tín chỉ đầy đủ.
- Hủy trong vòng 2–12 giờ: Không hoàn tín chỉ.
- Hủy trong vòng 2 giờ cuối: Mất thêm 1 tín chỉ (phạt).

## 3. Tín chỉ học
- Mỗi tín chỉ tương đương 1 buổi học 60 phút.
- Học viên mới nhận 10 tín chỉ miễn phí khi đăng ký.
- Tín chỉ không có thời hạn sử dụng.
- Có thể mua thêm tín chỉ tại quầy hỗ trợ hoặc qua ứng dụng.

## 4. Trình độ học viên
- Sơ cấp (Beginner): Chưa biết lái xe, học từ cơ bản.
- Trung cấp (Intermediate): Đã biết lái, cần hoàn thiện kỹ năng.
- Nâng cao (Advanced): Học kỹ năng lái xe nâng cao, thành thục.

## 5. Xe học
- Xe số sàn (Manual): Phù hợp cho thi bằng B2.
- Xe số tự động (Automatic): Phù hợp cho người lái xe thường ngày.
- Học viên không được chọn xe, hệ thống tự phân công.

## 6. Giáo viên
- Mỗi giáo viên hướng dẫn tối đa 3 học viên/ca.
- Giáo viên có thể đăng ký lịch rảnh hoặc hủy lịch chưa có học viên.
- Không thể hủy lịch đã có học viên đăng ký.

## 7. Quy định lái xe trên đường
- Học viên phải đeo dây an toàn trong suốt buổi học.
- Không sử dụng điện thoại khi lái xe.
- Tuân thủ tín hiệu đèn giao thông và biển báo.
- Giáo viên có quyền dừng buổi học nếu học viên vi phạm quy định an toàn.

## 8. Liên hệ hỗ trợ
- Email: support@sds.vn
- Hotline: 1900-SDS-001 (8:00 – 20:00 hàng ngày)
- Chat trực tiếp với nhân viên qua ứng dụng.

## 9. Hoàn trả và khiếu nại
- Khiếu nại về giáo viên hoặc xe học: Liên hệ admin trong vòng 24h sau buổi học.
- Hoàn tín chỉ do sự cố kỹ thuật: Được xét duyệt trong 3 ngày làm việc.

## 10. Chương trình giới thiệu bạn bè
- Giới thiệu 1 học viên mới: Nhận 2 tín chỉ thưởng.
- Học viên mới đăng ký qua link giới thiệu: Nhận 12 tín chỉ thay vì 10.
"""
