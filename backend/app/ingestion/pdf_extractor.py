"""
PDF extractor — page-by-page text extraction using PyMuPDF (fitz).

Design goals:
- Preserve the ORIGINAL page number (1-indexed) for every text block.
- Detect section headings heuristically (bold, large font, or ALL-CAPS lines).
- Never lose citation metadata during extraction.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import fitz  # PyMuPDF

from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PageContent:
    source: str          # original PDF filename (not path)
    page: int            # 1-indexed original page number — NEVER loses this
    section: Optional[str]   # detected section heading, if any
    text: str            # full page text


def _detect_section(blocks: list) -> Optional[str]:
    """
    Heuristically detect a section heading from PyMuPDF text blocks.
    Looks for the first block that is bold, UPPERCASE, or starts with a
    digit-dot pattern like "4.2" or "SER 3".
    """
    section_pattern = re.compile(
        r"^(\d+(\.\d+)*\s+\w|[A-Z]{2,4}\s*\d+|[A-Z\s]{5,}$)"
    )
    for block in blocks:
        if block.get("type") != 0:  # type 0 = text block
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                flags = span.get("flags", 0)
                is_bold = bool(flags & 2**4)   # PyMuPDF bold flag
                is_large = span.get("size", 0) >= 12

                if text and (is_bold or is_large) and section_pattern.match(text):
                    return text[:120]  # cap section name length
    return None


def extract_pdf(pdf_path: str | Path, doc_label: str) -> List[PageContent]:
    """
    Extract all pages from a PDF.

    Args:
        pdf_path: Absolute path to the PDF file.
        doc_label: One of "service_requests" | "bylaws" | "permits".

    Returns:
        List of PageContent — one entry per non-empty page.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    source_name = path.name
    pages: List[PageContent] = []

    with fitz.open(str(path)) as doc:
        logger.info("Extracting '%s' (%d pages).", source_name, len(doc))

        for page_index in range(len(doc)):
            page_number = page_index + 1  # 1-indexed — critical for citations
            page = doc[page_index]

            text = page.get_text("text").strip()
            if not text:
                logger.debug("Page %d is empty — skipping.", page_number)
                continue

            # Section heading detection from structured blocks
            blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE).get("blocks", [])
            section = _detect_section(blocks)

            pages.append(
                PageContent(
                    source=source_name,
                    page=page_number,
                    section=section,
                    text=text,
                )
            )

    logger.info("Extracted %d pages from '%s'.", len(pages), source_name)
    return pages
