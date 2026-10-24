"""
Document ingestion pipeline.

Orchestrates:
1. Extraction (PyMuPDF with section and 1-indexed page preservation)
2. Chunking (sliding window with overlap and deterministic IDs)
3. Embedding generation (Gemini text-embedding-004 in rate-limited batches)
4. Storage (Supabase PostgreSQL pgvector upsert)

Can be executed as a CLI command or imported programmatically.
"""

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path
from typing import List, Optional

from app.config import settings
from app.core.embeddings import embed_documents_batch
from app.db.vector_store import insert_chunks
from app.ingestion.chunker import chunk_pages
from app.ingestion.pdf_extractor import extract_pdf
from app.utils.logger import get_logger

logger = get_logger(__name__)

DOC_MAPPING = {
    "service_requests": ["service", "request", "management", "complaint"],
    "bylaws": ["bylaw", "by-law", "noise", "parking", "property"],
    "permits": ["permit", "license", "licensing", "building"],
}


def infer_doc_label(filename: str) -> str:
    """Infer the doc_label from a file name based on keyword matching."""
    lower = filename.lower()
    for label, keywords in DOC_MAPPING.items():
        if any(kw in lower for kw in keywords):
            return label
    return "service_requests"


async def ingest_pdf(
    pdf_path: str | Path,
    doc_label: Optional[str] = None,
    batch_size: int = 25,
) -> int:
    """
    Ingest a single PDF file into the vector store.

    Args:
        pdf_path: Absolute or relative path to PDF file.
        doc_label: Optional document label ('service_requests', 'bylaws', 'permits').
                   If not provided, inferred from filename.
        batch_size: Embedding batch size to stay within Gemini rate limits.

    Returns:
        Number of chunks successfully indexed.
    """
    path = Path(pdf_path)
    if not path.is_file():
        raise FileNotFoundError(f"PDF file not found: {path}")

    label = doc_label or infer_doc_label(path.name)
    logger.info("Starting ingestion for '%s' as '%s'", path.name, label)

    # 1. Extraction
    pages = extract_pdf(path, doc_label=label)
    if not pages:
        logger.warning("No pages extracted from %s", path.name)
        return 0

    # 2. Chunking
    chunks = chunk_pages(
        pages=pages,
        doc_label=label,
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
    )
    if not chunks:
        logger.warning("No chunks generated for %s", path.name)
        return 0

    logger.info("Generating embeddings for %d chunks in batches of %d...", len(chunks), batch_size)

    # 3. Batch embedding generation with rate limit protection
    records_to_insert = []
    texts = [c.text for c in chunks]

    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        logger.info(
            "Embedding batch %d-%d of %d...",
            i + 1,
            min(i + batch_size, len(texts)),
            len(texts),
        )
        embeddings = await embed_documents_batch(batch_texts)

        for chunk_obj, emb in zip(chunks[i : i + batch_size], embeddings):
            records_to_insert.append(
                {
                    "chunk_id": chunk_obj.chunk_id,
                    "text": chunk_obj.text,
                    "embedding": emb,
                    "source": chunk_obj.source,
                    "page": chunk_obj.page,
                    "section": chunk_obj.section,
                    "doc_label": chunk_obj.doc_label,
                }
            )

        # Gentle throttle between batches to protect free-tier rate limits
        if i + batch_size < len(texts):
            await asyncio.sleep(0.5)

    # 4. Upsert into Supabase
    insert_chunks(records_to_insert)
    logger.info("Successfully ingested %d chunks from %s", len(records_to_insert), path.name)
    return len(records_to_insert)


async def ingest_directory(dir_path: str | Path) -> int:
    """Ingest all PDF files found in directory."""
    path = Path(dir_path)
    if not path.is_dir():
        raise NotADirectoryError(f"Directory not found: {path}")

    pdf_files = list(path.glob("*.pdf"))
    if not pdf_files:
        logger.warning("No PDF files found in directory: %s", path)
        return 0

    total_chunks = 0
    for pdf in pdf_files:
        count = await ingest_pdf(pdf)
        total_chunks += count

    logger.info("Completed directory ingestion: %d total chunks indexed across %d files.", total_chunks, len(pdf_files))
    return total_chunks


def main():
    parser = argparse.ArgumentParser(description="Ingest municipal PDF documents into Supabase vector store")
    parser.add_argument("path", help="Path to PDF file or directory containing PDFs")
    parser.add_argument("--label", choices=["service_requests", "bylaws", "permits"], default=None, help="Explicit doc label")
    args = parser.parse_args()

    target = Path(args.path)
    if target.is_file():
        asyncio.run(ingest_pdf(target, doc_label=args.label))
    elif target.is_dir():
        asyncio.run(ingest_directory(target))
    else:
        logger.error("Path does not exist: %s", target)
        sys.exit(1)


if __name__ == "__main__":
    main()
