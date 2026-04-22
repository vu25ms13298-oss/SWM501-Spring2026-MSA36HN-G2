# SDS Implementation Plan
> Smart Booking & Automated Customer Support  
> Stack: FastAPI · PostgreSQL/pgvector · React (Vite) · Gemini API

---

## 1. Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| Backend | FastAPI + Uvicorn | Async, auto OpenAPI docs, type hints |
| Database | PostgreSQL 16-alpine + pgvector | Single DB cho relational + vector — tránh thêm service |
| ORM | SQLAlchemy 2.0 (async) | Typed models, Alembic migration |
| Auth | JWT (python-jose) | Stateless, đủ cho demo |
| RAG | LangChain + pgvector retriever | pgvector đã trong Postgres — không cần Chroma/Qdrant riêng |
| LLM / Embeddings | Gemini 1.5 Flash + text-embedding-004 | Free tier đủ dùng, tiếng Việt OK |
| Frontend | React (Vite) + TailwindCSS | Fast dev, component-based |
| Containerization | Docker Compose | backend + postgres trong một compose file |
| Mock Data | Seed script (Python) | 5 learners, 3 instructors, 20 bookings, sample KB docs |

update:
- sử dụng uv để quản lý
- sử dụng pgvector/pgvector, pg 16-alpine hình như không có vector DB.
---

## 2. Database Schema

### `users`
| Column | Type / Notes |
|---|---|
| id | UUID PK |
| role | ENUM(learner, instructor, admin, support) |
| name | VARCHAR |
| email | VARCHAR UNIQUE |
| password_hash | VARCHAR |
| skill_level | ENUM(beginner, intermediate, advanced) — NULL for non-learner |
| lesson_credits | INTEGER DEFAULT 0 |

### `instructor_availability`
| Column | Type / Notes |
|---|---|
| id | UUID PK |
| instructor_id | FK → users |
| slot_start | TIMESTAMPTZ |
| slot_end | TIMESTAMPTZ (slot_start + 1h) |
| status | ENUM(available, booked, cancelled) |

### `sessions`
| Column | Type / Notes |
|---|---|
| id | UUID PK |
| instructor_id | FK → users |
| vehicle_id | FK → vehicles |
| slot_start | TIMESTAMPTZ |
| slot_end | TIMESTAMPTZ |
| status | ENUM(confirmed, pending_reassignment, cancelled) |

### `bookings`
| Column | Type / Notes |
|---|---|
| id | UUID PK |
| learner_id | FK → users |
| session_id | FK → sessions |
| status | ENUM(confirmed, cancelled) |
| booked_at | TIMESTAMPTZ |
| cancelled_at | TIMESTAMPTZ NULLABLE |

### `vehicles`
| Column | Type / Notes |
|---|---|
| id | UUID PK |
| type | ENUM(manual, automatic) |
| plate | VARCHAR |

### `chat_messages`
| Column | Type / Notes |
|---|---|
| id | UUID PK |
| conversation_id | UUID |
| role | ENUM(user, assistant, staff) |
| content | TEXT |
| created_at | TIMESTAMPTZ |

### `knowledge_chunks` (pgvector)
| Column | Type / Notes |
|---|---|
| id | UUID PK |
| source_file | VARCHAR |
| chunk_text | TEXT |
| embedding | VECTOR(768) |
| metadata | JSONB |

> **Note — Double Booking guard:** `SELECT ... FOR UPDATE` khi check capacity, không check ở application layer rồi insert. Với 50 concurrent requests (NFR-02) sẽ race condition nếu chỉ dùng app-level check.

---

## 3. API Endpoints

Auth header: `Bearer <JWT>` trên tất cả routes trừ `/auth/*`.

### Auth
| Method | Path | Description |
|---|---|---|
| POST | `/auth/login` | Trả JWT. Body: `{email, password}` |
| POST | `/auth/register` | Tạo user mới (role=learner) |

### Booking — UC-01
| Method | Path | Description |
|---|---|---|
| GET | `/slots?date=YYYY-MM-DD` | Danh sách slot available. Trả `best_match` score dựa trên skill_level của caller (FR-04) |
| POST | `/bookings` | Tạo booking. Validate: 12h rule (FR-01), capacity ≤ 3 (FR-02), auto-assign instructor (FR-03) |
| DELETE | `/bookings/{id}` | Hủy booking. Apply BR-03 penalty logic. Trả credit adjustment |
| GET | `/bookings/me` | Lịch học upcoming của learner (dùng cho chatbot FR-09) |

### Instructor — UC-04
| Method | Path | Description |
|---|---|---|
| GET | `/instructor/schedule?week=YYYY-WW` | Lịch dạy theo tuần (FR-12) |
| POST | `/instructor/availability` | Đăng ký slot trống. Body: `[{slot_start, slot_end}]` |
| DELETE | `/instructor/availability/{id}` | Hủy slot. Validate BR-09 (block nếu đã có booking) |

