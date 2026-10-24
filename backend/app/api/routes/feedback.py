"""
Feedback API route — enables residents to rate answer helpfulness
and submit citation validation feedback.
"""

from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.db.supabase import get_supabase
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/feedback", tags=["Feedback"])


class FeedbackRequest(BaseModel):
    session_id: str
    message_id: Optional[str] = None
    rating: int = Field(ge=1, le=5, description="1 to 5 rating scale")
    helpful: bool
    comments: Optional[str] = None


@router.post("")
async def submit_feedback(request: FeedbackRequest):
    """Log feedback for evaluation and observability."""
    logger.info(
        "Feedback received for session %s: helpful=%s, rating=%d, comments=%s",
        request.session_id,
        request.helpful,
        request.rating,
        request.comments,
    )
    # Also attempt to record if feedback table exists, fallback to log without breaking
    try:
        client = get_supabase()
        client.table("chat_feedback").insert(
            {
                "session_id": request.session_id,
                "rating": request.rating,
                "helpful": request.helpful,
                "comments": request.comments,
            }
        ).execute()
    except Exception:
        # Table might not exist yet; structured logging handles persistence
        pass

    return {"status": "ok", "message": "Thank you for your feedback!"}
