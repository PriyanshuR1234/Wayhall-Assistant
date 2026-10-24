"""
Merge, deduplicate, and rerank retrieved candidates using
Reciprocal Rank Fusion (RRF).

RRF formula for a document d ranked at position r in run i:
    score(d) += 1 / (k + r)   where k=60 (standard constant)

Advantages:
- Does not require calibrated absolute scores from each retrieval method.
- Naturally combines vector rankings (cosine similarity) with FTS rankings.
- Simple, transparent, and auditable during a live demo.
"""

from collections import defaultdict
from typing import List

from app.db.vector_store import SearchResult
from app.utils.logger import get_logger

logger = get_logger(__name__)

RRF_K = 60          # standard constant — reduces sensitivity to top rank
MAX_FINAL_CHUNKS = 12   # max chunks sent to LLM (balances context vs cost)


def deduplicate(results: List[SearchResult]) -> List[SearchResult]:
    """
    Remove duplicates — keep the occurrence with the higher score.
    A chunk returned by both vector and FTS is deduplicated by chunk_id.
    """
    seen: dict[str, SearchResult] = {}
    for r in results:
        if r.chunk_id not in seen or r.score > seen[r.chunk_id].score:
            seen[r.chunk_id] = r
    return list(seen.values())


def rrf_rerank(
    results: List[SearchResult],
    max_results: int = MAX_FINAL_CHUNKS,
) -> List[SearchResult]:
    """
    Deduplicate then rerank using Reciprocal Rank Fusion.

    Strategy:
    1. Separate vector and FTS result lists (in order of their original scores).
    2. Assign RRF scores based on rank within each list.
    3. Sum RRF scores for each chunk_id across all lists.
    4. Return top-max_results chunks by total RRF score.
    """
    if not results:
        return []

    # Separate into per-method ranked lists
    vector_ranked = sorted(
        [r for r in results if r.method == "vector"],
        key=lambda x: x.score,
        reverse=True,   # higher similarity = better
    )
    fts_ranked = sorted(
        [r for r in results if r.method == "fts"],
        key=lambda x: x.score,
        reverse=True,   # higher rank = better
    )

    rrf_scores: dict[str, float] = defaultdict(float)
    chunk_map: dict[str, SearchResult] = {}

    for rank, result in enumerate(vector_ranked, start=1):
        rrf_scores[result.chunk_id] += 1.0 / (RRF_K + rank)
        chunk_map[result.chunk_id] = result

    for rank, result in enumerate(fts_ranked, start=1):
        rrf_scores[result.chunk_id] += 1.0 / (RRF_K + rank)
        chunk_map.setdefault(result.chunk_id, result)

    # Sort by total RRF score descending
    sorted_ids = sorted(rrf_scores, key=lambda cid: rrf_scores[cid], reverse=True)
    reranked = [chunk_map[cid] for cid in sorted_ids[:max_results]]

    logger.info(
        "RRF reranked %d candidates → top %d chunks (from %d unique docs: %s).",
        len(results),
        len(reranked),
        len({r.doc_label for r in reranked}),
        list({r.doc_label for r in reranked}),
    )
    return reranked
