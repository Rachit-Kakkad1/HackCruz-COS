"""
COS Brain — Working Memory.

Tracks what the user is currently thinking about: the active thread,
recent capsules, cluster centroid, and last interaction timestamp.
Working memory expires after inactivity and holds at most 20 capsules.
"""

from datetime import datetime, timedelta
from typing import Optional

from cos_brain.capsule import ContextCapsule
from cos_brain.embedding_engine import cosine_similarity

import numpy as np


class WorkingMemory:
    """
    In-memory buffer simulating cognitive working memory.

    Contains:
    - Recent capsules (max 20)
    - Active thread ID
    - Cluster centroid (running average of embeddings)
    - Last interaction timestamp (for drift detection)
    """

    def __init__(self, max_size: int = 20, timeout_minutes: int = 20):
        self.max_size = max_size
        self.timeout_minutes = timeout_minutes
        self.capsules: list[ContextCapsule] = []
        self.active_thread_id: Optional[str] = None
        self.centroid: Optional[list[float]] = None
        self.last_interaction: Optional[datetime] = None

    @property
    def is_expired(self) -> bool:
        """Check if working memory has expired due to inactivity."""
        if self.last_interaction is None:
            return True
        return (datetime.utcnow() - self.last_interaction) > timedelta(
            minutes=self.timeout_minutes
        )

    def add_capsule(self, capsule: ContextCapsule):
        """
        Add a capsule to working memory.
        If memory is full, evict the oldest capsule.
        Updates centroid and last interaction time.
        """
        # Check for context drift — if expired, reset
        if self.is_expired:
            self.reset()

        self.capsules.append(capsule)
        self.last_interaction = capsule.timestamp

        # Evict oldest if over capacity
        if len(self.capsules) > self.max_size:
            self.capsules = self.capsules[-self.max_size:]

        # Update running centroid
        self._update_centroid(capsule)

    def _update_centroid(self, capsule: ContextCapsule):
        """Update the cluster centroid as a running average of embeddings."""
        if capsule.embedding is None:
            return

        if self.centroid is None:
            self.centroid = list(capsule.embedding)
        else:
            # Exponential moving average for recency bias
            alpha = 0.3
            self.centroid = [
                alpha * e + (1 - alpha) * c
                for e, c in zip(capsule.embedding, self.centroid)
            ]

    def detect_context_drift(self, new_embedding: list[float], threshold: float = 0.75) -> bool:
        """
        Detect if a new capsule represents a significant context shift.
        Returns True if the new embedding is too different from the centroid.
        """
        if self.centroid is None:
            return False
        similarity = cosine_similarity(new_embedding, self.centroid)
        return similarity < threshold

    def get_recent_domains(self) -> list[str]:
        """Return unique domains from recent capsules."""
        return list({c.domain for c in self.capsules})

    def reset(self):
        """Clear working memory — simulates attention reset."""
        self.capsules = []
        self.active_thread_id = None
        self.centroid = None
        self.last_interaction = None

    def __len__(self):
        return len(self.capsules)
