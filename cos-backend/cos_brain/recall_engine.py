"""
COS Brain — Semantic Recall Engine.

Allows users to search their browsing memory by meaning rather than keywords.
Pipeline: query → embedding → pgvector nearest-neighbor → ranked results.
"""

from cos_brain.embedding_engine import generate_embedding, cosine_similarity


class RecallEngine:
    """
    Semantic search across the user's capsule memory.

    Unlike keyword search, this finds results based on meaning:
    "That article about fixing React state" → finds the exact page
    even if the title says "useState not updating — StackOverflow"
    """

    def prepare_query(self, query_text: str) -> list[float]:
        """Convert a search query to an embedding vector."""
        return generate_embedding(query_text)

    def rank_results(
        self,
        query_embedding: list[float],
        capsules: list[dict],
    ) -> list[dict]:
        """
        Re-rank capsule results by semantic similarity to the query.
        Each capsule dict should have an 'embedding' field.
        """
        scored = []
        for capsule in capsules:
            if capsule.get("embedding") is None:
                continue
            sim = cosine_similarity(query_embedding, capsule["embedding"])
            scored.append({**capsule, "relevance_score": round(sim, 4)})

        scored.sort(key=lambda x: -x["relevance_score"])
        return scored

    def format_recall_results(
        self,
        capsules: list[dict],
        threads: list[dict] = None,
    ) -> dict:
        """Format search results for the API response."""
        return {
            "capsules": [
                {
                    "id": str(c.get("id")),
                    "title": c.get("title"),
                    "domain": c.get("domain"),
                    "url": c.get("url"),
                    "timestamp": c.get("timestamp"),
                    "relevance_score": c.get("relevance_score", 0),
                }
                for c in capsules
            ],
            "threads": threads or [],
        }
