"""
Per-document parallel retrieval — the core of the coverage-first RAG pipeline.

For each sub-query:
  - Search EACH of the 3 documents independently (vector + FTS).
  - All searches run concurrently via asyncio.gather.
  - Results are returned as a flat list of SearchResult objects with
    their original method tags for RRF reranking.

Why per-document?
  A single global vector search can return all top-K from one PDF,
  silently missing evidence in the other two.
  Searching each document independently prevents any document from being
  excluded just because another happened to score slightly higher.
"""

import asyncio
from typing import List, Optional

from app.config import settings
from app.core.embeddings import embed_query
from app.db.vector_store import SearchResult, fts_search, vector_search, DOC_LABELS
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def _retrieve_for_one_doc(
    sub_query: str,
    query_embedding: List[float],
    doc_label: str,
    top_k: int,
) -> List[SearchResult]:
    """
    Run vector search + FTS concurrently for ONE document.
    Returns combined results (both methods) — duplicates handled upstream.
    """
    vec_task = vector_search(query_embedding, doc_label, top_k)
    fts_task = fts_search(sub_query, doc_label, top_k)
    vec_results, fts_results = await asyncio.gather(vec_task, fts_task)
    return vec_results + fts_results


async def retrieve_all_documents(
    sub_queries: List[str],
    top_k: Optional[int] = None,
) -> List[SearchResult]:
    """
    Run coverage-first retrieval: for each sub-query, search ALL 3 documents
    independently using both vector and FTS. All tasks run concurrently.

    Returns a flat list of SearchResult objects (before dedup/reranking).
    Max candidates: len(sub_queries) × 3 docs × 2 methods × top_k
    """
    top_k = top_k or settings.TOP_K_PER_DOC

    # Embed all sub-queries concurrently (one Gemini call per sub-query)
    embeddings = await asyncio.gather(*[embed_query(q) for q in sub_queries])

    # Build all retrieval tasks: sub_query × doc_label
    tasks = []
    for sub_query, embedding in zip(sub_queries, embeddings):
        for doc_label in DOC_LABELS:
            tasks.append(
                _retrieve_for_one_doc(sub_query, embedding, doc_label, top_k)
            )

    all_results: List[List[SearchResult]] = await asyncio.gather(*tasks)

    # Flatten
    flat: List[SearchResult] = []
    for result_group in all_results:
        flat.extend(result_group)

    logger.info(
        "Retrieved %d raw candidates across %d sub-queries × 3 docs × 2 methods.",
        len(flat),
        len(sub_queries),
    )
    return flat
