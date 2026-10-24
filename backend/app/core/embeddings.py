"""
Gemini Embedding API wrapper.

Uses google-generativeai to convert text into dense vectors.
The same model MUST be used for both ingestion and query embedding
— mixing models produces garbage retrieval results.
"""

import asyncio
from typing import List

import google.generativeai as genai

from app.config import settings
from app.utils.logger import get_logger
from app.utils.retry import retry_sync

logger = get_logger(__name__)

# Configure Gemini once at module load
genai.configure(api_key=settings.GEMINI_API_KEY)


@retry_sync(attempts=settings.RETRY_ATTEMPTS, base_delay=settings.RETRY_BASE_DELAY)
def _embed_sync(text: str, task_type: str = "retrieval_document") -> List[float]:
    """
    Embed a single piece of text synchronously.

    task_type options:
        "retrieval_document" — for PDF chunk text during ingestion
        "retrieval_query"    — for user query during retrieval
    """
    result = genai.embed_content(
        model=settings.GEMINI_EMBED_MODEL,
        content=text,
        task_type=task_type,
        output_dimensionality=settings.EMBEDDING_DIMENSIONS,
    )
    embedding: List[float] = result["embedding"]

    # Validate dimensions
    if len(embedding) != settings.EMBEDDING_DIMENSIONS:
        raise ValueError(
            f"Embedding dimension mismatch: expected {settings.EMBEDDING_DIMENSIONS}, "
            f"got {len(embedding)}. Rebuild the index if you changed the model."
        )

    return embedding


@retry_sync(attempts=settings.RETRY_ATTEMPTS, base_delay=settings.RETRY_BASE_DELAY)
def _embed_batch_sync(texts: List[str], task_type: str = "retrieval_document") -> List[List[float]]:
    """Embed multiple texts; Gemini API handles batching internally."""
    result = genai.embed_content(
        model=settings.GEMINI_EMBED_MODEL,
        content=texts,
        task_type=task_type,
        output_dimensionality=settings.EMBEDDING_DIMENSIONS,
    )
    return result["embedding"]


# ── Async public API ──────────────────────────────────────────────────────────

async def embed_query(text: str) -> List[float]:
    """Embed a user query for retrieval (async, retried)."""
    return await asyncio.to_thread(_embed_sync, text, "retrieval_query")


async def embed_document(text: str) -> List[float]:
    """Embed a document chunk for indexing (async, retried)."""
    return await asyncio.to_thread(_embed_sync, text, "retrieval_document")


async def embed_documents_batch(texts: List[str]) -> List[List[float]]:
    """Embed a batch of document chunks (async, retried)."""
    return await asyncio.to_thread(_embed_batch_sync, texts, "retrieval_document")
