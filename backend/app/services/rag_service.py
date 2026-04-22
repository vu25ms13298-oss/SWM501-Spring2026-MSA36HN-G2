import uuid
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.knowledge import KnowledgeChunk

logger = logging.getLogger(__name__)


def _get_embeddings():
    if not settings.GEMINI_API_KEY:
        return None
    try:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=settings.GEMINI_API_KEY,
        )
    except Exception as e:
        logger.warning(f"Could not init embeddings: {e}")
        return None


async def retrieve_similar_chunks(
    db: AsyncSession,
    query: str,
    top_k: int = 5,
) -> list[KnowledgeChunk]:
    embeddings = _get_embeddings()
    if embeddings is None:
        # Fallback: return all chunks (text search)
        result = await db.execute(select(KnowledgeChunk).limit(top_k))
        return result.scalars().all()

    try:
        query_embedding = await embeddings.aembed_query(query)
        result = await db.execute(
            select(KnowledgeChunk)
            .order_by(KnowledgeChunk.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )
        return result.scalars().all()
    except Exception as e:
        logger.error(f"RAG retrieval error: {e}")
        result = await db.execute(select(KnowledgeChunk).limit(top_k))
        return result.scalars().all()


async def ingest_document(filename: str, contents: bytes, content_type: str):
    """Background task: parse → chunk → embed → upsert."""
    from app.core.database import AsyncSessionLocal

    logger.info(f"Ingesting document: {filename}")
    chunks = _extract_chunks(filename, contents, content_type)

    embeddings = _get_embeddings()
    async with AsyncSessionLocal() as db:
        # Delete existing chunks for this file
        result = await db.execute(
            select(KnowledgeChunk).where(KnowledgeChunk.source_file == filename)
        )
        for old in result.scalars().all():
            await db.delete(old)

        for i, chunk_text in enumerate(chunks):
            embedding = None
            if embeddings:
                try:
                    embedding = await embeddings.aembed_query(chunk_text)
                except Exception as e:
                    logger.warning(f"Embed error chunk {i}: {e}")

            chunk = KnowledgeChunk(
                id=str(uuid.uuid4()),
                source_file=filename,
                chunk_text=chunk_text,
                embedding=embedding,
                metadata_={"chunk_index": i, "total_chunks": len(chunks)},
            )
            db.add(chunk)

        await db.commit()
    logger.info(f"Ingested {len(chunks)} chunks from {filename}")


def _extract_chunks(filename: str, contents: bytes, content_type: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    text = ""
    try:
        if content_type in (".md", ".txt"):
            text = contents.decode("utf-8", errors="ignore")
        elif content_type == ".pdf":
            import io
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(contents))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        elif content_type == ".docx":
            import io
            from docx import Document
            doc = Document(io.BytesIO(contents))
            text = "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        logger.error(f"Parse error for {filename}: {e}")
        text = contents.decode("utf-8", errors="ignore")

    # Simple sliding window chunking
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
        i += chunk_size - overlap

    return chunks if chunks else [text[:2000]]
