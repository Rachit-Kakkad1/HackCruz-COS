"""
COS Backend — Database Repository Layer.

Async CRUD operations for all models. Each function takes an AsyncSession
and returns results — no HTTP coupling.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, delete, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    User, Capsule, Session, Cluster, Thread, ThreadCapsule,
    ContextEdge, KnowledgeRecord, Decision, FocusRule,
)
from app.config import get_settings

settings = get_settings()


# ═══════════════════════════════════════════════════════════════════════════
# USERS
# ═══════════════════════════════════════════════════════════════════════════

async def get_or_create_user(db: AsyncSession, user_id: str) -> User:
    """Get user by ID, or create one if it doesn't exist."""
    uid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    if not user:
        user = User(id=uid)
        db.add(user)
        await db.flush()
    return user


# ═══════════════════════════════════════════════════════════════════════════
# CAPSULES
# ═══════════════════════════════════════════════════════════════════════════

async def create_capsule(
    db: AsyncSession, user_id: uuid.UUID, url: str, title: str,
    domain: str, text_content: str = None, timestamp: datetime = None,
    embedding: list = None,
) -> Capsule:
    """Create and persist a new context capsule."""
    capsule = Capsule(
        user_id=user_id, url=url, title=title, domain=domain,
        text_content=text_content,
        timestamp=timestamp or datetime.utcnow(),
        embedding=embedding,
        is_processed=embedding is not None,
    )
    db.add(capsule)
    await db.flush()
    return capsule


