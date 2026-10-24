"""
FastAPI application entry point for Wayhall Municipal Knowledge Assistant.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.chat import router as chat_router
from app.api.routes.documents import router as documents_router
from app.api.routes.feedback import router as feedback_router
from app.config import settings
from app.db.supabase import get_supabase
from app.db.vector_store import count_chunks
from app.models.responses import HealthResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Wayhall Municipal Knowledge Assistant API",
    description=(
        "Production-grade, coverage-first RAG backend for North American "
        "municipal service requests, bylaws, and permits."
    ),
    version="1.0.0",
)

# ── CORS Middleware ───────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount API Routes ──────────────────────────────────────────────────────────
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(feedback_router)


# ── Global Exception Handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server error on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred. Our team has been notified.",
            "error_type": exc.__class__.__name__,
        },
    )


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """System health check: verifies database connection and indexed document count."""
    db_status = "healthy"
    chunks_count = 0
    try:
        chunks_count = count_chunks()
        if chunks_count < 0:
            db_status = "degraded"
    except Exception as exc:
        logger.error("Database health check error: %s", exc)
        db_status = "unreachable"

    gemini_status = "configured" if settings.GEMINI_API_KEY else "missing_key"

    overall_status = "healthy" if db_status == "healthy" and gemini_status == "configured" else "degraded"

    return HealthResponse(
        status=overall_status,
        db=db_status,
        gemini=gemini_status,
        chunks_indexed=chunks_count,
    )


@app.get("/", tags=["System"])
async def root():
    return {
        "service": "Wayhall Municipal Knowledge Assistant",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
    }
