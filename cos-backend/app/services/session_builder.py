"""
COS Backend — Session Builder Service.

Manages browsing sessions: time-bounded windows of activity with
domain aggregation and context switch counting.
"""

from datetime import datetime, timedelta
from typing import Optional
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.database.models import Session


async def get_or_create_session(
    db: AsyncSession,
    user_id: uuid.UUID,
    timestamp: datetime,
    gap_minutes: int = 30,
) -> Session:
    """
    Find the current active session or create a new one.
    A session is considered active if the last event was within gap_minutes.
    """
    cutoff = timestamp - timedelta(minutes=gap_minutes)
    result = await db.execute(
        select(Session)
        .where(
            Session.user_id == user_id,
            Session.end_time >= cutoff,
        )
        .order_by(Session.end_time.desc())
        .limit(1)
    )
    session = result.scalar_one_or_none()

    if session:
        # Update end time
        session.end_time = timestamp
        session.total_switches = (session.total_switches or 0) + 1
    else:
        session = Session(
            user_id=user_id,
            start_time=timestamp,
            end_time=timestamp,
            domain_stats={},
            total_switches=0,
        )
        db.add(session)

    await db.flush()
    return session


async def update_domain_stats(
    db: AsyncSession,
    session: Session,
    domain: str,
    seconds: int = 0,
):
    """Add time to a domain's counter within a session."""
    stats = session.domain_stats or {}
    stats[domain] = stats.get(domain, 0) + seconds
    session.domain_stats = stats
    await db.flush()
