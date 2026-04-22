# Smart Driving School (SDS)

Smart Booking & Automated Customer Support for a driving school.

## Overview

This repository contains a full-stack prototype with:

- Backend: FastAPI + SQLAlchemy async + PostgreSQL (pgvector)
- Frontend: React (Vite) + TailwindCSS
- AI/RAG: Gemini API + pgvector retrieval
- Runtime: Docker Compose

## Current Status

Implemented foundation and runnable MVP:

- Authentication (register/login/me)
- Booking core flow (slot list, create booking, cancel booking, my bookings)
- Instructor schedule and availability management
- Admin forecast and session override endpoints
- Chat pipeline (intent + retrieval/generation + conversation logging)
- Knowledge-base upload/list/delete endpoints
- Seeded demo data (users, vehicles, sessions, bookings, sample KB chunks)

## Project Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── core/
│   │   ├── models/
│   │   ├── routers/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── scripts/
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── pages/
│   └── package.json
├── docker-compose.yml
├── .env
└── implementation plan.md
```

## Prerequisites

- Docker Desktop (running)
- Optional for local non-docker run:
  - Python 3.12+
  - Node.js 20+

## Quick Start (Docker)

1. From repository root, build and run all services:

```bash
docker compose up --build -d
```

2. Access applications:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Health check: http://localhost:8000/health

3. Stop services:

```bash
docker compose down
```

4. Stop and remove database volume:

```bash
docker compose down -v
```

## Environment Variables

Root `.env` is used by backend container.

```env
SECRET_KEY=sds-super-secret-key-change-in-production-2026
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
GEMINI_API_KEY=
DATABASE_URL=postgresql+asyncpg://sds:sds_password@localhost:5432/sds_db
```

Notes:

- In Docker runtime, backend uses internal service host `postgres`.
- Set `GEMINI_API_KEY` to enable real LLM/embedding calls.
- Without Gemini key, chat still runs with fallback behavior.

## Demo Accounts (Seeded)

- Admin: `admin@sds.vn` / `admin123`
- Instructor: `instructor1@sds.vn` / `instructor123`
- Learner: `learner1@sds.vn` / `learner123`

## API Summary

### Auth

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

### Booking

- `GET /slots?date=YYYY-MM-DD`
- `POST /bookings`
- `DELETE /bookings/{booking_id}`
- `GET /bookings/me`

### Instructor

- `GET /instructor/schedule?week=YYYY-WW`
- `POST /instructor/availability`
- `DELETE /instructor/availability/{slot_id}`

### Admin

- `GET /admin/forecast?weeks=2`
- `GET /admin/sessions`
- `PUT /admin/sessions/{session_id}`

### Chatbot

- `POST /chat/message`
- `GET /chat/history/{conversation_id}`
- `POST /chat/escalate`

### Knowledge Base

- `POST /admin/kb/upload`
- `GET /admin/kb/documents`
- `DELETE /admin/kb/documents/{source_file}`

## Frontend Pages

- Login/Register
- Learner dashboard
- Booking page
- My bookings page
- Instructor schedule page
- Admin dashboard
- Floating chat widget

## Known Decisions

- `bcrypt==4.0.1` is pinned for passlib compatibility.
- pgvector is provided via `pgvector/pgvector:pg16` image.
- Tables are currently auto-created at startup from SQLAlchemy metadata.

## Troubleshooting

### Frontend JSX parsing error in hook files

Issue:

- `The JSX syntax extension is not currently enabled`

Fix applied:

- Hook containing JSX moved to `frontend/src/hooks/useAuth.jsx`
- Imports updated to reference `.jsx` module

### Verify service status

```bash
docker compose ps
docker compose logs backend --tail 100
docker compose logs frontend --tail 100
```

## Next Suggested Steps

- Add Alembic migration workflow (instead of startup table creation)
- Add automated tests for booking constraints and auth guards
- Add role-based UI route protection improvements
- Add background worker/queue for KB ingestion at scale
