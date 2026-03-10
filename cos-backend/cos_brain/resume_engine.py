"""
COS Brain — Context Resume Engine.

Detects what the user was working on and suggests resuming.

When a user returns to the browser after inactivity, this module
analyzes their most recent threads, capsules, and graph to generate
a resume suggestion like:

    "You were working on: Debugging AWS Cognito Auth
     Last step: Investigating StackOverflow solution
     Resume?"

Uses the existing thread, cluster, and capsule data — no new storage needed.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ResumeSuggestion:
    """A suggestion for what the user should resume working on."""
    thread_title: str
    thread_id: str
    last_capsule_title: str
    last_capsule_url: str
    last_active: datetime
    minutes_ago: int
    capsule_count: int
    related_domains: list[str]
    confidence: float  # 0.0 – 1.0


class ResumeEngine:
    """
    Analyzes recent browsing context to generate resume suggestions.

    Logic:
    1. Find the user's most recently active threads
    2. Score threads by recency + depth (capsule count)
    3. Generate a ResumeSuggestion for the best candidate
    """

    def __init__(
        self,
        max_idle_hours: int = 12,
        min_capsules_for_resume: int = 2,
    ):
        self.max_idle_hours = max_idle_hours
        self.min_capsules = min_capsules_for_resume

    def generate_suggestions(
        self,
        threads: list[dict],
        now: Optional[datetime] = None,
    ) -> list[ResumeSuggestion]:
        """
        Generate ranked resume suggestions from recent threads.

        Each thread dict should contain:
            id, title, updated_at, status, capsules: [{title, url, domain, timestamp}]

        Returns up to 3 suggestions, sorted by confidence.
        """
        now = now or datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=self.max_idle_hours)
        suggestions = []

        for thread in threads:
            # Skip inactive threads
            updated = thread.get("updated_at")
            if not updated or updated < cutoff:
                continue

            # Skip threads with too few capsules
            capsules = thread.get("capsules", [])
            if len(capsules) < self.min_capsules:
                continue

            # Score by recency and depth
            minutes_ago = int((now - updated).total_seconds() / 60)
            recency_score = max(0.0, 1.0 - (minutes_ago / (self.max_idle_hours * 60)))
            depth_score = min(1.0, len(capsules) / 10)
            confidence = round(0.6 * recency_score + 0.4 * depth_score, 3)

            # Collect unique domains
            domains = list(set(c.get("domain", "") for c in capsules if c.get("domain")))

            # Get the last capsule
            last = capsules[-1] if capsules else {}

            # Title fallback: if thread has no title, use domains
            title = thread.get("title") or self._generate_fallback_title(capsules)

            suggestions.append(ResumeSuggestion(
                thread_title=title,
                thread_id=str(thread["id"]),
                last_capsule_title=last.get("title", ""),
                last_capsule_url=last.get("url", ""),
                last_active=updated,
                minutes_ago=minutes_ago,
                capsule_count=len(capsules),
                related_domains=domains[:5],
                confidence=confidence,
            ))

        # Sort by confidence descending, return top 3
        suggestions.sort(key=lambda s: -s.confidence)
        return suggestions[:3]

    def _generate_fallback_title(self, capsules: list[dict]) -> str:
        """Generate a title from capsule domains + keywords if thread is untitled."""
        domains = list(set(c.get("domain", "") for c in capsules if c.get("domain")))
        if len(domains) == 1:
            return f"Research on {domains[0]}"
        elif len(domains) <= 3:
            return f"Working across {', '.join(domains[:3])}"
        else:
            return f"Multi-topic research ({len(capsules)} pages)"

    def format_for_ui(self, suggestions: list[ResumeSuggestion]) -> list[dict]:
        """Format suggestions for the Chrome extension popup."""
        return [
            {
                "threadId": s.thread_id,
                "title": s.thread_title,
                "lastStep": s.last_capsule_title,
                "lastUrl": s.last_capsule_url,
                "minutesAgo": s.minutes_ago,
                "pageCount": s.capsule_count,
                "domains": s.related_domains,
                "confidence": s.confidence,
            }
            for s in suggestions
        ]
