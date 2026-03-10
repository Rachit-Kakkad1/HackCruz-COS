"""
COS Backend — AI Summarization Module.

Uses OpenAI GPT-4o-mini for thread title generation, summary creation,
and decision detection. Falls back to extractive methods when no API key.
"""

import logging
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ─── Lazy OpenAI Client ───────────────────────────────────────────────────
_client = None


def _get_client():
    global _client
    if _client is None and settings.openai_api_key:
        try:
            from openai import OpenAI
            _client = OpenAI(api_key=settings.openai_api_key)
            logger.info("✓ OpenAI client initialized")
        except Exception as e:
            logger.warning(f"⚠ Failed to initialize OpenAI: {e}")
    return _client


async def generate_thread_title(capsule_titles: list[str]) -> Optional[str]:
    """Generate a concise thread title using GPT-4o-mini."""
    client = _get_client()
    if not client:
        return None  # Caller should use fallback

    try:
        titles_text = "\n".join(f"- {t}" for t in capsule_titles[:15])
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a cognitive analyst. Given a list of web page titles from a browsing session, generate a short, descriptive title (max 10 words) that captures the reasoning thread. Respond with ONLY the title, no quotes or punctuation.",
                },
                {
                    "role": "user",
                    "content": f"Page titles:\n{titles_text}",
                },
            ],
            max_tokens=30,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"LLM title generation failed: {e}")
        return None


async def generate_thread_summary(
    thread_title: str,
    capsule_titles: list[str],
    capsule_urls: list[str],
) -> Optional[str]:
    """Generate a summary of a completed reasoning thread."""
    client = _get_client()
    if not client:
        return None

    try:
        context = "\n".join(
            f"- [{t}]({u})" for t, u in zip(capsule_titles[:15], capsule_urls[:15])
        )
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a cognitive analyst. Generate a 2-3 sentence summary of a completed research/browsing thread. Include: the problem being investigated, key resources used, and any conclusions reached.",
                },
                {
                    "role": "user",
                    "content": f"Thread: {thread_title}\n\nPages visited:\n{context}",
                },
            ],
            max_tokens=150,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"LLM summary generation failed: {e}")
        return None


async def detect_decision_llm(
    capsule_titles: list[str],
) -> Optional[dict]:
    """Use LLM to detect if a decision was made during a browsing session."""
    client = _get_client()
    if not client:
        return None

    try:
        titles_text = "\n".join(f"- {t}" for t in capsule_titles[:15])
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": "Analyze the browsing session below. If the user appears to have made a technology or tool decision (comparing options and then focusing on one), respond in this exact format:\nDECISION: <decision title>\nREASON: <brief reason>\n\nIf no clear decision was made, respond with just: NONE",
                },
                {
                    "role": "user",
                    "content": f"Pages visited:\n{titles_text}",
                },
            ],
            max_tokens=80,
            temperature=0.2,
        )
        text = response.choices[0].message.content.strip()
        if text.startswith("NONE"):
            return None
        lines = text.split("\n")
        title = lines[0].replace("DECISION:", "").strip() if lines else ""
        reason = lines[1].replace("REASON:", "").strip() if len(lines) > 1 else ""
        return {"title": title, "reason": reason}
    except Exception as e:
        logger.warning(f"LLM decision detection failed: {e}")
        return None


async def generate_reflection(
    thread_titles: list[str],
    domain_stats: dict,
) -> Optional[str]:
    """
    Reflection Engine (per user feedback): Analyze daily patterns
    to generate self-improving insights.
    """
    client = _get_client()
    if not client:
        return None

    try:
        threads_text = "\n".join(f"- {t}" for t in thread_titles[:10])
        domains_text = "\n".join(
            f"- {d}: {m // 60}min" for d, m in sorted(
                domain_stats.items(), key=lambda x: -x[1]
            )[:10]
        )
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a personal productivity coach. Analyze the user's daily browsing patterns and generate ONE actionable insight about their problem-solving approach. Be specific and constructive. Max 2 sentences.",
                },
                {
                    "role": "user",
                    "content": f"Research threads today:\n{threads_text}\n\nTime by domain:\n{domains_text}",
                },
            ],
            max_tokens=100,
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"LLM reflection failed: {e}")
        return None
