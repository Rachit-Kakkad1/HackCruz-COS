"""
COS Backend Lite — FAISS Vector Store.

Stores embeddings in a FAISS IndexFlatIP (inner product on normalized
vectors = cosine similarity). Metadata is kept in a parallel list and
persisted alongside the index via pickle.
"""

import os
import pickle
import logging

import numpy as np
import faiss

logger = logging.getLogger(__name__)

# ─── Persistence paths ────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
INDEX_PATH = os.path.join(DATA_DIR, "faiss.index")
META_PATH = os.path.join(DATA_DIR, "metadata.pkl")

EMBEDDING_DIM = 384


class VectorStore:
    """
    FAISS-backed vector store with parallel metadata tracking.

    Uses IndexFlatIP so that searching normalized vectors gives cosine
    similarity scores directly.
    """

    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.index: faiss.IndexFlatIP = None
        self.metadata: list[dict] = []
        self._load()

    # ─── Persistence ──────────────────────────────────────────────────

    def _load(self):
        """Load existing index and metadata from disk, or create new."""
        if os.path.exists(INDEX_PATH) and os.path.exists(META_PATH):
            try:
                self.index = faiss.read_index(INDEX_PATH)
                with open(META_PATH, "rb") as f:
                    self.metadata = pickle.load(f)
                logger.info(
                    f"Loaded FAISS index with {self.index.ntotal} vectors."
                )
                return
            except Exception as e:
                logger.warning(f"Failed to load index, creating new: {e}")

        self.index = faiss.IndexFlatIP(EMBEDDING_DIM)
        self.metadata = []
        logger.info("Created new FAISS index.")

    def _save(self):
        """Persist index and metadata to disk."""
        faiss.write_index(self.index, INDEX_PATH)
        with open(META_PATH, "wb") as f:
            pickle.dump(self.metadata, f)

    # ─── Operations ───────────────────────────────────────────────────

    def add(self, embedding: list[float], meta: dict):
        """
        Add a single embedding + metadata entry.

        The embedding is L2-normalized before insertion so that inner
        product search produces cosine similarity scores.
        """
        vec = np.array([embedding], dtype=np.float32)
        faiss.normalize_L2(vec)
        self.index.add(vec)
        self.metadata.append(meta)
        self._save()

    def search(self, query_embedding: list[float], k: int = 3) -> list[dict]:
        """
        Search for the top-k most similar vectors.

        Returns a list of metadata dicts augmented with a 'score' key.
        """
        if self.index.ntotal == 0:
            return []

        vec = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(vec)

        actual_k = min(k, self.index.ntotal)
        scores, indices = self.index.search(vec, actual_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            entry = dict(self.metadata[idx])
            entry["score"] = float(score)
            results.append(entry)

        return results

    def get_all_embeddings(self) -> np.ndarray:
        """Return all stored vectors as an (N, dim) numpy array."""
        if self.index.ntotal == 0:
            return np.array([], dtype=np.float32).reshape(0, EMBEDDING_DIM)
        return faiss.rev_swig_ptr(
            self.index.get_xb(), self.index.ntotal * EMBEDDING_DIM
        ).reshape(self.index.ntotal, EMBEDDING_DIM).copy()

    @property
    def count(self) -> int:
        return self.index.ntotal


# ─── Module-level singleton ──────────────────────────────────────────────
vector_store = VectorStore()
