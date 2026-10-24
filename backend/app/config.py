"""
Application configuration — loaded from .env via pydantic-settings.
All runtime settings live here; nothing else imports os.getenv directly.
"""

from functools import lru_cache
from typing import List

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[".env", "../.env"],
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Supabase ────────────────────────────────────────────────────────────
    SUPABASE_URL: str = Field(
        default="",
        validation_alias=AliasChoices("SUPABASE_URL", "PROJECT_URL"),
    )
    SUPABASE_SECRET_KEY: str = Field(
        default="",
        validation_alias=AliasChoices("SUPABASE_SECRET_KEY", "SECRET_KEY"),
    )
    SUPABASE_PUBLISHABLE_KEY: str = Field(
        default="",
        validation_alias=AliasChoices("SUPABASE_PUBLISHABLE_KEY", "PUBLISHABLE_KEY"),
    )

    # ── Google Gemini ────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    GEMINI_EMBED_MODEL: str = "models/gemini-embedding-001"
    GEMINI_LLM_MODEL: str = "models/gemini-3.5-flash-lite"
    EMBEDDING_DIMENSIONS: int = 768

    # ── Ingestion & Chunking ─────────────────────────────────────────────────
    CHUNK_SIZE: int = 700
    CHUNK_OVERLAP: int = 120

    # ── RAG pipeline tuning ──────────────────────────────────────────────────
    TOP_K_PER_DOC: int = 5          # candidates per document per method
    MAX_HISTORY_TURNS: int = 8      # conversation turns sent to LLM
    RETRY_ATTEMPTS: int = 3
    RETRY_BASE_DELAY: float = 2.0   # seconds — doubles on each retry

    # ── CORS ─────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "*",
    ]

    @property
    def CORS_ORIGINS(self) -> List[str]:
        return self.ALLOWED_ORIGINS

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        """Accept comma-separated string or a list."""
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
