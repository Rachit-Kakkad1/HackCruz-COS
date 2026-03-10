"""
COS Backend — Async Event Worker.

Continuously consumes capsule IDs from the Redis queue and runs the
full cognitive brain pipeline:

1. Load capsule from PostgreSQL
2. Generate embedding (sentence-transformers)
3. Store embedding in pgvector
4. Run clustering engine
5. Update reasoning threads
6. Create context graph edges
7. Run reasoning inference (detect logical relationships)
8. Detect decisions
9. Update working memory

Features:
- Batch processing (configurable, default 10)
- Retry with exponential backoff (max 3 attempts)
- Dead-letter queue for permanently failed events
- Graceful shutdown on SIGINT/SIGTERM
- Backpressure: adaptive batch sizing based on queue depth
- Idempotent: skips already-processed capsules

Run: python -m app.workers.event_worker
"""

import asyncio
import logging
import signal
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.config import get_settings
from app.database.connection import async_session, init_db
from app.database.models import Capsule
from app.database import repositories as repo
from app.services.event_queue import (
    dequeue_batch, send_to_dead_letter, get_queue_stats, close_redis,
)
from cos_brain.brain import CognitiveBrain
from cos_brain.capsule import ContextCapsule
from app.database.models import Capsule, ThreadCapsule

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-30s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger("cos.event_worker")
settings = get_settings()

# ─── Configuration ────────────────────────────────────────────────────────
MIN_BATCH = 5
MAX_BATCH = 20
MAX_RETRIES = 3
POLL_TIMEOUT = 2  # seconds to wait on empty queue

# ─── Global Brain Instance ────────────────────────────────────────────────
brain = CognitiveBrain(
    similarity_threshold=settings.similarity_threshold,
    max_gap_minutes=settings.time_gap_minutes,
    max_working_memory=settings.max_working_memory,
    max_semantic_edges=settings.max_semantic_edges,
)

# ─── Graceful Shutdown ────────────────────────────────────────────────────
_shutdown = False


def _handle_signal(sig, frame):
    global _shutdown
    logger.info(f"Received {signal.Signals(sig).name} — shutting down gracefully...")
    _shutdown = True


# ═══════════════════════════════════════════════════════════════════════════
# SINGLE CAPSULE PROCESSOR (idempotent)
# ═══════════════════════════════════════════════════════════════════════════

async def process_capsule(capsule_id: str, user_id: str):
    """
    Run the full cognitive pipeline for one capsule.
    Idempotent: skips if already processed.
    """
    async with async_session() as db:
        try:
            uid = uuid.UUID(capsule_id)
            user_uuid = uuid.UUID(user_id)

            # 1. Load capsule — skip if already processed
            result = await db.execute(select(Capsule).where(Capsule.id == uid))
            capsule_row = result.scalar_one_or_none()
            if not capsule_row or capsule_row.is_processed:
                return

            # 2. Build brain capsule + generate embedding
            brain_capsule = ContextCapsule(
                id=str(capsule_row.id),
                user_id=str(capsule_row.user_id),
                url=capsule_row.url,
                title=capsule_row.title,
                domain=capsule_row.domain,
                text_content=capsule_row.text_content,
                timestamp=capsule_row.timestamp,
            )
            brain_capsule = brain.generate_capsule_embedding(brain_capsule)

            # 3. Update DB row with embedding
            capsule_row.embedding = brain_capsule.embedding
            capsule_row.is_processed = True

            # 4. Update working memory
            brain.update_working_memory(brain_capsule)

            # 5. Clustering
            active_clusters = await repo.get_active_clusters(db, user_uuid)
            cluster_dicts = [
                {
                    "id": str(c.id),
                    "centroid": list(c.centroid) if c.centroid else None,
                    "last_timestamp": c.updated_at,
                }
                for c in active_clusters
            ]
            matched_cluster_id = brain.process_clustering(brain_capsule, cluster_dicts)

            if matched_cluster_id:
                capsule_row.cluster_id = uuid.UUID(matched_cluster_id)
            else:
                new_cluster = await repo.create_cluster(
                    db, user_uuid, centroid=brain_capsule.embedding
                )
                capsule_row.cluster_id = new_cluster.id

            # 6. Threading
            active_threads = await repo.get_active_threads(db, user_uuid)
            thread_dicts = [
                {
                    "id": str(t.id),
                    "updated_at": t.updated_at,
                    "centroid": None,
                }
                for t in active_threads
            ]
            thread_result = brain.process_threading(brain_capsule, thread_dicts)

            assigned_thread_id = None
            if thread_result["action"] == "extend" and thread_result["thread_id"]:
                assigned_thread_id = uuid.UUID(thread_result["thread_id"])
                await repo.link_capsule_to_thread(db, assigned_thread_id, capsule_row.id)
                for t in active_threads:
                    if str(t.id) == thread_result["thread_id"]:
                        t.updated_at = datetime.now(timezone.utc)
                        break
            else:
                new_thread = await repo.create_thread(db, user_uuid)
                assigned_thread_id = new_thread.id
                await repo.link_capsule_to_thread(db, new_thread.id, capsule_row.id)

            # Complete stale threads
            for tid in thread_result.get("should_complete", []):
                for t in active_threads:
                    if str(t.id) == tid:
                        t.status = "completed"
                        break

            # 7. Graph edges
            recent = await repo.get_recent_capsules(db, user_uuid, limit=10)
            recent_brain = [
                ContextCapsule(
                    id=str(c.id), user_id=str(c.user_id), url=c.url,
                    title=c.title, domain=c.domain, timestamp=c.timestamp,
                    embedding=list(c.embedding) if c.embedding else None,
                )
                for c in recent if str(c.id) != str(capsule_row.id)
            ]

            existing_count = await repo.count_edges_for_capsule(
                db, capsule_row.id, "semantic"
            )
            edges = brain.process_graph_edges(
                brain_capsule, recent_brain, existing_count
            )
            for edge in edges:
                await repo.create_edge(
                    db,
                    source_id=uuid.UUID(edge.source_id),
                    target_id=uuid.UUID(edge.target_id),
                    edge_type=edge.edge_type,
                    weight=edge.weight,
                )

            # 8. Decision detection
            recent_titles = [c.title for c in recent[:10]]
            decision = brain.detect_decision(
                recent_titles, str(user_uuid)
            )
            if decision:
                await repo.create_decision(
                    db, user_uuid, decision.title, decision.reason,
                )

            # 9. Reasoning inference (detect logical edges within thread)
            if assigned_thread_id:
                # Fetch all capsules in this thread
                thread_caps_result = await db.execute(
                    select(Capsule)
                    .join(ThreadCapsule, ThreadCapsule.capsule_id == Capsule.id)
                    .where(ThreadCapsule.thread_id == assigned_thread_id)
                    .order_by(Capsule.timestamp.asc())
                )
                thread_capsule_rows = list(thread_caps_result.scalars().all())

                thread_brain_capsules = [
                    ContextCapsule(
                        id=str(c.id), user_id=str(c.user_id), url=c.url,
                        title=c.title, domain=c.domain, timestamp=c.timestamp,
                        embedding=list(c.embedding) if c.embedding else None,
                    )
                    for c in thread_capsule_rows
                ]

                # Run reasoning inference
                reasoning_edges = brain.process_reasoning(
                    brain_capsule, thread_brain_capsules
                )
                for redge in reasoning_edges:
                    await repo.create_edge(
                        db,
                        source_id=uuid.UUID(redge.source_id),
                        target_id=uuid.UUID(redge.target_id),
                        edge_type=redge.edge_type,
                        weight=redge.weight,
                    )

            await db.commit()

        except Exception as e:
            await db.rollback()
            raise  # Let the retry handler deal with it


