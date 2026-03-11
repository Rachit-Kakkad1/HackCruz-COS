"""
COS Backend Lite — Embedder Module.

Singleton wrapper around sentence-transformers for generating
384-dimensional semantic embedding vectors.

Model: all-MiniLM-L6-v2 (local, no external API calls).
"""

import logging
import numpy as np

logger = logging.getLogger(__name__)

# ─── Singleton ────────────────────────────────────────────────────────────
_model = None


def _get_model():
    """Lazy-load the sentence-transformers model once."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading embedding model: all-MiniLM-L6-v2 ...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Embedding model loaded successfully.")
    return _model


def generate_embedding(text: str) -> list[float]:
    """
    Generate a normalized 384-dim embedding vector for the given text.

    Args:
        text: Input text string (title + page content combined).

    Returns:
        List of 384 floats (unit-normalized).
    """
    if not text or not text.strip():
        return [0.0] * 384

    model = _get_model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a_arr = np.array(a, dtype=np.float32)
    b_arr = np.array(b, dtype=np.float32)
    dot = np.dot(a_arr, b_arr)
    norm = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
    if norm == 0:
        return 0.0
    return float(dot / norm)
