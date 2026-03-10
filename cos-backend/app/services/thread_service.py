"""
COS Backend — Thread Service.

Bridges the brain's thread engine with the database layer to
manage reasoning threads at the API level.
"""

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import repositories as repo
from app.database.models import Thread, ThreadCapsule, Capsule
from app.ai import generate_thread_title


async def get_thread_with_capsules(
    db: AsyncSession,
    thread_id: uuid.UUID,
) -> dict:
    """Get a thread with its linked capsules."""
    result = await db.execute(select(Thread).where(Thread.id == thread_id))
    thread = result.scalar_one_or_none()
    if not thread:
        return None

    # Get linked capsules
    caps_result = await db.execute(
        select(Capsule)
        .join(ThreadCapsule, ThreadCapsule.capsule_id == Capsule.id)
        .where(ThreadCapsule.thread_id == thread_id)
        .order_by(Capsule.timestamp.asc())
    )
    capsules = list(caps_result.scalars().all())

    return {
        "id": str(thread.id),
        "title": thread.title,
        "summary": thread.summary,
        "status": thread.status,
        "created_at": thread.created_at.isoformat(),
        "updated_at": thread.updated_at.isoformat(),
        "capsules": [
            {
                "id": str(c.id),
                "title": c.title,
                "domain": c.domain,
                "url": c.url,
                "timestamp": c.timestamp.isoformat(),
            }
            for c in capsules
        ],
    }


async def maybe_update_thread_title(
    db: AsyncSession,
    thread: Thread,
    capsule_titles: list[str],
):
    """
    Attempt to generate a better title for a thread using LLM.
    Only runs if thread currently has no title or a placeholder.
    """
    if thread.title and not thread.title.startswith("Untitled"):
        return

    llm_title = await generate_thread_title(capsule_titles)
    if llm_title:
        thread.title = llm_title
    else:
        # Fallback: TF-IDF keyword extraction
        from cos_brain.thread_engine import ThreadEngine
        engine = ThreadEngine()
        thread.title = engine.generate_fallback_title(capsule_titles)

    thread.updated_at = datetime.utcnow()
    await db.flush()
