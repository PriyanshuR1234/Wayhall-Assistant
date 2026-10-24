"""
Document chunker — section and page-aware chunking for municipal documents.

Critical rules:
- NEVER lose or alter the original 1-indexed page number.
- Attach section heading context to chunk metadata.
- Produce clean, overlapping chunks bounded by sentence/paragraph breaks.
- Generate deterministic, traceable chunk IDs: {doc_label}_p{page:02d}_{idx:03d}
"""

import re
from dataclasses import dataclass
from typing import List, Optional

from app.ingestion.pdf_extractor import PageContent
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TextChunk:
    chunk_id: str
    text: str
    source: str
    page: int
    section: Optional[str]
    doc_label: str


def _split_text(
    text: str,
    chunk_size: int = 700,
    chunk_overlap: int = 120,
) -> List[str]:
    """
    Split text into chunks bounded by paragraph or sentence boundaries where possible,
    with an overlap between consecutive chunks.
    """
    clean_text = re.sub(r"\s+", " ", text).strip()
    if not clean_text:
        return []

    if len(clean_text) <= chunk_size:
        return [clean_text]

    # Split primarily on paragraphs or sentence boundaries
    sentences = re.split(r"(?<=[.!?])\s+", clean_text)
    chunks: List[str] = []
    current_chunk: List[str] = []
    current_len = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        sent_len = len(sentence)
        if current_len + sent_len > chunk_size and current_chunk:
            chunk_str = " ".join(current_chunk).strip()
            if chunk_str:
                chunks.append(chunk_str)

            # Keep overlap from the end of current chunk
            overlap_sentences: List[str] = []
            overlap_len = 0
            for prev in reversed(current_chunk):
                if overlap_len + len(prev) < chunk_overlap:
                    overlap_sentences.insert(0, prev)
                    overlap_len += len(prev)
                else:
                    break

            current_chunk = overlap_sentences + [sentence]
            current_len = sum(len(s) for s in current_chunk) + len(current_chunk)
        else:
            current_chunk.append(sentence)
            current_len += sent_len + 1

    if current_chunk:
        chunk_str = " ".join(current_chunk).strip()
        if chunk_str and (not chunks or chunk_str != chunks[-1]):
            chunks.append(chunk_str)

    return chunks


def chunk_pages(
    pages: List[PageContent],
    doc_label: str,
    chunk_size: int = 700,
    chunk_overlap: int = 120,
) -> List[TextChunk]:
    """
    Convert extracted PDF pages into clean, traceable TextChunk objects.

    Args:
        pages: List of PageContent extracted from a single PDF.
        doc_label: Normalized document label ('service_requests', 'bylaws', 'permits').
        chunk_size: Target character length per chunk.
        chunk_overlap: Target character overlap between consecutive chunks.

    Returns:
        List of TextChunk instances with metadata preserved.
    """
    chunks: List[TextChunk] = []

    for page in pages:
        # Critical validation: page must be positive integer
        assert page.page >= 1, f"Invalid page number {page.page} for {page.source}"

        page_chunks = _split_text(
            page.text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        for idx, text_block in enumerate(page_chunks):
            # Deterministic, easily identifiable chunk ID
            chunk_id = f"{doc_label}_p{page.page:02d}_{idx + 1:03d}"

            chunk = TextChunk(
                chunk_id=chunk_id,
                text=text_block,
                source=page.source,
                page=page.page,
                section=page.section,
                doc_label=doc_label,
            )
            chunks.append(chunk)

    logger.info(
        "Chunked %d pages of '%s' into %d chunks.",
        len(pages),
        doc_label,
        len(chunks),
    )
    return chunks
