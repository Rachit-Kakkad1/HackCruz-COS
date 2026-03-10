"""
COS Backend — Analytics API.

GET /api/v1/analytics/usage-today — Per-domain time aggregation
GET /api/v1/analytics/focus-score — Productivity score
GET /api/v1/analytics/timeline    — Chronological capsule list
"""

import uuid
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.services import analytics_engine, focus_engine

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


@router.get("/usage-today")
async def usage_today(
    userId: str = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db),
):
    """Return per-domain time aggregation for today."""
    try:
        user_id = uuid.UUID(userId)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid userId — must be a valid UUID")
    return await analytics_engine.get_usage_today(db, user_id)


@router.get("/focus-score")
async def focus_score(
    userId: str = Query(..., description="User ID"),
    db: AsyncSession = Depends(get_db),
):
    """Return the current Focus Score (0-100)."""
    try:
        user_id = uuid.UUID(userId)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid userId — must be a valid UUID")
    return await focus_engine.calculate_focus_score(db, user_id)


@router.get("/timeline")
async def timeline(
    userId: str = Query(..., description="User ID"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Return chronological list of recent capsules for the Timeline UI."""
    try:
        user_id = uuid.UUID(userId)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid userId — must be a valid UUID")
    return await analytics_engine.get_timeline(db, user_id, limit)
