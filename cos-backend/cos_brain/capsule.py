"""
COS Brain — Context Capsule.

A capsule represents a single moment of browsing context at the sensory level.
This is a pure data class — no I/O, no framework coupling.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class ContextCapsule:
    """Atomic unit of browsing context — sensory memory layer."""

    url: str
    title: str
    domain: str
    user_id: str
    text_content: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    embedding: Optional[list[float]] = None
    cluster_id: Optional[str] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    @property
    def combined_text(self) -> str:
        """Combine title + text for embedding generation."""
        parts = [self.title]
        if self.text_content:
            parts.append(self.text_content[:500])  # Truncate for performance
        return " ".join(parts)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "url": self.url,
            "title": self.title,
            "domain": self.domain,
            "text_content": self.text_content,
            "timestamp": self.timestamp.isoformat(),
            "cluster_id": self.cluster_id,
        }
