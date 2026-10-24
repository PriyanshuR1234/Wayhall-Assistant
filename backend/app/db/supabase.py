"""
Supabase client singleton — shared across the application.
Uses the service-role key (backend only — never exposed to the frontend).
"""

from supabase import create_client, Client
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_client: Client | None = None


def get_supabase() -> Client:
    """Return the shared Supabase client, initialising it on first call."""
    global _client
    if _client is None:
        logger.info("Initialising Supabase client → %s", settings.SUPABASE_URL)
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SECRET_KEY)
        logger.info("Supabase client ready.")
    return _client
