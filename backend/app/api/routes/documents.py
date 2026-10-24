"""
Documents API route — inspect indexed documents, chunk distributions,
and knowledge base stats.
"""

from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel

from app.db.supabase import get_supabase
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/documents", tags=["Documents"])


class DocumentSummary(BaseModel):
    doc_label: str
    source: str
    chunk_count: int
    page_min: int
    page_max: int


class ChunkDetail(BaseModel):
    chunk_id: str
    doc_label: str
    source: str
    page: int
    section: Optional[str]
    snippet: str


@router.get("", response_model=List[DocumentSummary])
async def list_documents():
    """List indexed municipal documents with page ranges and chunk counts."""
    client = get_supabase()
    try:
        # Query distinct doc_labels and chunks
        resp = client.table("document_chunks").select("doc_label, source, page").execute()
        rows = resp.data or []

        doc_map = {}
        for r in rows:
            label = r["doc_label"]
            source = r["source"]
            page = r["page"]
            if label not in doc_map:
                doc_map[label] = {
                    "doc_label": label,
                    "source": source,
                    "chunk_count": 0,
                    "pages": set(),
                }
            doc_map[label]["chunk_count"] += 1
            doc_map[label]["pages"].add(page)

        summaries = []
        for label, data in doc_map.items():
            pages = data["pages"]
            summaries.append(
                DocumentSummary(
                    doc_label=label,
                    source=data["source"],
                    chunk_count=data["chunk_count"],
                    page_min=min(pages) if pages else 0,
                    page_max=max(pages) if pages else 0,
                )
            )
        return summaries
    except Exception as exc:
        logger.error("Failed to list documents: %s", exc)
        return []


@router.get("/{doc_label}/chunks", response_model=List[ChunkDetail])
async def get_document_chunks(doc_label: str, limit: int = 50):
    """Inspect raw chunks for a specific document label (great for live demo inspection)."""
    client = get_supabase()
    try:
        resp = (
            client.table("document_chunks")
            .select("chunk_id, doc_label, source, page, section, text")
            .eq("doc_label", doc_label)
            .order("page", desc=False)
            .limit(limit)
            .execute()
        )
        return [
            ChunkDetail(
                chunk_id=r["chunk_id"],
                doc_label=r["doc_label"],
                source=r["source"],
                page=r["page"],
                section=r.get("section"),
                snippet=r["text"][:300] + ("..." if len(r["text"]) > 300 else ""),
            )
            for r in (resp.data or [])
        ]
    except Exception as exc:
        logger.error("Failed to get document chunks for %s: %s", doc_label, exc)
        return []
