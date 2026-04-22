from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Import all models so SQLAlchemy registers them
    import app.models  # noqa

    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS knowledge_chunks_embedding_idx "
                "ON knowledge_chunks USING hnsw (embedding vector_cosine_ops)"
            )
        )

    # Auto-seed if database is empty
    from app.scripts.seed import seed_if_empty
    await seed_if_empty()

    yield

    await engine.dispose()


app = FastAPI(
    title="Smart Driving School API",
    version="1.0.0",
    description="Booking & AI-Powered Customer Support for SDS",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import auth, booking, instructor, admin, chat, knowledge  # noqa

app.include_router(auth.router)
app.include_router(booking.router)
app.include_router(instructor.router)
app.include_router(admin.router)
app.include_router(chat.router)
app.include_router(knowledge.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "SDS Backend"}