### Admin — UC-02, UC-06
| Method | Path | Description |
|---|---|---|
| GET | `/admin/forecast?weeks=2` | Dự báo demand vs instructor capacity. Trả `alert: true` nếu thiếu (FR-05) |
| PUT | `/admin/sessions/{id}` | Override session: đổi instructor hoặc hủy ca (FR-13) |
| GET | `/admin/sessions` | Danh sách sessions với filter |

### Chatbot — UC-03, UC-07
| Method | Path | Description |
|---|---|---|
| POST | `/chat/message` | Body: `{conversation_id, message}`. Pipeline: intent → RAG/API → Gemini → log (FR-11) |
| GET | `/chat/history/{conversation_id}` | Lịch sử hội thoại (cho human handoff FR-15) |
| POST | `/chat/escalate` | Chuyển conversation sang Support Staff |

### Knowledge Base — UC-05
| Method | Path | Description |
|---|---|---|
| POST | `/admin/kb/upload` | Upload PDF/MD/Docx. Async: parse → chunk → embed → upsert pgvector (FR-14) |
| GET | `/admin/kb/documents` | Danh sách documents trong KB |
| DELETE | `/admin/kb/documents/{id}` | Xóa document + chunks khỏi pgvector |

---

## 4. Sprint Task Breakdown

Effort: `S` = ~2h · `M` = ~4h · `L` = ~8h

---

### Sprint 0 — Setup & Architecture

| Task | Description | Effort | Layer |
|---|---|---|---|
| S0-DEV-01 | FastAPI project structure: routers, models, schemas, services, core | M | Backend |
| S0-DEV-02 | Docker Compose: postgres + pgvector + backend | M | Backend |
| S0-DEV-03 | SQLAlchemy async engine + Alembic migration setup | M | Backend |
| S0-DEV-04 | JWT auth middleware: login + decode + role guard decorator | M | Backend |
| S0-DEV-05 | Seed script: 3 instructors, 5 learners, 5 vehicles, 20 availability slots | M | Backend |
| S0-DEV-06 | Vite + React + TailwindCSS + React Router + axios setup | S | Frontend |
| S0-DEV-07 | Login page + JWT token storage + auth context | M | Frontend |

---

### Sprint 1 — Core Booking + Chatbot Infra

| Task | Description | Effort | Layer |
|---|---|---|---|
| S1-DEV-01 | `GET /slots`: query available slots, annotate `best_match` by skill_level (basic scoring) | M | Backend |
| S1-DEV-02 | `POST /bookings`: 12h rule, capacity ≤ 3 check (SELECT FOR UPDATE), auto-assign instructor | L | Backend |
| S1-DEV-03 | `DELETE /bookings/{id}`: cancellation + BR-03 penalty logic | M | Backend |
| S1-DEV-04 | `GET/POST/DELETE /instructor/availability` với BR-09 guard | M | Backend |
| S1-DEV-05 | Notification stub: log confirmed/changed booking vào DB (FR-06) | S | Backend |
| S1-DEV-06 | Booking UI: calendar view → slot list → confirm flow | L | Frontend |
| S1-DEV-07 | My Bookings page: list + cancel button | M | Frontend |
| S1-DEV-08 | Instructor weekly schedule view (read-only calendar) | M | Frontend |
| S1-DEV-09 | Chat widget UI: message bubbles, input, send button | M | Frontend |
| S1-DEV-10 | `POST /chat/message` stub: echo + log to `chat_messages` | S | Backend |

---

### Sprint 2 — Full RAG Chatbot + Smart Grouping

| Task | Description | Effort | Layer |
|---|---|---|---|
| S2-DEV-01 | `knowledge_chunks` table + HNSW index trên embedding column | S | Backend |
| S2-DEV-02 | KB ingestion service: LangChain loader (PDF/MD/Docx) → chunk → Gemini embed → upsert | L | Backend |
| S2-DEV-03 | RAG retriever: pgvector similarity search, top-5 chunks | M | Backend |
| S2-DEV-04 | Intent detection: Gemini prompt classify → `booking_query / progress_query / fee_query / general_faq` | M | Backend |
| S2-DEV-05 | Chat pipeline: intent → route (API call vs RAG) → Gemini generate → response | L | Backend |
| S2-DEV-06 | `GET /bookings/me`: upcoming sessions với instructor name (chatbot FR-09) | S | Backend |
| S2-DEV-07 | Human handoff: `POST /chat/escalate`, `GET /chat/history` (FR-15) | M | Backend |
| S2-DEV-08 | `POST /admin/kb/upload` + async background task | M | Backend |
| S2-DEV-09 | Nâng cấp `GET /slots`: grouping score = same-skill-level learners / total learners in slot (FR-04) | M | Backend |
| S2-DEV-10 | Chat UI: kết nối real API, thêm typing indicator | M | Frontend |
| S2-DEV-11 | Admin KB management page: upload form, document list, delete | M | Frontend |

---

### Sprint 3 — Analytics + Admin + Polish

