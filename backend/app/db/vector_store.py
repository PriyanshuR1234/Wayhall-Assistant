"""
Vector store operations — insert chunks, run vector similarity search,
run full-text search, and upsert.

All DB calls are synchronous (supabase-py v2 sync client) and wrapped
with asyncio.to_thread so they compose cleanly with asyncio.gather
in the RAG retrieval layer.
"""

import asyncio
from dataclasses import dataclass
from typing import List, Optional

from app.config import settings
from app.db.supabase import get_supabase
from app.utils.logger import get_logger

logger = get_logger(__name__)

# All three doc labels — used for validation
DOC_LABELS = ["service_requests", "bylaws", "permits"]


@dataclass
class ChunkRecord:
    chunk_id: str
    text: str
    source: str
    page: int
    section: Optional[str]
    doc_label: str


@dataclass
class SearchResult:
    chunk_id: str
    text: str
    source: str
    page: int
    section: Optional[str]
    doc_label: str
    score: float        # similarity (0-1) for vector; rank for FTS
    method: str         # "vector" | "fts"


# ── Insert ────────────────────────────────────────────────────────────────────

def insert_chunks(chunks: List[dict]) -> None:
    """
    Bulk-insert document chunks.
    Each dict must have: chunk_id, text, embedding (list[float]),
    source, page, section, doc_label.
    """
    client = get_supabase()
    # Upsert so re-ingestion is idempotent
    resp = client.table("document_chunks").upsert(chunks, on_conflict="chunk_id").execute()
    logger.info("Upserted %d chunks into document_chunks.", len(chunks))
    return resp


# ── Sync search helpers ───────────────────────────────────────────────────────

def _vector_search_sync(
    query_embedding: List[float],
    doc_label: Optional[str],
    top_k: int,
) -> List[SearchResult]:
    client = get_supabase()
    try:
        resp = client.rpc(
            "match_chunks",
            {
                "query_embedding": query_embedding,
                "doc_label_filter": doc_label,
                "match_count": top_k,
            },
        ).execute()
        results = []
        for row in (resp.data or []):
            results.append(
                SearchResult(
                    chunk_id=row["chunk_id"],
                    text=row["text"],
                    source=row["source"],
                    page=row["page"],
                    section=row.get("section"),
                    doc_label=row["doc_label"],
                    score=float(row["similarity"]),
                    method="vector",
                )
            )
        return results
    except Exception as exc:
        logger.error("Vector search failed for doc_label=%s: %s", doc_label, exc)
        return []


def _fts_search_sync(
    query_text: str,
    doc_label: Optional[str],
    top_k: int,
) -> List[SearchResult]:
    client = get_supabase()
    try:
        resp = client.rpc(
            "search_chunks_fts",
            {
                "query_text": query_text,
                "doc_label_filter": doc_label,
                "match_count": top_k,
            },
        ).execute()
        results = []
        for row in (resp.data or []):
            results.append(
                SearchResult(
                    chunk_id=row["chunk_id"],
                    text=row["text"],
                    source=row["source"],
                    page=row["page"],
                    section=row.get("section"),
                    doc_label=row["doc_label"],
                    score=float(row["rank"]),
                    method="fts",
                )
            )
        return results
    except Exception as exc:
        logger.error("FTS search failed for doc_label=%s: %s", doc_label, exc)
        return []


# ── Async wrappers ────────────────────────────────────────────────────────────

async def vector_search(
    query_embedding: List[float],
    doc_label: Optional[str] = None,
    top_k: int = 5,
) -> List[SearchResult]:
    return await asyncio.to_thread(
        _vector_search_sync, query_embedding, doc_label, top_k
    )


async def fts_search(
    query_text: str,
    doc_label: Optional[str] = None,
    top_k: int = 5,
) -> List[SearchResult]:
    return await asyncio.to_thread(_fts_search_sync, query_text, doc_label, top_k)


# ── Utility ───────────────────────────────────────────────────────────────────

def count_chunks() -> int:
    """Return total number of indexed chunks — used in health check."""
    client = get_supabase()
    try:
        resp = client.table("document_chunks").select("id", count="exact").execute()
        return resp.count or 0
    except Exception as exc:
        logger.error("count_chunks failed: %s", exc)
        return -1
