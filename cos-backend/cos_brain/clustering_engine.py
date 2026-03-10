"""
COS Brain — Clustering Engine.

Groups context capsules into semantic clusters using cosine similarity
and time proximity. Clusters feed into reasoning threads.
"""

from datetime import timedelta
from typing import Optional

import numpy as np

from cos_brain.capsule import ContextCapsule
from cos_brain.embedding_engine import cosine_similarity


class ClusteringEngine:
    """
    Online clustering engine for context capsules.

    Rules:
    - Capsules join an existing cluster if cosine similarity > threshold
      AND time gap < max_gap_minutes.
    - Otherwise, a new cluster is created.
    """

    def __init__(
        self,
        similarity_threshold: float = 0.75,
        max_gap_minutes: int = 20,
    ):
        self.similarity_threshold = similarity_threshold
        self.max_gap_minutes = max_gap_minutes

    def find_matching_cluster(
        self,
        capsule: ContextCapsule,
        active_clusters: list[dict],
    ) -> Optional[str]:
        """
        Determine which existing cluster a capsule belongs to.

        Each cluster dict has:
          - id: str
          - centroid: list[float]
          - last_timestamp: datetime

        Returns the cluster ID if a match is found, or None.
        """
        if capsule.embedding is None:
            return None

        best_id = None
        best_score = 0.0

        for cluster in active_clusters:
            if cluster.get("centroid") is None:
                continue

            # Time proximity check
            time_diff = abs(
                (capsule.timestamp - cluster["last_timestamp"]).total_seconds()
            )
            if time_diff > self.max_gap_minutes * 60:
                continue

            # Semantic similarity check
            sim = cosine_similarity(capsule.embedding, cluster["centroid"])
            if sim >= self.similarity_threshold and sim > best_score:
                best_score = sim
                best_id = cluster["id"]

        return best_id

    def compute_centroid(self, embeddings: list[list[float]]) -> list[float]:
        """Compute the average centroid of a set of embedding vectors."""
        if not embeddings:
            return [0.0] * 384
        arr = np.array(embeddings)
        centroid = arr.mean(axis=0)
        # Normalize
        norm = np.linalg.norm(centroid)
        if norm > 0:
            centroid = centroid / norm
        return centroid.tolist()

    def should_merge_clusters(
        self,
        centroid_a: list[float],
        centroid_b: list[float],
    ) -> bool:
        """Check if two clusters are similar enough to merge."""
        sim = cosine_similarity(centroid_a, centroid_b)
        return sim >= self.similarity_threshold
