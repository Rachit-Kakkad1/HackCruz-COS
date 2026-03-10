"""
COS Backend — Background Workers.

Scheduled tasks that run independently of the API:
1. Memory consolidation (daily) — convert threads to knowledge records
2. Data retention (daily) — purge capsules older than 30 days
3. Embedding backfill — process unprocessed capsules (MICRO-BATCH)
4. Thread title generation — auto-title unnamed threads
5. Reflection engine (daily) — generate self-improvement insights

Run this module directly: python -m app.workers.background_tasks
"""

import asyncio
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings
from app.database.connection import async_session, init_db
from app.database import repositories as repo
from app.database.models import Thread, Capsule, ThreadCapsule
from app.services import knowledge_service
from cos_brain.embedding_engine import generate_embeddings_batch
from cos_brain.thread_engine import ThreadEngine

from sqlalchemy import select, func

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-30s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


# ═══════════════════════════════════════════════════════════════════════════
# TASK 1: Memory Consolidation (runs at 3 AM daily)
# ═══════════════════════════════════════════════════════════════════════════
async def consolidate_memories():
    """
    Review completed reasoning threads and convert them to
    long-term knowledge records. Simulates human sleep consolidation.
    """
    logger.info("🧠 Starting daily memory consolidation...")

    async with async_session() as db:
        try:
            result = await db.execute(
                select(Thread).where(Thread.status == "completed")
            )
            threads = list(result.scalars().all())
            count = 0

            for thread in threads:
                try:
                    await knowledge_service.consolidate_thread(db, thread)
                    count += 1
                except Exception as e:
                    logger.warning(f"Failed to consolidate thread {thread.id}: {e}")

            await db.commit()
            logger.info(f"✓ Consolidated {count}/{len(threads)} threads into knowledge records")

        except Exception as e:
            await db.rollback()
            logger.error(f"Consolidation failed: {e}", exc_info=True)


# ═══════════════════════════════════════════════════════════════════════════
# TASK 2: Data Retention (runs at 4 AM daily)
# ═══════════════════════════════════════════════════════════════════════════
async def enforce_data_retention():
    """
    Delete raw capsules older than the retention period (default: 30 days).
    Only raw event data is deleted; knowledge records are preserved.
    """
    logger.info("🗑️  Enforcing data retention policy...")

    async with async_session() as db:
        try:
            deleted = await repo.purge_old_capsules(db, settings.data_retention_days)
            await db.commit()
            logger.info(f"✓ Purged {deleted} capsules older than {settings.data_retention_days} days")
        except Exception as e:
            await db.rollback()
            logger.error(f"Retention enforcement failed: {e}", exc_info=True)


# ═══════════════════════════════════════════════════════════════════════════
# TASK 3: Micro-Batch Embedding Backfill (runs every 5 minutes)
# ═══════════════════════════════════════════════════════════════════════════
async def backfill_embeddings():
    """
    Process any capsules without embeddings using MICRO-BATCH encoding.
    3-5× faster than one-by-one processing.
    """
    async with async_session() as db:
        try:
            capsules = await repo.get_unprocessed_capsules(db, limit=32)
            if not capsules:
                return

            logger.info(f"🔄 Micro-batch embedding backfill for {len(capsules)} capsules...")

            # Collect texts for batch encoding
            texts = [
                f"{c.title} {c.text_content or ''}"
                for c in capsules
            ]

            # Single model.encode() call for entire batch — 3-5× faster
            embeddings = generate_embeddings_batch(texts)

            # Apply embeddings to capsules
            for capsule, embedding in zip(capsules, embeddings):
                capsule.embedding = embedding
                capsule.is_processed = True

            await db.commit()
            logger.info(f"✓ Batch-embedded {len(capsules)} capsules")

        except Exception as e:
            await db.rollback()
            logger.error(f"Embedding backfill failed: {e}", exc_info=True)


# ═══════════════════════════════════════════════════════════════════════════
# TASK 4: Thread Title Generation (runs every 10 minutes)
# ═══════════════════════════════════════════════════════════════════════════
thread_engine = ThreadEngine()


