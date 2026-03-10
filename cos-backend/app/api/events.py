"""
COS Backend — Event Ingestion API (v2 — Async Pipeline).

POST /api/v1/events/track — Ultra-fast ingestion endpoint.

This endpoint ONLY:
1. Validates the incoming event
2. Inserts a raw capsule record in PostgreSQL (is_processed=false)
3. Pushes the capsule ID into a Redis event queue
4. Returns immediately

Target latency: <10ms.

All heavy AI processing (embeddings, clustering, threading, graph)
is handled by the separate event_worker.py consumer.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.database import repositories as repo
from app.services.event_queue import enqueue_event

router = APIRouter(prefix="/api/v1/events", tags=["Events"])


# ─── Request Model ────────────────────────────────────────────────────────
class TrackEventRequest(BaseModel):
    userId: str
    url: str
    title: str
    textSnippet: Optional[str] = None
    timestamp: Optional[str] = None


# ─── Endpoint ─────────────────────────────────────────────────────────────
@router.post("/track")
async def track_event(
    request: TrackEventRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Ultra-fast event ingestion (<10ms).

    Fast path only:
    1. Insert raw capsule → PostgreSQL
    2. Push capsule_id → Redis queue
    3. Return 200

    The event_worker.py consumer handles all AI processing.
    """
    # Parse timestamp
    ts = datetime.now(timezone.utc)
    if request.timestamp:
        try:
            ts = datetime.fromisoformat(request.timestamp.replace("Z", "+00:00"))
        except ValueError:
            pass

    # Extract domain from URL
    domain = urlparse(request.url).netloc.replace("www.", "")

    # Ensure user exists
    user = await repo.get_or_create_user(db, request.userId)

    # Insert raw capsule (no embedding, is_processed=false)
    capsule = await repo.create_capsule(
        db,
        user_id=user.id,
        url=request.url,
        title=request.title,
        domain=domain,
        text_content=request.textSnippet,
        timestamp=ts,
    )

    # Push to Redis queue for async processing
    queue_depth = await enqueue_event(str(capsule.id), str(user.id))

    return {
        "status": "ok",
        "capsule_id": str(capsule.id),
        "queue_depth": queue_depth,
    }
