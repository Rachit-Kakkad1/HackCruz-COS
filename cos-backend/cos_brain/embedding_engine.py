"""
COS Brain — Embedding Engine.

Singleton wrapper around sentence-transformers for generating vector embeddings.
Includes sha256-based caching to avoid recomputation (per user feedback).
"""

import hashlib
import logging
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# ─── Global Singleton ─────────────────────────────────────────────────────
_model = None
_cache: dict[str, list[float]] = {}


def _get_model():
    """Lazy-load the sentence-transformers model once."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("✓ Loaded embedding model: all-MiniLM-L6-v2")
        except Exception as e:
            logger.warning(f"⚠ Failed to load embedding model: {e}. Using fallback.")
            _model = "fallback"
    return _model


def _cache_key(text: str) -> str:
    """Generate a sha256 hash key for embedding cache."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def generate_embedding(text: str) -> list[float]:
    """
    Generate a 384-dim embedding vector for the given text.

    Uses sha256 caching to avoid repeated computation of the same text.
    Falls back to a random normalized vector if the model isn't available.
    """
    if not text or not text.strip():
        return [0.0] * 384

    # Check cache first
    key = _cache_key(text)
    if key in _cache:
        return _cache[key]

    model = _get_model()

    if model == "fallback":
        # Deterministic fallback based on text hash for dev environments
        rng = np.random.RandomState(int(key[:8], 16) % (2**31))
        vec = rng.randn(384).astype(float)
        vec = (vec / np.linalg.norm(vec)).tolist()
    else:
        vec = model.encode(text, normalize_embeddings=True).tolist()

    # Store in cache
    _cache[key] = vec
    return vec


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for a batch of texts.
    Checks cache for each; only computes uncached entries in a single pass.
    """
    results = [None] * len(texts)
    uncached_indices = []
    uncached_texts = []

    for i, text in enumerate(texts):
        if not text or not text.strip():
            results[i] = [0.0] * 384
            continue
        key = _cache_key(text)
        if key in _cache:
            results[i] = _cache[key]
        else:
            uncached_indices.append(i)
            uncached_texts.append(text)

    if uncached_texts:
        model = _get_model()
        if model == "fallback":
            for idx, text in zip(uncached_indices, uncached_texts):
                results[idx] = generate_embedding(text)
        else:
            batch_vecs = model.encode(uncached_texts, normalize_embeddings=True)
            for idx, text, vec in zip(uncached_indices, uncached_texts, batch_vecs):
                vec_list = vec.tolist()
                _cache[_cache_key(text)] = vec_list
                results[idx] = vec_list

    return results


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a_arr = np.array(a)
    b_arr = np.array(b)
    dot = np.dot(a_arr, b_arr)
    norm = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
    return float(dot / norm) if norm > 0 else 0.0
