"""
COS Backend — FastAPI Application Entry Point.

Configures CORS, registers all API routers, and initializes
the database on startup (including the pgvector extension).
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database.connection import init_db
from app.services.event_queue import close_redis, get_queue_stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-30s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


# ─── Lifespan: Startup / Shutdown ─────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables and pgvector extension on startup."""
    logger.info("🧠 Starting COS Backend — Cognitive Memory System")
    await init_db()
    logger.info("✓ Database initialized with pgvector extension")
    yield
    await close_redis()
    logger.info("🛑 COS Backend shutting down")


# ─── FastAPI App ──────────────────────────────────────────────────────────
app = FastAPI(
    title="Context Scope (COS) — Cognitive Backend",
    description="AI-powered cognitive memory system for browsing activity.",
    version="1.0.0",
    lifespan=lifespan,
)

# ─── CORS ─────────────────────────────────────────────────────────────────
origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Register API Routers ────────────────────────────────────────────────
from app.api.events import router as events_router
from app.api.analytics import router as analytics_router
from app.api.search import router as search_router
from app.api.threads import router as threads_router
from app.api.context_map import router as context_map_router
from app.api.resume import router as resume_router

app.include_router(events_router)
app.include_router(analytics_router)
app.include_router(search_router)
app.include_router(threads_router)
app.include_router(context_map_router)
app.include_router(resume_router)


# ─── Health Check ─────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "service": "COS Cognitive Backend"}


@app.get("/health/queue", tags=["System"])
async def queue_health():
    """Return Redis event queue depths for pipeline monitoring."""
    stats = await get_queue_stats()
    return {"status": "ok", **stats}


# ─── User Data Deletion (Privacy) ────────────────────────────────────────
import uuid
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.database import repositories as repo


@app.delete("/api/v1/user/data", tags=["Privacy"])
async def delete_user_data(
    userId: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete ALL data for a user (GDPR right to erasure)."""
    user_id = uuid.UUID(userId)
    await repo.delete_user_data(db, user_id)
    return {"status": "deleted", "userId": userId}