async def get_recent_capsules(
    db: AsyncSession, user_id: uuid.UUID, limit: int = 20,
) -> list[Capsule]:
    """Fetch the N most recent capsules for a user (working memory)."""
    result = await db.execute(
        select(Capsule)
        .where(Capsule.user_id == user_id)
        .order_by(Capsule.timestamp.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_capsules_today(db: AsyncSession, user_id: uuid.UUID) -> list[Capsule]:
    """Fetch all capsules from today."""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(Capsule)
        .where(Capsule.user_id == user_id, Capsule.timestamp >= today)
        .order_by(Capsule.timestamp.asc())
    )
    return list(result.scalars().all())


async def get_unprocessed_capsules(db: AsyncSession, limit: int = 50) -> list[Capsule]:
    """Fetch capsules awaiting embedding generation."""
    result = await db.execute(
        select(Capsule)
        .where(Capsule.is_processed == False)
        .order_by(Capsule.timestamp.asc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def search_capsules_by_vector(
    db: AsyncSession, user_id: uuid.UUID, query_embedding: list, limit: int = 10,
) -> list[Capsule]:
    """Semantic vector search via pgvector nearest-neighbor."""
    result = await db.execute(
        select(Capsule)
        .where(Capsule.user_id == user_id, Capsule.embedding.isnot(None))
        .order_by(Capsule.embedding.cosine_distance(query_embedding))
        .limit(limit)
    )
    return list(result.scalars().all())


# ═══════════════════════════════════════════════════════════════════════════
# CLUSTERS
# ═══════════════════════════════════════════════════════════════════════════

async def create_cluster(
    db: AsyncSession, user_id: uuid.UUID, label: str = None, centroid: list = None,
) -> Cluster:
    cluster = Cluster(user_id=user_id, label=label, centroid=centroid)
    db.add(cluster)
    await db.flush()
    return cluster


async def get_active_clusters(
    db: AsyncSession, user_id: uuid.UUID, hours: int = 4,
) -> list[Cluster]:
    """Clusters updated within the last N hours."""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    result = await db.execute(
        select(Cluster)
        .where(Cluster.user_id == user_id, Cluster.updated_at >= cutoff)
        .order_by(Cluster.updated_at.desc())
    )
    return list(result.scalars().all())


# ═══════════════════════════════════════════════════════════════════════════
# THREADS
# ═══════════════════════════════════════════════════════════════════════════

async def create_thread(
    db: AsyncSession, user_id: uuid.UUID, title: str = None, summary: str = None,
) -> Thread:
    thread = Thread(user_id=user_id, title=title, summary=summary)
    db.add(thread)
    await db.flush()
    return thread


async def get_active_threads(db: AsyncSession, user_id: uuid.UUID) -> list[Thread]:
    result = await db.execute(
        select(Thread)
        .where(Thread.user_id == user_id, Thread.status == "active")
        .order_by(Thread.updated_at.desc())
    )
    return list(result.scalars().all())


async def get_threads_for_user(db: AsyncSession, user_id: uuid.UUID, limit: int = 20) -> list[Thread]:
    result = await db.execute(
        select(Thread)
        .where(Thread.user_id == user_id)
        .order_by(Thread.updated_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def link_capsule_to_thread(
    db: AsyncSession, thread_id: uuid.UUID, capsule_id: uuid.UUID,
):
    link = ThreadCapsule(thread_id=thread_id, capsule_id=capsule_id)
    db.add(link)
    await db.flush()


# ═══════════════════════════════════════════════════════════════════════════
# CONTEXT EDGES
# ═══════════════════════════════════════════════════════════════════════════

async def create_edge(
    db: AsyncSession, source_id: uuid.UUID, target_id: uuid.UUID,
    edge_type: str, weight: float = 1.0,
) -> ContextEdge:
    edge = ContextEdge(
        source_id=source_id, target_id=target_id,
        edge_type=edge_type, weight=weight,
    )
    db.add(edge)
    await db.flush()
    return edge


async def get_edges_for_capsules(
    db: AsyncSession, capsule_ids: list[uuid.UUID],
) -> list[ContextEdge]:
    """Get all edges where source or target is in the given capsule set."""
    if not capsule_ids:
        return []
    result = await db.execute(
        select(ContextEdge).where(
            (ContextEdge.source_id.in_(capsule_ids)) |
            (ContextEdge.target_id.in_(capsule_ids))
        )
    )
    return list(result.scalars().all())


async def count_edges_for_capsule(
    db: AsyncSession, capsule_id: uuid.UUID, edge_type: str,
) -> int:
    """Count edges of a given type emanating from a capsule (explosion protection)."""
    result = await db.execute(
        select(func.count(ContextEdge.id))
        .where(ContextEdge.source_id == capsule_id, ContextEdge.edge_type == edge_type)
    )
    return result.scalar() or 0


# ═══════════════════════════════════════════════════════════════════════════
# KNOWLEDGE RECORDS
# ═══════════════════════════════════════════════════════════════════════════

async def create_knowledge_record(
    db: AsyncSession, user_id: uuid.UUID, problem: str,
    sources: list, conclusion: str, thread_id: uuid.UUID = None,
) -> KnowledgeRecord:
    record = KnowledgeRecord(
        user_id=user_id, problem=problem, sources=sources,
        conclusion=conclusion, thread_id=thread_id,
    )
    db.add(record)
    await db.flush()
    return record


# ═══════════════════════════════════════════════════════════════════════════
# DECISIONS
# ═══════════════════════════════════════════════════════════════════════════

async def create_decision(
    db: AsyncSession, user_id: uuid.UUID, title: str, reason: str = None,
    thread_id: uuid.UUID = None,
) -> Decision:
    decision = Decision(
        user_id=user_id, title=title, reason=reason, thread_id=thread_id,
    )
    db.add(decision)
    await db.flush()
    return decision


# ═══════════════════════════════════════════════════════════════════════════
# FOCUS RULES
# ═══════════════════════════════════════════════════════════════════════════

async def get_focus_rules(db: AsyncSession, user_id: uuid.UUID) -> list[FocusRule]:
    result = await db.execute(
        select(FocusRule).where(FocusRule.user_id == user_id)
    )
    return list(result.scalars().all())


# ═══════════════════════════════════════════════════════════════════════════
# DATA RETENTION
# ═══════════════════════════════════════════════════════════════════════════

async def purge_old_capsules(db: AsyncSession, days: int = 30) -> int:
    """Delete capsules older than N days. Returns count of deleted rows."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        delete(Capsule).where(Capsule.timestamp < cutoff)
    )
    return result.rowcount


async def delete_user_data(db: AsyncSession, user_id: uuid.UUID):
    """Delete ALL data for a user (GDPR-style right to erasure)."""
    await db.execute(delete(Capsule).where(Capsule.user_id == user_id))
    await db.execute(delete(Thread).where(Thread.user_id == user_id))
    await db.execute(delete(Cluster).where(Cluster.user_id == user_id))
    await db.execute(delete(KnowledgeRecord).where(KnowledgeRecord.user_id == user_id))
    await db.execute(delete(Decision).where(Decision.user_id == user_id))
    await db.execute(delete(FocusRule).where(FocusRule.user_id == user_id))
    await db.execute(delete(User).where(User.id == user_id))
    await db.flush()