| Task | Description | Effort | Layer |
|---|---|---|---|
| S3-DEV-01 | `GET /admin/forecast`: moving average trên booking history, compare vs instructor count, flag alert (FR-05) | L | Backend |
| S3-DEV-02 | `PUT /admin/sessions/{id}`: override instructor + notification stub (FR-13) | M | Backend |
| S3-DEV-03 | Thêm skill_level display per session slot cho instructor view (US-04) | S | Backend |
| S3-DEV-04 | Admin Dashboard: forecast bar chart (recharts), red alert badge, session override modal | L | Frontend |
| S3-DEV-05 | Learner Dashboard: hours completed, next lesson, credits remaining | M | Frontend |
| S3-DEV-06 | E2E manual test pass: booking flow, chatbot FAQ, admin forecast | M | QA |
| S3-DEV-07 | README + Docker Compose one-command setup | S | Backend |
| S3-DEV-08 | Seed nâng cấp: chat history mẫu + sample KB PDF (driving school policy) | S | Backend |

---

## 5. Project Structure

```
sds-project/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app + lifespan
│   │   ├── core/
│   │   │   ├── config.py            # Settings (pydantic-settings)
│   │   │   ├── database.py          # Async SQLAlchemy engine
│   │   │   └── security.py          # JWT encode/decode
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── booking.py
│   │   │   ├── session.py
│   │   │   └── knowledge.py         # knowledge_chunks (pgvector)
│   │   ├── schemas/                 # Pydantic request/response schemas
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── booking.py           # /slots, /bookings
│   │   │   ├── instructor.py
│   │   │   ├── admin.py
│   │   │   └── chat.py
│   │   ├── services/
│   │   │   ├── booking_service.py   # Business logic FR-01..06
│   │   │   ├── rag_service.py       # LangChain + pgvector
│   │   │   ├── chat_service.py      # Intent → pipeline → Gemini
│   │   │   └── forecast_service.py  # Demand forecasting
│   │   └── scripts/
│   │       └── seed.py
│   ├── alembic/
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx
│   │   │   ├── BookingPage.jsx
│   │   │   ├── MyBookingsPage.jsx
│   │   │   ├── InstructorPage.jsx
│   │   │   ├── AdminDashboard.jsx
│   │   │   └── LearnerDashboard.jsx
│   │   ├── components/
│   │   │   ├── ChatWidget.jsx
│   │   │   ├── SlotCalendar.jsx
│   │   │   └── ForecastChart.jsx
│   │   ├── hooks/
│   │   │   └── useAuth.js
│   │   └── api/
│   │       └── client.js            # axios instance + interceptors
│   ├── vite.config.js
│   └── package.json
│
└── docker-compose.yml
```

---

## 6. RAG / Chatbot Pipeline

```
User message
    │
    ▼
Intent Detection (Gemini Flash prompt)
    │
    ├── booking_query    ──► GET /bookings/me  ──► format response
    │
    ├── progress_query   ──► pgvector similarity search (top-5 chunks)
    │                                │
    ├── fee_query        ──►         │
    │                                ▼
    └── general_faq      ──► Gemini Flash generate
                              (system_prompt + retrieved_chunks + user_message)
                                     │
                                     ▼
                              Log to chat_messages (FR-11)
                                     │
                                     ▼
                         confidence < threshold?
                              │              │
                             YES             NO
                              │              │
                         escalate        return response
                       /chat/escalate
```

**System prompt constraint (BR-05):**
```
If the retrieved context does not contain enough information,
respond with: "Xin lỗi, tôi không có thông tin về vấn đề này.
Vui lòng liên hệ nhân viên hỗ trợ."
Do NOT generate information outside the provided context.
```

---

## 7. Key Design Decisions

| Decision | Rationale & Trade-off |
|---|---|
| pgvector thay vì Chroma/Qdrant | Không deploy thêm service. Đủ cho KB < 10k chunks. Trade-off: không có built-in UI nhưng không cần cho demo. |
| Gemini Flash thay vì OpenAI | Free tier 1M tokens/ngày. Tiếng Việt OK. Trade-off: latency ~1.5-2s, nhưng NFR-03 cho phép 3s. |
| Intent detection bằng Gemini prompt | Đủ cho 4 intents, không cần training data. Trade-off: 1 extra API call, bù lại bằng simplicity. |
| SQLAlchemy async (không dùng Tortoise/Beanie) | Typed models, Alembic migration dễ kiểm soát. Trade-off: boilerplate nhiều hơn. |
| Notification stub (log to DB) | Scope demo không cần SMTP/FCM. Record trong DB đủ để tester verify FR-06. |
| Moving average cho forecasting | Đủ để demo trend. Trade-off: kém chính xác hơn Prophet/ARIMA nhưng không justify thêm dependency với mock data. |
| Smart Grouping = rule-based scoring | `score = same_skill_learners / total_learners`. Không cần ML model. Nếu thầy hỏi sâu: production sẽ là bin-packing optimization. |