"""
COS Brain — Temporal Cognitive Graph.

Builds and manages the graph of capsule relationships that powers
the Cognitive Map UI. Each node is a capsule, edges represent
temporal, semantic, cluster, or reasoning relationships.

Edge types:
    temporal         — consecutive browsing events (time-based)
    semantic         — cosine similarity between embeddings
    cluster          — shared cluster membership
    causes           — A triggers/leads to B
    answers          — B answers a question from A
    explains         — B explains/contextualizes A
    contradicts      — B contradicts the approach in A
    decision_result  — B is the outcome of research in A
    implements       — B implements a concept from A

Implements graph explosion protection (max 5 semantic edges per capsule).
"""

from dataclasses import dataclass, field
from typing import Optional

from cos_brain.capsule import ContextCapsule
from cos_brain.embedding_engine import cosine_similarity


# All recognized edge types for the cognitive graph
REASONING_EDGE_TYPES = frozenset({
    "causes", "answers", "explains",
    "contradicts", "decision_result", "implements",
})

ALL_EDGE_TYPES = frozenset({
    "temporal", "semantic", "cluster",
}) | REASONING_EDGE_TYPES


@dataclass
class GraphEdge:
    """Represents a relationship between two capsule nodes."""
    source_id: str
    target_id: str
    edge_type: str  # temporal | semantic | cluster | reasoning types
    weight: float = 1.0  # also serves as confidence for reasoning edges


class CognitiveGraph:
    """
    Manages the temporal cognitive graph.

    Edge creation rules:
    - temporal: always created between consecutive capsules (weight = 1.0)
    - semantic: created when cosine similarity > threshold (weight = similarity)
    - cluster: created when capsules share a cluster (weight = 1.0)
    - causal: created by LLM analysis (future extension)

    Graph explosion protection: max_semantic_edges per capsule.
    """

    def __init__(
        self,
        similarity_threshold: float = 0.75,
        max_semantic_edges: int = 5,
    ):
        self.similarity_threshold = similarity_threshold
        self.max_semantic_edges = max_semantic_edges

    def create_temporal_edge(
        self,
        prev_capsule_id: str,
        new_capsule_id: str,
    ) -> GraphEdge:
        """Create a temporal edge between consecutive capsules."""
        return GraphEdge(
            source_id=prev_capsule_id,
            target_id=new_capsule_id,
            edge_type="temporal",
            weight=1.0,
        )

    def find_semantic_edges(
        self,
        new_capsule: ContextCapsule,
        recent_capsules: list[ContextCapsule],
        existing_edge_count: int = 0,
    ) -> list[GraphEdge]:
        """
        Find semantic relationships between the new capsule and recent ones.
        Respects the max_semantic_edges limit to prevent graph explosion.
        """
        if new_capsule.embedding is None:
            return []

        remaining_slots = self.max_semantic_edges - existing_edge_count
        if remaining_slots <= 0:
            return []

        candidates = []
        for capsule in recent_capsules:
            if capsule.id == new_capsule.id or capsule.embedding is None:
                continue
            sim = cosine_similarity(new_capsule.embedding, capsule.embedding)
            if sim >= self.similarity_threshold:
                candidates.append((capsule.id, sim))

        # Sort by similarity descending, take only remaining_slots
        candidates.sort(key=lambda x: -x[1])
        edges = []
        for target_id, sim in candidates[:remaining_slots]:
            edges.append(GraphEdge(
                source_id=new_capsule.id,
                target_id=target_id,
                edge_type="semantic",
                weight=round(sim, 4),
            ))
        return edges

    def create_cluster_edge(
        self,
        capsule_id: str,
        cluster_member_id: str,
    ) -> GraphEdge:
        """Create a cluster edge between capsules in the same cluster."""
        return GraphEdge(
            source_id=capsule_id,
            target_id=cluster_member_id,
            edge_type="cluster",
            weight=1.0,
        )

    def format_for_ui(
        self,
        capsules: list[dict],
        edges: list[dict],
        clusters: list[dict] = None,
    ) -> dict:
        """
        Format graph data for the Cognitive Map React Flow UI.
        Returns the exact structure expected by CognitiveMap.jsx.
        """
        nodes = []
        for c in capsules:
            nodes.append({
                "id": str(c["id"]),
                "title": c["title"],
                "domain": c["domain"],
                "timestamp": c["timestamp"],
                "url": c.get("url", ""),
                "cluster": c.get("cluster_id"),
            })

        ui_edges = []
        for e in edges:
            edge_data = {
                "source": str(e["source_id"]),
                "target": str(e["target_id"]),
                "type": e["edge_type"],
            }
            # Include confidence for reasoning edges
            if e["edge_type"] in REASONING_EDGE_TYPES:
                edge_data["confidence"] = e.get("weight", 1.0)
            ui_edges.append(edge_data)

        result = {"nodes": nodes, "edges": ui_edges}
        if clusters:
            result["clusters"] = clusters

        return result