async def generate_thread_titles():
    """
    Auto-generate titles for unnamed threads using:
    1. LLM summarization (if OpenAI key available)
    2. TF-IDF keyword extraction (fallback)

    Example output: "Debugging AWS Cognito Token Verification Bug"
    """
    async with async_session() as db:
        try:
            # Find threads without titles that have capsules
            result = await db.execute(
                select(Thread)
                .where(Thread.title.is_(None))
                .where(Thread.status.in_(["active", "completed"]))
                .limit(10)
            )
            untitled = list(result.scalars().all())
            if not untitled:
                return

            logger.info(f"📝 Generating titles for {len(untitled)} threads...")
            titled_count = 0

            for thread in untitled:
                # Fetch capsule titles for this thread
                caps_result = await db.execute(
                    select(Capsule.title)
                    .join(ThreadCapsule, ThreadCapsule.capsule_id == Capsule.id)
                    .where(ThreadCapsule.thread_id == thread.id)
                    .order_by(Capsule.timestamp.asc())
                )
                capsule_titles = [row[0] for row in caps_result.all()]

                if len(capsule_titles) < 2:
                    continue

                # Try LLM first, fall back to TF-IDF keywords
                title = None
                try:
                    from app.ai import generate_thread_title
                    title = await generate_thread_title(capsule_titles)
                except Exception:
                    pass

                if not title:
                    # TF-IDF fallback
                    title = thread_engine.generate_thread_title_from_keywords(
                        capsule_titles
                    )

                if title:
                    thread.title = title
                    titled_count += 1

            await db.commit()
            logger.info(f"✓ Generated {titled_count} thread titles")

        except Exception as e:
            await db.rollback()
            logger.error(f"Thread title generation failed: {e}", exc_info=True)


# ═══════════════════════════════════════════════════════════════════════════
# TASK 5: Reflection Engine (runs at 11 PM daily)
# ═══════════════════════════════════════════════════════════════════════════
async def generate_daily_reflection():
    """
    Analyze daily patterns and generate self-improvement insights.
    (Per user feedback: "This turns COS into a self-improving cognitive assistant")
    """
    from app.ai import generate_reflection

    logger.info("🪞 Generating daily reflection...")

    async with async_session() as db:
        try:
            result = await db.execute(
                select(Thread).where(Thread.status.in_(["completed", "archived"]))
            )
            threads = list(result.scalars().all())
            if not threads:
                return

            thread_titles = [t.title or "Untitled" for t in threads]

            # Get domain stats from capsules
            from collections import defaultdict
            capsules = await repo.get_capsules_today(db, threads[0].user_id)
            domain_stats = defaultdict(int)
            prev_ts = None
            for c in capsules:
                if prev_ts:
                    delta = (c.timestamp - prev_ts).total_seconds()
                    if delta < 1800:
                        domain_stats[c.domain] += int(delta)
                prev_ts = c.timestamp

            reflection = await generate_reflection(thread_titles, dict(domain_stats))
            if reflection:
                logger.info(f"🪞 Daily Reflection: {reflection}")

        except Exception as e:
            logger.error(f"Reflection generation failed: {e}", exc_info=True)


# ═══════════════════════════════════════════════════════════════════════════
# SCHEDULER SETUP
# ═══════════════════════════════════════════════════════════════════════════
async def main():
    """Start the background worker with scheduled tasks."""
    await init_db()
    logger.info("🚀 COS Background Worker starting...")

    scheduler = AsyncIOScheduler()

    # Daily memory consolidation at 3 AM
    scheduler.add_job(consolidate_memories, "cron", hour=3, id="consolidation")

    # Daily data retention at 4 AM
    scheduler.add_job(enforce_data_retention, "cron", hour=4, id="retention")

    # Micro-batch embedding backfill every 5 minutes
    scheduler.add_job(backfill_embeddings, "interval", minutes=5, id="backfill")

    # Thread title generation every 10 minutes
    scheduler.add_job(generate_thread_titles, "interval", minutes=10, id="thread_titles")

    # Daily reflection at 11 PM
    scheduler.add_job(generate_daily_reflection, "cron", hour=23, id="reflection")

    scheduler.start()
    logger.info("✓ Background scheduler started with 5 tasks")

    # Keep the worker alive
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("🛑 Background worker stopped")


if __name__ == "__main__":
    asyncio.run(main())
