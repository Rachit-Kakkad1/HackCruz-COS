"""
COS Backend — Database ORM Models.

All tables for the cognitive memory system: users, capsules, sessions,
clusters, threads, context_edges, knowledge_records, decisions, focus_rules.

All timestamps use timezone-aware UTC via datetime.now(timezone.utc).
"""

import uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Column, String, Text, DateTime, Float, Integer, Boolean,
    ForeignKey, JSON, Enum as SAEnum, Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.connection import Base
from app.config import get_settings

settings = get_settings()
EMBEDDING_DIM = settings.embedding_dimension


def _utc_now():
    """Timezone-aware UTC timestamp factory."""
    return datetime.now(timezone.utc)


# ─── Users ─────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=True)
    display_name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utc_now)

    capsules = relationship("Capsule", back_populates="user", cascade="all, delete-orphan")
    threads = relationship("Thread", back_populates="user", cascade="all, delete-orphan")


# ─── Context Capsules (Sensory Memory) ─────────────────────────────────────
class Capsule(Base):
    __tablename__ = "capsules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    url = Column(Text, nullable=False)
    title = Column(String(500), nullable=False)
    domain = Column(String(255), nullable=False)
    text_content = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    embedding = Column(Vector(EMBEDDING_DIM), nullable=True)  # pgvector
    cluster_id = Column(UUID(as_uuid=True), ForeignKey("clusters.id", ondelete="SET NULL"), nullable=True)
    is_processed = Column(Boolean, default=False)  # True once embedding + graph done

    user = relationship("User", back_populates="capsules")
    cluster = relationship("Cluster", back_populates="capsules")

    __table_args__ = (
        Index("ix_capsules_user_timestamp", "user_id", "timestamp"),
        Index("ix_capsules_domain", "domain"),
        Index("ix_capsules_is_processed", "is_processed"),
    )


# ─── Clusters (Sub-task Groupings) ─────────────────────────────────────────
class Cluster(Base):
    __tablename__ = "clusters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    label = Column(String(500), nullable=True)
    centroid = Column(Vector(EMBEDDING_DIM), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utc_now)
    updated_at = Column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)

    capsules = relationship("Capsule", back_populates="cluster")


# ─── Sessions (Time-bounded Browsing Windows) ──────────────────────────────
class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    domain_stats = Column(JSON, nullable=True)  # {"github.com": 1800, "youtube.com": 600}
    total_switches = Column(Integer, default=0)


# ─── Reasoning Threads ─────────────────────────────────────────────────────
class Thread(Base):
    __tablename__ = "threads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500), nullable=True)
    summary = Column(Text, nullable=True)
    status = Column(String(50), default="active")  # active | completed | archived
    created_at = Column(DateTime(timezone=True), default=_utc_now)
    updated_at = Column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)

    user = relationship("User", back_populates="threads")
    capsule_links = relationship("ThreadCapsule", back_populates="thread", cascade="all, delete-orphan")


class ThreadCapsule(Base):
    __tablename__ = "thread_capsules"

    thread_id = Column(UUID(as_uuid=True), ForeignKey("threads.id", ondelete="CASCADE"), primary_key=True)
    capsule_id = Column(UUID(as_uuid=True), ForeignKey("capsules.id", ondelete="CASCADE"), primary_key=True)
    added_at = Column(DateTime(timezone=True), default=_utc_now)

    thread = relationship("Thread", back_populates="capsule_links")


# ─── Cognitive Graph Edges ─────────────────────────────────────────────────
class ContextEdge(Base):
    __tablename__ = "context_edges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("capsules.id", ondelete="CASCADE"), nullable=False)
    target_id = Column(UUID(as_uuid=True), ForeignKey("capsules.id", ondelete="CASCADE"), nullable=False)
    edge_type = Column(String(50), nullable=False)  # temporal | semantic | cluster | reasoning types
    weight = Column(Float, default=1.0)
    created_at = Column(DateTime(timezone=True), default=_utc_now)

    __table_args__ = (
        Index("ix_edges_source", "source_id"),
        Index("ix_edges_target", "target_id"),
    )


# ─── Knowledge Records (Long-Term Memory) ──────────────────────────────────
class KnowledgeRecord(Base):
    __tablename__ = "knowledge_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    problem = Column(Text, nullable=True)
    sources = Column(JSON, nullable=True)  # ["url1", "url2"]
    conclusion = Column(Text, nullable=True)
    thread_id = Column(UUID(as_uuid=True), ForeignKey("threads.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utc_now)


# ─── Decision Memory ──────────────────────────────────────────────────────
class Decision(Base):
    __tablename__ = "decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500), nullable=False)
    reason = Column(Text, nullable=True)
    thread_id = Column(UUID(as_uuid=True), ForeignKey("threads.id", ondelete="SET NULL"), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=_utc_now)


# ─── Focus Rules ───────────────────────────────────────────────────────────
class FocusRule(Base):
    __tablename__ = "focus_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    pattern = Column(String(500), nullable=False)  # regex pattern for URL matching
    is_productive = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=_utc_now)
