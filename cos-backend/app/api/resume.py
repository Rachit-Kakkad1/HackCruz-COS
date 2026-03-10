"""
COS Backend — Context Resume API.

GET /api/v1/resume?userId=... — Returns context resume suggestions.

Tells the user what they were working on and suggests resuming.
Uses the existing thread, capsule, and cluster data.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.connection import get_db
from app.database.models import Thread, ThreadCapsule, Capsule
from cos_brain.resume_engine import ResumeEngine

router = APIRouter(prefix="/api/v1", tags=["Resume"])
resume_engine = ResumeEngine()


@router.get("/resume")
async def get_resume_suggestions(
    userId: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get context resume suggestions for a user.

    Returns up to 3 ranked suggestions based on recent threads,
    sorted by confidence (recency × depth).

    Example response:
    {
        "suggestions": [
            {
                "threadId": "...",
                "title": "Debugging AWS Cognito Auth",
                "lastStep": "StackOverflow: JWT verification fix",
                "lastUrl": "https://stackoverflow.com/...",
                "minutesAgo": 42,
                "pageCount": 7,
                "domains": ["stackoverflow.com", "docs.aws.amazon.com"],
                "confidence": 0.82
            }
        ]
    }
    """
    try:
        user_id = uuid.UUID(userId)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid userId — must be a valid UUID")

    # Fetch active/recent threads with their capsules
    result = await db.execute(
        select(Thread)
        .where(Thread.user_id == user_id)
        .where(Thread.status.in_(["active", "completed"]))
        .order_by(Thread.updated_at.desc())
        .limit(10)
    )
    threads = list(result.scalars().all())

    if not threads:
        return {"suggestions": []}

    # Build thread dicts with capsule data
    thread_dicts = []
    for thread in threads:
        # Fetch capsules for this thread
        caps_result = await db.execute(
            select(Capsule)
            .join(ThreadCapsule, ThreadCapsule.capsule_id == Capsule.id)
            .where(ThreadCapsule.thread_id == thread.id)
            .order_by(Capsule.timestamp.asc())
        )
        capsules = list(caps_result.scalars().all())

        thread_dicts.append({
            "id": str(thread.id),
            "title": thread.title,
            "updated_at": thread.updated_at,
            "status": thread.status,
            "capsules": [
                {
                    "title": c.title,
                    "url": c.url,
                    "domain": c.domain,
                    "timestamp": c.timestamp,
                }
                for c in capsules
            ],
        })

    # Generate suggestions
    suggestions = resume_engine.generate_suggestions(
        thread_dicts, now=datetime.now(timezone.utc)
    )

    return {
        "suggestions": resume_engine.format_for_ui(suggestions),
    }
