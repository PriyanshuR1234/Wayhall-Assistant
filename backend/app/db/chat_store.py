"""
Chat history CRUD — sessions and messages stored in Supabase PostgreSQL.
All heavy I/O is sync; expose async wrappers where needed.
"""

import asyncio
import uuid
from typing import List, Optional

from app.db.supabase import get_supabase
from app.utils.logger import get_logger

logger = get_logger(__name__)


# ── Sessions ──────────────────────────────────────────────────────────────────

def create_session_sync() -> dict:
    client = get_supabase()
    resp = client.table("chat_sessions").insert({}).execute()
    return resp.data[0]


async def create_session() -> dict:
    return await asyncio.to_thread(create_session_sync)


def get_session_sync(session_id: str) -> Optional[dict]:
    client = get_supabase()
    resp = (
        client.table("chat_sessions")
        .select("*")
        .eq("id", session_id)
        .maybe_single()
        .execute()
    )
    return resp.data


async def get_session(session_id: str) -> Optional[dict]:
    return await asyncio.to_thread(get_session_sync, session_id)


# ── Messages ──────────────────────────────────────────────────────────────────

def save_message_sync(
    session_id: str,
    role: str,
    content: str,
    citations: Optional[list] = None,
) -> dict:
    client = get_supabase()
    payload = {
        "session_id": session_id,
        "role": role,
        "content": content,
        "citations": citations or [],
    }
    resp = client.table("chat_messages").insert(payload).execute()
    return resp.data[0]


async def save_message(
    session_id: str,
    role: str,
    content: str,
    citations: Optional[list] = None,
) -> dict:
    return await asyncio.to_thread(save_message_sync, session_id, role, content, citations)


def get_recent_messages_sync(session_id: str, limit: int = 10) -> List[dict]:
    """Return the last `limit` messages ordered oldest-first for prompt building."""
    client = get_supabase()
    resp = (
        client.table("chat_messages")
        .select("role, content, citations, created_at")
        .eq("session_id", session_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    # Reverse so oldest message comes first
    return list(reversed(resp.data or []))


async def get_recent_messages(session_id: str, limit: int = 10) -> List[dict]:
    return await asyncio.to_thread(get_recent_messages_sync, session_id, limit)


def get_all_messages_sync(session_id: str) -> List[dict]:
    client = get_supabase()
    resp = (
        client.table("chat_messages")
        .select("role, content, citations, created_at")
        .eq("session_id", session_id)
        .order("created_at", desc=False)
        .execute()
    )
    return resp.data or []


async def get_all_messages(session_id: str) -> List[dict]:
    return await asyncio.to_thread(get_all_messages_sync, session_id)
