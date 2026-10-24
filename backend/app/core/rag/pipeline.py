"""
RAG pipeline orchestrator — ties together all stages:

1. Query decomposition
2. Per-document parallel retrieval (vector + FTS)
3. RRF merge and rerank
4. Evidence coverage validation (retry if gaps)
5. LLM generation with grounded evidence
6. Backend citation validation (citations built from metadata, not LLM text)

Returns a structured RAGResult consumed by the chat API route.
"""

from dataclasses import dataclass, field
from typing import List

from app.core.llm import generate_answer
from app.core.rag.decomposer import decompose_query
from app.core.rag.reranker import rrf_rerank
from app.core.rag.retriever import retrieve_all_documents
from app.core.rag.validator import validate_coverage
from app.db.vector_store import SearchResult
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Citation:
    chunk_id: str
    source: str
    page: int
    section: str | None
    snippet: str


@dataclass
class RAGResult:
    answer: str
    citations: List[Citation] = field(default_factory=list)
    unsupported_parts: List[str] = field(default_factory=list)
    retrieval_doc_labels: List[str] = field(default_factory=list)


async def run_rag_pipeline(
    user_question: str,
    history: List[dict],
) -> RAGResult:
    """
    Full coverage-first RAG pipeline.

    Args:
        user_question: The current user message (may be a follow-up).
        history: Recent conversation turns [{"role": ..., "content": ...}, ...].

    Returns:
        RAGResult with answer, verified citations, and unsupported_parts.
    """

    # ── STAGE 1: Query decomposition & contextualization ─────────────────────
    standalone_question, sub_queries = await decompose_query(user_question, history=history)

    # ── STAGE 2: Per-document parallel retrieval ──────────────────────────────
    raw_candidates: List[SearchResult] = await retrieve_all_documents(sub_queries)

    # Carry over previous turn citations to ensure seamless follow-up context
    if history:
        for msg in reversed(history):
            if msg.get("role") == "assistant" and msg.get("citations"):
                prev_ids = [
                    c["chunk_id"] for c in msg["citations"] if isinstance(c, dict) and "chunk_id" in c
                ]
                candidate_ids = {c.chunk_id for c in raw_candidates}
                missing_ids = [cid for cid in prev_ids if cid not in candidate_ids]
                if missing_ids:
                    try:
                        from app.db.supabase import get_supabase
                        client = get_supabase()
                        resp = (
                            client.table("document_chunks")
                            .select("chunk_id, text, source, page, section, doc_label")
                            .in_("chunk_id", missing_ids)
                            .execute()
                        )
                        for row in (resp.data or []):
                            raw_candidates.append(
                                SearchResult(
                                    chunk_id=row["chunk_id"],
                                    text=row["text"],
                                    source=row["source"],
                                    page=row["page"],
                                    section=row.get("section"),
                                    doc_label=row["doc_label"],
                                    score=1.0,
                                    method="context_carryover",
                                )
                            )
                        logger.info("Carried over %d citations from previous turn", len(resp.data or []))
                    except Exception as e:
                        logger.warning("Failed to carry over previous citations: %s", e)
                break

    if not raw_candidates:
        logger.warning("No candidates retrieved for question: %s", user_question[:80])
        return RAGResult(
            answer=(
                "I could not find any relevant information in the supplied "
                "municipal documents for your question."
            ),
            unsupported_parts=[user_question],
        )

    # ── STAGE 3: RRF rerank ────────────────────────────────────────────────────
    ranked_chunks: List[SearchResult] = rrf_rerank(raw_candidates)

    # ── STAGE 4: Evidence coverage validation ─────────────────────────────────
    augmented_chunks, unsupported_parts = await validate_coverage(
        sub_queries, ranked_chunks
    )

    # Final rerank after augmentation
    final_chunks: List[SearchResult] = rrf_rerank(augmented_chunks)

    # Build evidence package for the LLM (dicts, not dataclasses)
    evidence_package = [
        {
            "chunk_id": c.chunk_id,
            "text": c.text,
            "source": c.source,
            "page": c.page,
            "section": c.section,
        }
        for c in final_chunks
    ]

    # ── STAGE 5: LLM generation ────────────────────────────────────────────────
    llm_result = await generate_answer(
        user_question=user_question,
        evidence_chunks=evidence_package,
        history=history,
        standalone_context=standalone_question,
    )

    # ── STAGE 6: Backend citation validation ──────────────────────────────────
    # Build a lookup from retrieved chunks — source of truth for citations.
    chunk_lookup: dict[str, SearchResult] = {c.chunk_id: c for c in final_chunks}
    evidence_ids_claimed = llm_result.get("evidence_ids_used", [])

    verified_citations: List[Citation] = []
    for cid in evidence_ids_claimed:
        if cid in chunk_lookup:
            chunk = chunk_lookup[cid]
            verified_citations.append(
                Citation(
                    chunk_id=cid,
                    source=chunk.source,
                    page=chunk.page,         # from DB metadata — NOT from LLM
                    section=chunk.section,
                    snippet=chunk.text[:300].strip(),  # trimmed for UI display
                )
            )
        else:
            logger.warning(
                "LLM cited unknown chunk_id '%s' — discarding citation.", cid
            )

    # Deduplicate citations by chunk_id
    seen_cids: set[str] = set()
    deduped_citations: List[Citation] = []
    for c in verified_citations:
        if c.chunk_id not in seen_cids:
            seen_cids.add(c.chunk_id)
            deduped_citations.append(c)

    # Which document labels actually contributed
    retrieval_doc_labels = sorted(
        {c.doc_label for c in final_chunks if c.chunk_id in seen_cids}
    )

    # Merge unsupported parts from validator + LLM
    all_unsupported = list(
        set(unsupported_parts + llm_result.get("unsupported_parts", []))
    )

    logger.info(
        "RAG complete | citations=%d | unsupported=%d | docs=%s",
        len(deduped_citations),
        len(all_unsupported),
        retrieval_doc_labels,
    )

    return RAGResult(
        answer=llm_result["answer"],
        citations=deduped_citations,
        unsupported_parts=all_unsupported,
        retrieval_doc_labels=retrieval_doc_labels,
    )
