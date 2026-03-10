"""
COS Backend — Knowledge Service.

Handles consolidation of threads into long-term knowledge records.
"""

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.models import Thread, ThreadCapsule, Capsule, KnowledgeRecord
from app.database import repositories as repo
from app.ai import generate_thread_summary


async def consolidate_thread(
    db: AsyncSession,
    thread: Thread,
) -> KnowledgeRecord:
    """
    Convert a completed thread into a long-term knowledge record.
    This is the memory consolidation process.
    """
    # Get all capsules in the thread
    caps_result = await db.execute(
        select(Capsule)
        .join(ThreadCapsule, ThreadCapsule.capsule_id == Capsule.id)
        .where(ThreadCapsule.thread_id == thread.id)
        .order_by(Capsule.timestamp.asc())
    )
    capsules = list(caps_result.scalars().all())

    titles = [c.title for c in capsules]
    urls = [c.url for c in capsules]

    # Try LLM summary first
    summary = await generate_thread_summary(thread.title or "", titles, urls)

    # Create knowledge record
    from cos_brain.knowledge_engine import KnowledgeEngine
    engine = KnowledgeEngine()
    knowledge = engine.extract_knowledge_from_thread(
        thread.title or "Unknown", titles, urls, summary
    )

    record = await repo.create_knowledge_record(
        db,
        user_id=thread.user_id,
        problem=knowledge.problem,
        sources=knowledge.sources,
        conclusion=knowledge.conclusion,
        thread_id=thread.id,
    )

    # Mark thread as archived
    thread.status = "archived"
    thread.summary = summary or knowledge.conclusion
    thread.updated_at = datetime.utcnow()
    await db.flush()

    return record
