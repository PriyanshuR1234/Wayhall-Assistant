"""
Chat API route — orchestrates session handling, conversation memory,
and coverage-first RAG pipeline execution.
"""

from typing import List
from fastapi import APIRouter, HTTPException, status

from app.core.rag.pipeline import run_rag_pipeline
from app.db.chat_store import (
    create_session,
    get_all_messages,
    get_recent_messages,
    get_session,
    save_message,
)
from app.models.requests import ChatRequest
from app.models.responses import (
    ChatResponse,
    Citation,
    MessageResponse,
    SessionDetailResponse,
    SessionResponse,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["Chat"])


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session():
    """Explicitly create a new chat session."""
    session = await create_session()
    return SessionResponse(
        session_id=str(session["id"]),
        created_at=str(session["created_at"]),
    )


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_chat_session(session_id: str):
    """Retrieve full message history for a given session."""
    session = await get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    raw_messages = await get_all_messages(session_id)
    messages: List[MessageResponse] = []
    for m in raw_messages:
        citations = [Citation(**c) for c in (m.get("citations") or [])]
        messages.append(
            MessageResponse(
                role=m["role"],
                content=m["content"],
                citations=citations,
                created_at=str(m["created_at"]),
            )
        )

    return SessionDetailResponse(
        session_id=session_id,
        messages=messages,
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Primary chat endpoint.
    Processes resident queries through the coverage-first RAG pipeline.
    """
    session_id = request.session_id

    # 1. Resolve or create chat session
    if not session_id:
        new_session = await create_session()
        session_id = str(new_session["id"])
        logger.info("Created new session: %s", session_id)
    else:
        existing = await get_session(session_id)
        if not existing:
            new_session = await create_session()
            session_id = str(new_session["id"])
            logger.info("Supplied session invalid; created new session: %s", session_id)

    # 2. Fetch prior history for multi-turn conversational context (before saving current message)
    prior_history = await get_recent_messages(session_id=session_id, limit=8)

    # 3. Persist user turn
    await save_message(
        session_id=session_id,
        role="user",
        content=request.message,
    )

    # 4. Execute Coverage-First RAG Pipeline with conversational context
    rag_result = await run_rag_pipeline(
        user_question=request.message,
        history=prior_history,
    )

    # 5. Build verified citations payload
    citation_payloads = [
        {
            "chunk_id": c.chunk_id,
            "source": c.source,
            "page": c.page,
            "section": c.section,
            "snippet": c.snippet,
        }
        for c in rag_result.citations
    ]

    # 6. Persist assistant turn with verified citations
    await save_message(
        session_id=session_id,
        role="assistant",
        content=rag_result.answer,
        citations=citation_payloads,
    )

    citations_response = [Citation(**cp) for cp in citation_payloads]

    return ChatResponse(
        session_id=session_id,
        answer=rag_result.answer,
        citations=citations_response,
        unsupported_parts=rag_result.unsupported_parts,
        retrieval_doc_labels=rag_result.retrieval_doc_labels,
    )
