"""
COS Brain — Decision Memory.

Detects and stores important decisions made during research sessions.
Allows the system to answer questions like "Why did I choose X?"
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class DecisionRecord:
    """A decision detected from a browsing research session."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    title: str = ""
    reason: Optional[str] = None
    thread_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


class DecisionMemory:
    """
    Detects decisions from browsing patterns.

    Decision detection heuristics (used when no LLM is available):
    - User visits comparison pages (e.g., "X vs Y")
    - User reads documentation + alternatives, then focuses on one
    - Thread shifts from broad exploration to narrow implementation
    """

    # Keywords that indicate decision-making activity
    DECISION_KEYWORDS = [
        "vs", "versus", "comparison", "alternative", "choose", "choosing",
        "best", "review", "pricing", "pros", "cons", "decision",
        "migrate", "migration", "switch", "replace", "instead",
    ]

    def detect_decision_signal(self, capsule_titles: list[str]) -> bool:
        """
        Heuristic check: do the titles suggest a decision was being made?
        """
        combined = " ".join(t.lower() for t in capsule_titles)
        return any(kw in combined for kw in self.DECISION_KEYWORDS)

    def create_decision_from_titles(
        self,
        capsule_titles: list[str],
        user_id: str,
        thread_id: str = None,
    ) -> Optional[DecisionRecord]:
        """
        Create a decision record from capsule titles using heuristic extraction.
        In production, an LLM would generate the title and reason.
        """
        if not self.detect_decision_signal(capsule_titles):
            return None

        # Build a decision title from the comparison pattern
        title = self._extract_decision_title(capsule_titles)
        reason = f"Based on research across {len(capsule_titles)} sources"

        return DecisionRecord(
            user_id=user_id,
            title=title,
            reason=reason,
            thread_id=thread_id,
        )

    def _extract_decision_title(self, titles: list[str]) -> str:
        """Extract a decision title from comparison-style page titles."""
        for title in titles:
            lower = title.lower()
            if " vs " in lower or "versus" in lower or "comparison" in lower:
                return f"Decision: {title[:100]}"
        return f"Decision from: {titles[0][:80]}" if titles else "Unknown decision"
