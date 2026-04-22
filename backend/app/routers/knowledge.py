import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct

from app.core.database import get_db
from app.core.security import require_roles
from app.models.user import User
from app.models.knowledge import KnowledgeChunk
from app.services import rag_service

router = APIRouter(prefix="/admin/kb", tags=["knowledge-base"])


@router.post("/upload", status_code=202)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    allowed = {".pdf", ".md", ".docx", ".txt"}
    import os
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed)}",
        )

    contents = await file.read()
    background_tasks.add_task(
        rag_service.ingest_document,
        filename=file.filename,
        contents=contents,
        content_type=ext,
    )
    return {"message": f"Document '{file.filename}' queued for processing", "filename": file.filename}


@router.get("/documents")
async def list_documents(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    result = await db.execute(
        select(
            KnowledgeChunk.source_file,
            func.count(KnowledgeChunk.id).label("chunk_count"),
        ).group_by(KnowledgeChunk.source_file)
    )
    rows = result.all()
    return [{"source_file": r.source_file, "chunk_count": r.chunk_count} for r in rows]


@router.delete("/documents/{source_file:path}", status_code=204)
async def delete_document(
    source_file: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles("admin")),
):
    result = await db.execute(
        select(KnowledgeChunk).where(KnowledgeChunk.source_file == source_file)
    )
    chunks = result.scalars().all()
    if not chunks:
        raise HTTPException(status_code=404, detail="Document not found")

    for chunk in chunks:
        await db.delete(chunk)
    await db.commit()
