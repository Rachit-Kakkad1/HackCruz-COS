"""
COS Backend — Analytics Engine Service.

Powers the dashboard: usage breakdown, timeline, and domain aggregation.
"""

from datetime import datetime
from collections import defaultdict
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import repositories as repo


async def get_usage_today(db: AsyncSession, user_id: uuid.UUID) -> dict:
    """
    Aggregate time-per-domain for today.
    Returns data for the TimeGraph component.
    """
    capsules = await repo.get_capsules_today(db, user_id)

    domain_time = defaultdict(int)
    prev_ts = None

    for capsule in capsules:
        if prev_ts:
            delta = (capsule.timestamp - prev_ts).total_seconds()
            if delta < 1800:  # Max 30min per gap
                domain_time[capsule.domain] += int(delta)
        prev_ts = capsule.timestamp

    # Sort by time descending
    sorted_domains = sorted(domain_time.items(), key=lambda x: -x[1])
    return {
        "domains": [
            {
                "domain": d,
                "seconds": s,
                "minutes": round(s / 60, 1),
            }
            for d, s in sorted_domains[:15]
        ],
        "total_minutes": round(sum(domain_time.values()) / 60, 1),
        "capsule_count": len(capsules),
    }


async def get_timeline(
    db: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 50,
) -> list[dict]:
    """
    Return a chronological list of capsules for the Timeline component.
    """
    capsules = await repo.get_recent_capsules(db, user_id, limit)

    return [
        {
            "id": str(c.id),
            "title": c.title,
            "domain": c.domain,
            "url": c.url,
            "timestamp": c.timestamp.isoformat(),
            "favicon": f"https://www.google.com/s2/favicons?domain={c.domain}&sz=64",
        }
        for c in reversed(capsules)
    ]
