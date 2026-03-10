"""
COS Backend — Async SQLAlchemy Database Connection.

Provides the async engine, session factory, and base model.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

# ─── Async Engine ──────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

# ─── Session Factory ───────────────────────────────────────────────────────
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ─── Base Model ────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ─── Dependency for FastAPI ────────────────────────────────────────────────
async def get_db() -> AsyncSession:
    """Yield an async database session for use as a FastAPI dependency."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ─── Initialization Helper ────────────────────────────────────────────────
async def init_db():
    """Create all tables and enable pgvector extension."""
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
