"""
Pydantic request models for all API endpoints.
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str | None = Field(
        default=None,
        description="Existing chat session UUID. Pass null to start a new session.",
    )
    message: str = Field(
        min_length=2,
        max_length=2000,
        description="The user's question (2–2000 characters).",
    )


class CreateSessionRequest(BaseModel):
    """Optional — a session is also auto-created inside /chat if session_id is null."""

    pass
