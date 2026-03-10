"""
COS Backend — Threads API.

GET /api/v1/threads         — List reasoning threads
GET /api/v1/threads/{id}    — Thread detail with capsules
"""

import uuid

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.database import repositories as repo
from app.services import thread_service

router = APIRouter(prefix="/api/v1/threads", tags=["Threads"])


@router.get("")
async def list_threads(
    userId: str = Query(..., description="User ID"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List reasoning threads for a user, newest first."""
    try:
        user_id = uuid.UUID(userId)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid userId — must be a valid UUID")
    threads = await repo.get_threads_for_user(db, user_id, limit)
    return [
        {
            "id": str(t.id),
            "title": t.title,
            "summary": t.summary,
            "status": t.status,
            "created_at": t.created_at.isoformat(),
            "updated_at": t.updated_at.isoformat(),
        }
        for t in threads
    ]


@router.get("/{thread_id}")
async def get_thread(
    thread_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific thread with its linked capsules."""
    tid = uuid.UUID(thread_id)
    result = await thread_service.get_thread_with_capsules(db, tid)
    if not result:
        raise HTTPException(status_code=404, detail="Thread not found")
    return result
