"""
COS Brain — Orchestrator.

The central coordinator that wires all cognitive modules together.
This is the single entry point for the API layer to interact
with the brain. It processes events through the full pipeline:

Event → Capsule → Embedding → Cluster → Thread → Reasoning → Graph
"""

import logging
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from cos_brain.capsule import ContextCapsule
from cos_brain.embedding_engine import generate_embedding, cosine_similarity
from cos_brain.working_memory import WorkingMemory
from cos_brain.clustering_engine import ClusteringEngine
from cos_brain.thread_engine import ThreadEngine
from cos_brain.context_graph import CognitiveGraph, GraphEdge
from cos_brain.knowledge_engine import KnowledgeEngine
from cos_brain.decision_memory import DecisionMemory
from cos_brain.recall_engine import RecallEngine
from cos_brain.reasoning_engine import ReasoningEngine, ReasoningEdge

logger = logging.getLogger(__name__)


class CognitiveBrain:
    """
    The central cognitive engine for Context Scope.

    All brain logic is framework-independent — this module has no
    knowledge of FastAPI, SQLAlchemy, or any web framework.
    It operates on pure data structures and returns results for
    the service layer to persist.
    """

    def __init__(
        self,
        similarity_threshold: float = 0.75,
        max_gap_minutes: int = 20,
        max_working_memory: int = 20,
        max_semantic_edges: int = 5,
    ):
        self.working_memories: dict[str, WorkingMemory] = {}  # Per-user
        self.clustering = ClusteringEngine(similarity_threshold, max_gap_minutes)
        self.threading = ThreadEngine(similarity_threshold, max_gap_minutes)
        self.graph = CognitiveGraph(similarity_threshold, max_semantic_edges)
        self.knowledge = KnowledgeEngine()
        self.decisions = DecisionMemory()
        self.recall = RecallEngine()
        self.reasoning = ReasoningEngine()

        self._max_working_memory = max_working_memory
        self._max_gap_minutes = max_gap_minutes

    # ─── Working Memory Access ─────────────────────────────────────────
    def _get_memory(self, user_id: str) -> WorkingMemory:
        """Get or create working memory for a user."""
        if user_id not in self.working_memories:
            self.working_memories[user_id] = WorkingMemory(
                max_size=self._max_working_memory,
                timeout_minutes=self._max_gap_minutes,
            )
        return self.working_memories[user_id]

    # ─── Event Ingestion Pipeline ──────────────────────────────────────
    def create_capsule(
        self,
        user_id: str,
        url: str,
        title: str,
        text_content: str = None,
        timestamp: datetime = None,
    ) -> ContextCapsule:
        """Step 1: Create a context capsule from a raw browsing event."""
        domain = urlparse(url).netloc.replace("www.", "")
        capsule = ContextCapsule(
            user_id=user_id,
            url=url,
            title=title,
            domain=domain,
            text_content=text_content,
            timestamp=timestamp or datetime.utcnow(),
        )
        return capsule

    def generate_capsule_embedding(self, capsule: ContextCapsule) -> ContextCapsule:
        """Step 2: Generate embedding for a capsule."""
        capsule.embedding = generate_embedding(capsule.combined_text)
        return capsule

    def process_clustering(
        self,
        capsule: ContextCapsule,
        active_clusters: list[dict],
    ) -> Optional[str]:
        """Step 3: Find or create a cluster for the capsule."""
        return self.clustering.find_matching_cluster(capsule, active_clusters)

    def process_threading(
        self,
        capsule: ContextCapsule,
        active_threads: list[dict],
    ) -> dict:
        """
        Step 4: Determine which thread this capsule belongs to.

        Returns:
            {
                "action": "extend" | "create",
                "thread_id": str | None,
                "should_complete": list[str],  # thread IDs to complete
            }
        """
        memory = self._get_memory(capsule.user_id)
        result = {"action": "create", "thread_id": None, "should_complete": []}

        # Check which threads should be completed due to inactivity
        for thread in active_threads:
            if self.threading.should_complete_thread(thread["updated_at"]):
                result["should_complete"].append(thread["id"])

        # Find a matching active thread
        for thread in active_threads:
            if thread["id"] in result["should_complete"]:
                continue
            if self.threading.should_extend_thread(thread["updated_at"], capsule.timestamp):
                # If we have a centroid, also check semantic proximity
                if capsule.embedding and thread.get("centroid"):
                    sim = cosine_similarity(capsule.embedding, thread["centroid"])
                    if sim >= self.clustering.similarity_threshold:
                        result["action"] = "extend"
                        result["thread_id"] = thread["id"]
                        break
                else:
                    result["action"] = "extend"
                    result["thread_id"] = thread["id"]
                    break

        return result

    def process_graph_edges(
        self,
        capsule: ContextCapsule,
        recent_capsules: list[ContextCapsule],
        existing_semantic_count: int = 0,
    ) -> list[GraphEdge]:
        """
        Step 5: Create graph edges for the new capsule.
        Returns a list of edges to persist.
        """
        edges = []

        # Temporal edge to the most recent capsule
        if recent_capsules:
            prev = recent_capsules[0]  # Most recent
            if prev.id != capsule.id:
                edges.append(self.graph.create_temporal_edge(prev.id, capsule.id))

        # Semantic edges (with explosion protection)
        semantic_edges = self.graph.find_semantic_edges(
            capsule, recent_capsules, existing_semantic_count
        )
        edges.extend(semantic_edges)

        return edges

    def process_reasoning(
        self,
        capsule: ContextCapsule,
        thread_capsules: list[ContextCapsule],
    ) -> list[GraphEdge]:
        """
        Step 5b: Detect reasoning relationships within the thread.
        Returns GraphEdge objects with confidence as weight.
        """
        reasoning_edges = self.reasoning.infer_reasoning_edges(
            capsule, thread_capsules
        )
        return [
            GraphEdge(
                source_id=re.source_id,
                target_id=re.target_id,
                edge_type=re.edge_type,
                weight=re.confidence,
            )
            for re in reasoning_edges
        ]

    def update_working_memory(self, capsule: ContextCapsule):
        """Step 6: Add the capsule to the user's working memory."""
        memory = self._get_memory(capsule.user_id)

        # Detect context drift before adding
        drift = False
        if capsule.embedding:
            drift = memory.detect_context_drift(capsule.embedding)
            if drift:
                logger.info(f"Context drift detected for user {capsule.user_id}")

        memory.add_capsule(capsule)
        return drift

    # ─── Semantic Recall ───────────────────────────────────────────────
    def search(self, query_text: str) -> list[float]:
        """Prepare a search query embedding for semantic recall."""
        return self.recall.prepare_query(query_text)

    # ─── Knowledge Consolidation ───────────────────────────────────────
    def consolidate_thread(
        self,
        thread_title: str,
        capsule_titles: list[str],
        capsule_urls: list[str],
        thread_summary: str = None,
    ):
        """Convert a completed thread into a knowledge record."""
        return self.knowledge.extract_knowledge_from_thread(
            thread_title, capsule_titles, capsule_urls, thread_summary
        )

    # ─── Decision Detection ────────────────────────────────────────────
    def detect_decision(
        self,
        capsule_titles: list[str],
        user_id: str,
        thread_id: str = None,
    ):
        """Check if recent capsules indicate a decision was made."""
        return self.decisions.create_decision_from_titles(
            capsule_titles, user_id, thread_id
        )

    # ─── Graph Formatting ─────────────────────────────────────────────
    def format_graph_for_ui(self, capsules, edges, clusters=None):
        """Format graph data for the Cognitive Map UI."""
        return self.graph.format_for_ui(capsules, edges, clusters)
