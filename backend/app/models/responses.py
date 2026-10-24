"""
Pydantic response models for all API endpoints.
"""

from typing import List, Optional
from pydantic import BaseModel


class Citation(BaseModel):
    chunk_id: str
    source: str       # original PDF filename
    page: int         # original page number — from metadata, NOT from LLM
    section: Optional[str] = None
    snippet: str      # the retrieved text chunk (trimmed for display)


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    citations: List[Citation] = []
    unsupported_parts: List[str] = []
    retrieval_doc_labels: List[str] = []   # which PDFs were used — for UI badges


class SessionResponse(BaseModel):
    session_id: str
    created_at: str


class MessageResponse(BaseModel):
    role: str
    content: str
    citations: List[Citation] = []
    created_at: str


class SessionDetailResponse(BaseModel):
    session_id: str
    messages: List[MessageResponse]


class HealthResponse(BaseModel):
    status: str
    db: str
    gemini: str
    chunks_indexed: int
