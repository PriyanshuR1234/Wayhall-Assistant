"""
Evidence coverage validator.

After retrieval and reranking, checks whether each sub-query has at least
one retrieved chunk that could plausibly address it.

If a sub-query has no evidence:
  - Retry with expanded top_k.
  - If still nothing, mark it as an unsupported part.

This prevents the LLM from receiving an incomplete evidence package
without realising it, and ensures the "not in documents" message is
triggered correctly.
"""

import asyncio
from typing import List, Set, Tuple

from app.core.embeddings import embed_query
from app.db.vector_store import SearchResult, vector_search, fts_search, DOC_LABELS
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _has_coverage(sub_query: str, chunks: List[SearchResult], threshold: float = 0.30) -> bool:
    """
    Heuristic: a sub_query is 'covered' if at least one chunk has a vector
    similarity ≥ threshold OR any FTS chunk is returned.
    Keyword-heavy queries (exact section refs, times) often come through FTS.
    """
    q_lower = sub_query.lower()
    for chunk in chunks:
        # FTS hit for this sub-query's keywords → covered
        if chunk.method == "fts" and chunk.score > 0:
            return True
        # Strong vector similarity → covered
        if chunk.method == "vector" and chunk.score >= threshold:
            return True
    return False


async def _retry_retrieval(sub_query: str, expanded_top_k: int = 8) -> List[SearchResult]:
    """Retry retrieval with broader top_k across all docs."""
    embedding = await embed_query(sub_query)
    tasks = []
    for doc_label in DOC_LABELS:
        tasks.append(vector_search(embedding, doc_label, expanded_top_k))
        tasks.append(fts_search(sub_query, doc_label, expanded_top_k))
    results = await asyncio.gather(*tasks)
    flat = [r for group in results for r in group]
    return flat


async def validate_coverage(
    sub_queries: List[str],
    ranked_chunks: List[SearchResult],
) -> Tuple[List[SearchResult], List[str]]:
    """
    For each sub_query, check whether ranked_chunks already contain evidence.
    For any sub_query without evidence, retry once with a larger candidate pool.

    Returns:
        (augmented_chunks, unsupported_parts)
        - augmented_chunks: original + any new chunks from retries
        - unsupported_parts: sub-queries with no evidence after retry
    """
    augmented = list(ranked_chunks)
    unsupported: List[str] = []

    for sub_query in sub_queries:
        if _has_coverage(sub_query, ranked_chunks):
            continue

        logger.info("No coverage for sub-query '%s' — retrying with expanded k.", sub_query)
        retry_results = await _retry_retrieval(sub_query, expanded_top_k=8)

        if retry_results:
            # Add new chunks not already present
            existing_ids: Set[str] = {c.chunk_id for c in augmented}
            new_chunks = [r for r in retry_results if r.chunk_id not in existing_ids]
            augmented.extend(new_chunks)
            logger.info(
                "Retry for '%s' added %d new candidates.", sub_query, len(new_chunks)
            )

            # Check again
            if not _has_coverage(sub_query, augmented):
                unsupported.append(sub_query)
        else:
            unsupported.append(sub_query)

    if unsupported:
        logger.warning(
            "Unsupported sub-queries (no evidence found): %s", unsupported
        )

    return augmented, unsupported
