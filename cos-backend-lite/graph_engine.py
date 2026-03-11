"""
COS Backend Lite — Graph Engine.

When a new embedding arrives, compares it against all existing embeddings.
If cosine similarity exceeds the threshold (0.75), stores a relationship
edge in the SQLite database.
"""

import logging
import numpy as np

from embedder import cosine_similarity
from database import insert_edge
from vector_store import vector_store

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.75


def process_new_context(new_context_id: int, new_embedding: list[float]):
    """
    Compare the new embedding against all stored embeddings.

    For each pair with cosine similarity > SIMILARITY_THRESHOLD,
    insert a relationship edge into the context_edges table.

    Args:
        new_context_id: Database ID of the newly inserted context.
        new_embedding: 384-dim embedding vector for the new context.
    """
    total = vector_store.count
    if total <= 1:
        # No existing vectors to compare against (just the one we added)
        return

    all_embeddings = vector_store.get_all_embeddings()
    new_vec = np.array(new_embedding, dtype=np.float32)

    edges_created = 0

    # Compare against all existing vectors except the last one (which is the new one)
    for idx in range(total - 1):
        existing_vec = all_embeddings[idx].tolist()
        sim = cosine_similarity(new_embedding, existing_vec)

        if sim >= SIMILARITY_THRESHOLD:
            # target_id is idx + 1 because SQLite IDs are 1-indexed
            target_id = idx + 1
            insert_edge(new_context_id, target_id, round(sim, 4))
            edges_created += 1

    if edges_created > 0:
        logger.info(
            f"Graph: Created {edges_created} edge(s) for context {new_context_id}"
        )