# ═══════════════════════════════════════════════════════════════════════════
# BATCH PROCESSOR WITH RETRY
# ═══════════════════════════════════════════════════════════════════════════

async def process_batch(events: list[dict]):
    """Process a batch of events with per-event retry and dead-lettering."""
    for event in events:
        capsule_id = event.get("capsule_id")
        user_id = event.get("user_id")

        if not capsule_id or not user_id:
            await send_to_dead_letter(event, "missing capsule_id or user_id")
            continue

        retries = 0
        while retries < MAX_RETRIES:
            try:
                await process_capsule(capsule_id, user_id)
                break
            except Exception as e:
                retries += 1
                if retries >= MAX_RETRIES:
                    await send_to_dead_letter(event, str(e)[:200])
                    logger.error(
                        f"Capsule {capsule_id} failed after {MAX_RETRIES} retries: {e}"
                    )
                else:
                    wait = 2 ** retries * 0.5  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(
                        f"Capsule {capsule_id} retry {retries}/{MAX_RETRIES} "
                        f"in {wait}s: {e}"
                    )
                    await asyncio.sleep(wait)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN WORKER LOOP
# ═══════════════════════════════════════════════════════════════════════════

async def worker_loop():
    """
    Main consumer loop with adaptive batch sizing.

    - When queue is deep (>50), uses larger batches (MAX_BATCH)
    - When queue is shallow, uses smaller batches (MIN_BATCH)
    - Logs throughput stats every 50 processed events
    """
    total_processed = 0
    batch_size = MIN_BATCH

    logger.info(
        f"🧠 Event worker started — batch: {MIN_BATCH}-{MAX_BATCH}, "
        f"retries: {MAX_RETRIES}, poll: {POLL_TIMEOUT}s"
    )

    while not _shutdown:
        try:
            # Adaptive batch sizing based on backpressure
            stats = await get_queue_stats()
            pending = stats["pending"]

            if pending > 50:
                batch_size = MAX_BATCH
            elif pending > 10:
                batch_size = 10
            else:
                batch_size = MIN_BATCH

            # Dequeue a batch
            events = await dequeue_batch(
                batch_size=batch_size, timeout=POLL_TIMEOUT
            )

            if not events:
                continue

            # Process the batch
            await process_batch(events)
            total_processed += len(events)

            # Periodic stats logging
            if total_processed % 50 == 0 and total_processed > 0:
                stats = await get_queue_stats()
                logger.info(
                    f"📊 Processed: {total_processed} | "
                    f"Pending: {stats['pending']} | "
                    f"Dead: {stats['dead_letter']} | "
                    f"Batch: {batch_size}"
                )

        except Exception as e:
            logger.error(f"Worker loop error: {e}", exc_info=True)
            await asyncio.sleep(1)  # Prevent tight error loops


async def main():
    """Entry point for the event worker."""
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    # Initialize database
    await init_db()
    logger.info("✓ Database initialized")

    try:
        await worker_loop()
    finally:
        await close_redis()
        logger.info("🛑 Event worker stopped")


if __name__ == "__main__":
    asyncio.run(main())
