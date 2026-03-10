"""
COS Backend — Application Settings.

All configuration is read from environment variables via pydantic-settings.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ─── Database ──────────────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://cos_user:cos_secret@localhost:5432/cos_db"

    # ─── Redis ─────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ─── AI / Embeddings ───────────────────────────────────────────────────
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    # ─── LLM ───────────────────────────────────────────────────────────────
    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"

    # ─── CORS ──────────────────────────────────────────────────────────────
    cors_origins: str = "http://localhost:5173,chrome-extension://*"

    # ─── Cognitive Thresholds ──────────────────────────────────────────────
    similarity_threshold: float = 0.75
    time_gap_minutes: int = 20
    max_working_memory: int = 20
    max_semantic_edges: int = 5  # Graph explosion protection
    data_retention_days: int = 30

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
