"""
COS Brain — Reasoning Thread Engine.

Creates and extends reasoning threads from capsule clusters.
A thread represents a coherent user task (e.g., "Debugging React auth bug").
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid


@dataclass
class ReasoningThread:
    """Pure data model for a reasoning thread."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    title: Optional[str] = None
    summary: Optional[str] = None
    status: str = "active"  # active | completed | archived
    capsule_ids: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ThreadEngine:
    """
    Manages reasoning threads.

    Thread creation rules:
    - A new thread is created when a cluster forms without an active thread.
    - A capsule extends an existing thread if semantic similarity > threshold
      AND time gap < max_gap.
    """

    def __init__(
        self,
        similarity_threshold: float = 0.75,
        max_gap_minutes: int = 20,
    ):
        self.similarity_threshold = similarity_threshold
        self.max_gap_minutes = max_gap_minutes

    def should_extend_thread(
        self,
        thread_updated_at: datetime,
        capsule_timestamp: datetime,
    ) -> bool:
        """Check if a capsule should extend an existing thread (time-check)."""
        gap = abs((capsule_timestamp - thread_updated_at).total_seconds())
        return gap <= self.max_gap_minutes * 60

    def generate_fallback_title(self, capsule_titles: list[str]) -> str:
        """
        Generate a thread title without an LLM — uses TF-IDF-style keyword
        extraction from capsule titles (per user feedback: better than first-sentence).
        """
        if not capsule_titles:
            return "Untitled Thread"

        # Count word frequency across titles, filter stop words
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "in", "on", "at",
            "to", "for", "of", "with", "and", "or", "but", "not", "this",
            "that", "it", "by", "from", "as", "be", "has", "had", "have",
            "will", "can", "do", "does", "did", "-", "–", "|", "·",
        }
        word_freq: dict[str, int] = {}
        for title in capsule_titles:
            for word in title.lower().split():
                word = word.strip(".,!?():;\"'")
                if word and word not in stop_words and len(word) > 2:
                    word_freq[word] = word_freq.get(word, 0) + 1

        # Take the top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: -x[1])
        top_keywords = [w for w, _ in sorted_words[:5]]

        if not top_keywords:
            return capsule_titles[0][:80]

        return " ".join(kw.capitalize() for kw in top_keywords)

    def should_complete_thread(
        self,
        thread_updated_at: datetime,
        inactivity_minutes: int = 60,
    ) -> bool:
        """Check if a thread should be marked completed due to prolonged inactivity."""
        gap = (datetime.now(timezone.utc) - thread_updated_at).total_seconds()
        return gap > inactivity_minutes * 60

    # Alias for background worker compatibility
    generate_thread_title_from_keywords = generate_fallback_title
