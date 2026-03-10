"""
COS Backend — Redis Event Queue Service.

Provides a clean abstraction over Redis for the event ingestion pipeline.
Uses Redis Lists (LPUSH/BRPOP) for simplicity and reliability.

Queue: cos:events       — main processing queue
Queue: cos:events:dead  — dead-letter queue for failed events
"""

import json
import logging
from typing import Optional

import redis.asyncio as aioredis

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ─── Queue Names ──────────────────────────────────────────────────────────
QUEUE_KEY = "cos:events"
DEAD_LETTER_KEY = "cos:events:dead"
PROCESSING_KEY = "cos:events:processing"

# ─── Singleton Connection Pool ────────────────────────────────────────────
_pool: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """Get or create the async Redis connection pool."""
    global _pool
    if _pool is None:
        _pool = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            max_connections=20,
        )
    return _pool


async def close_redis():
    """Shutdown the Redis connection pool gracefully."""
    global _pool
    if _pool:
        await _pool.aclose()
        _pool = None


# ═══════════════════════════════════════════════════════════════════════════
# PRODUCER — called by the FastAPI ingestion endpoint
# ═══════════════════════════════════════════════════════════════════════════

async def enqueue_event(capsule_id: str, user_id: str) -> int:
    """
    Push a capsule processing job into the Redis queue.
    Returns the new queue length.
    """
    r = await get_redis()
    payload = json.dumps({"capsule_id": capsule_id, "user_id": user_id})
    length = await r.lpush(QUEUE_KEY, payload)
    return length


# ═══════════════════════════════════════════════════════════════════════════
# CONSUMER — called by the event worker
# ═══════════════════════════════════════════════════════════════════════════

async def dequeue_event(timeout: int = 5) -> Optional[dict]:
    """
    Blocking pop a single event from the queue.
    Returns None if no event arrives within `timeout` seconds.
    """
    r = await get_redis()
    result = await r.brpop(QUEUE_KEY, timeout=timeout)
    if result is None:
        return None
    _, payload = result
    return json.loads(payload)


async def dequeue_batch(batch_size: int = 10, timeout: int = 2) -> list[dict]:
    """
    Pop up to `batch_size` events from the queue using a pipeline.
    First event blocks for `timeout` seconds; remaining are non-blocking.
    """
    r = await get_redis()

    # Wait for at least one event
    first = await r.brpop(QUEUE_KEY, timeout=timeout)
    if first is None:
        return []

    _, payload = first
    events = [json.loads(payload)]

    # Grab more without blocking (up to batch_size - 1)
    pipe = r.pipeline()
    for _ in range(batch_size - 1):
        pipe.rpop(QUEUE_KEY)
    results = await pipe.execute()

    for raw in results:
        if raw is not None:
            events.append(json.loads(raw))

    return events


async def send_to_dead_letter(event: dict, error: str):
    """Move a failed event to the dead-letter queue with error metadata."""
    r = await get_redis()
    payload = json.dumps({**event, "error": error})
    await r.lpush(DEAD_LETTER_KEY, payload)
    logger.warning(f"Event {event.get('capsule_id')} → dead-letter: {error}")


# ═══════════════════════════════════════════════════════════════════════════
# MONITORING — for health checks and debugging
# ═══════════════════════════════════════════════════════════════════════════

async def get_queue_stats() -> dict:
    """Return queue depths for monitoring."""
    r = await get_redis()
    return {
        "pending": await r.llen(QUEUE_KEY),
        "dead_letter": await r.llen(DEAD_LETTER_KEY),
    }
