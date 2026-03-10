"""
COS Backend — Focus Engine Service.

Calculates the Focus Score using the formula from user review:
FocusScore = (ProductiveTime / TotalTime) × 100 − ContextSwitchPenalty
"""

import re
import uuid
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import repositories as repo

# ─── Default Productive Domain Patterns ───────────────────────────────────
DEFAULT_PRODUCTIVE = [
    r"github\.com", r"gitlab\.com", r"stackoverflow\.com",
    r"docs\.", r"developer\.", r"learn\.", r"medium\.com",
    r"notion\.so", r"figma\.com", r"linear\.app",
    r"aws\.amazon\.com", r"cloud\.google\.com",
]

DEFAULT_DISTRACTING = [
    r"youtube\.com", r"twitter\.com", r"x\.com", r"reddit\.com",
    r"facebook\.com", r"instagram\.com", r"tiktok\.com",
    r"netflix\.com", r"twitch\.tv",
]


def _is_productive(domain: str, rules: list = None) -> bool:
    """Check if a domain matches productive patterns."""
    patterns = rules or DEFAULT_PRODUCTIVE
    return any(re.search(p, domain) for p in patterns)


def _is_distracting(domain: str, rules: list = None) -> bool:
    """Check if a domain matches distracting patterns."""
    patterns = rules or DEFAULT_DISTRACTING
    return any(re.search(p, domain) for p in patterns)


async def calculate_focus_score(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> dict:
    """
    Calculate the Focus Score (0-100).

    Formula (from user review):
    FocusScore = (ProductiveTime / TotalTime) × 100 − ContextSwitchPenalty

    ContextSwitchPenalty = min(30, switches_per_hour × 2)
    """
    capsules = await repo.get_capsules_today(db, user_id)

    if not capsules:
        return {
            "score": 100,
            "productive_minutes": 0,
            "distracting_minutes": 0,
            "neutral_minutes": 0,
            "context_switches": 0,
            "penalty": 0,
        }

    # Calculate per-domain time
    domain_time = defaultdict(int)
    prev_ts = None
    prev_domain = None
    context_switches = 0

    for cap in capsules:
        if prev_ts:
            delta = (cap.timestamp - prev_ts).total_seconds()
            if delta < 1800:
                domain_time[cap.domain] += int(delta)
        if prev_domain and prev_domain != cap.domain:
            context_switches += 1
        prev_ts = cap.timestamp
        prev_domain = cap.domain

    total_seconds = sum(domain_time.values()) or 1
    productive_seconds = sum(s for d, s in domain_time.items() if _is_productive(d))
    distracting_seconds = sum(s for d, s in domain_time.items() if _is_distracting(d))
    neutral_seconds = total_seconds - productive_seconds - distracting_seconds

    # Calculate raw score
    raw_score = (productive_seconds / total_seconds) * 100

    # Context switch penalty (per user feedback formula)
    hours = max(total_seconds / 3600, 1)
    switches_per_hour = context_switches / hours
    penalty = min(30, switches_per_hour * 2)

    score = max(0, min(100, round(raw_score - penalty)))

    return {
        "score": score,
        "productive_minutes": round(productive_seconds / 60, 1),
        "distracting_minutes": round(distracting_seconds / 60, 1),
        "neutral_minutes": round(neutral_seconds / 60, 1),
        "context_switches": context_switches,
        "penalty": round(penalty, 1),
    }
