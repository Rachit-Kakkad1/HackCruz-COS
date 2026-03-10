"""
COS Brain — Reasoning Inference Engine.

Transforms the context graph from a simple activity graph into a
reasoning graph by detecting logical relationships between capsules
within the same thread.

Reasoning edge types:
    CAUSES          — A leads to / triggers B
    ANSWERS         — B answers a question posed by A
    EXPLAINS        — B provides context/explanation for A
    CONTRADICTS     — B contradicts the claim or approach in A
    DECISION_RESULT — B is the outcome of a decision explored in A
    IMPLEMENTS      — B is an implementation of a concept in A

Detection pipeline:
    1. Keyword pattern matching (fast, no model needed)
    2. Semantic similarity analysis (from existing embeddings)
    3. Optional LLM reasoning (when OpenAI key is available)
"""

import logging
import re
from dataclasses import dataclass
from typing import Optional

from cos_brain.capsule import ContextCapsule
from cos_brain.embedding_engine import cosine_similarity

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# REASONING EDGE DATA MODEL
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class ReasoningEdge:
    """A logical relationship between two capsules."""
    source_id: str
    target_id: str
    edge_type: str  # causes | answers | explains | contradicts | decision_result | implements
    confidence: float  # 0.0 – 1.0


# ═══════════════════════════════════════════════════════════════════════════
# KEYWORD PATTERN RULES
# ═══════════════════════════════════════════════════════════════════════════

# Each rule: (edge_type, source_patterns, target_patterns, base_confidence)
# Logic: if SOURCE title matches source_patterns AND TARGET title matches
# target_patterns, emit an edge of edge_type with base_confidence.
PATTERN_RULES = [
    # ANSWERS: source looks like a question, target is from a Q&A site
    (
        "answers",
        [r"how to", r"why does", r"what is", r"can i", r"error", r"issue", r"bug", r"problem"],
        [r"stackoverflow\.com", r"stackexchange\.com", r"answer", r"solution", r"solved", r"fix"],
        0.72,
    ),
    # IMPLEMENTS: source is documentation/concept, target is code/tutorial
    (
        "implements",
        [r"docs?\.", r"documentation", r"guide", r"api reference", r"specification"],
        [r"github\.com", r"codepen", r"tutorial", r"example", r"implementation", r"how to build"],
        0.68,
    ),
    # CAUSES: source describes error/setup, target is the consequence
    (
        "causes",
        [r"install", r"config", r"setup", r"upgrade", r"migrate", r"deploy", r"change"],
        [r"error", r"broken", r"fail", r"crash", r"issue", r"bug", r"not working", r"exception"],
        0.65,
    ),
    # EXPLAINS: target provides deeper explanation of source topic
    (
        "explains",
        [r"what is", r"overview", r"introduction", r"getting started"],
        [r"deep dive", r"how .* works", r"internals", r"architecture", r"under the hood", r"explained"],
        0.70,
    ),
    # CONTRADICTS: comparison or alternative approach
    (
        "contradicts",
        [],  # any source
        [r"vs\.?( |$)", r"versus", r"alternative", r"instead of", r"don.?t use", r"deprecated"],
        0.60,
    ),
    # DECISION_RESULT: research → decision outcome
    (
        "decision_result",
        [r"comparison", r"vs\.?( |$)", r"pricing", r"review", r"benchmark", r"pros.*cons"],
        [r"chose", r"selected", r"using", r"switched to", r"migrated to", r"getting started"],
        0.66,
    ),
]


# ═══════════════════════════════════════════════════════════════════════════
# REASONING ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class ReasoningEngine:
    """
    Detects logical relationships between capsules within a thread.

    Detection hierarchy (fast → expensive):
    1. Keyword/pattern matching — always runs
    2. Semantic similarity boosting — uses existing embeddings
    3. LLM reasoning — optional, runs async if API key is set

    Confidence scoring:
    - Pattern match: base confidence from rule
    - Semantic boost: +0.1 if similarity > 0.6, +0.15 if > 0.8
    - LLM override: uses model's confidence directly (0.0–1.0)
    """

    def __init__(
        self,
        min_confidence: float = 0.55,
        max_reasoning_edges_per_pair: int = 1,
    ):
        self.min_confidence = min_confidence
        self.max_per_pair = max_reasoning_edges_per_pair

    # ─── Main Entry Point ────────────────────────────────────────────────
    def infer_reasoning_edges(
        self,
        new_capsule: ContextCapsule,
        thread_capsules: list[ContextCapsule],
    ) -> list[ReasoningEdge]:
        """
        Detect reasoning relationships between the new capsule and
        other capsules in the same thread.

        Returns edges sorted by confidence descending, capped at
        max 3 reasoning edges per new capsule (explosion protection).
        """
        if not thread_capsules:
            return []

        all_edges: list[ReasoningEdge] = []

        for other in thread_capsules:
            if other.id == new_capsule.id:
                continue

            # Try pattern matching in both directions
            edges = self._pattern_match(other, new_capsule)

            # Boost confidence with semantic similarity
            for edge in edges:
                edge.confidence = self._apply_semantic_boost(
                    edge.confidence, other, new_capsule
                )

            # Filter by minimum confidence
            edges = [e for e in edges if e.confidence >= self.min_confidence]

            # Keep only best edge per pair
            if edges:
                edges.sort(key=lambda e: -e.confidence)
                all_edges.append(edges[0])

        # Cap total reasoning edges (explosion protection)
        all_edges.sort(key=lambda e: -e.confidence)
        return all_edges[:3]

    # ─── Pattern Matching ────────────────────────────────────────────────
    def _pattern_match(
        self,
        source: ContextCapsule,
        target: ContextCapsule,
    ) -> list[ReasoningEdge]:
        """Apply keyword pattern rules to detect reasoning relationships."""
        edges = []
        source_text = f"{source.title} {source.domain}".lower()
        target_text = f"{target.title} {target.domain}".lower()

        for edge_type, src_patterns, tgt_patterns, base_conf in PATTERN_RULES:
            src_match = not src_patterns or any(
                re.search(p, source_text) for p in src_patterns
            )
            tgt_match = not tgt_patterns or any(
                re.search(p, target_text) for p in tgt_patterns
            )

            if src_match and tgt_match:
                edges.append(ReasoningEdge(
                    source_id=source.id,
                    target_id=target.id,
                    edge_type=edge_type,
                    confidence=base_conf,
                ))

        return edges

    # ─── Semantic Similarity Boost ───────────────────────────────────────
    def _apply_semantic_boost(
        self,
        base_confidence: float,
        source: ContextCapsule,
        target: ContextCapsule,
    ) -> float:
        """
        Boost confidence if embeddings confirm semantic relatedness.
        High similarity = stronger logical connection.
        """
        if source.embedding is None or target.embedding is None:
            return base_confidence

        sim = cosine_similarity(source.embedding, target.embedding)

        if sim >= 0.85:
            return min(1.0, base_confidence + 0.18)
        elif sim >= 0.70:
            return min(1.0, base_confidence + 0.12)
        elif sim >= 0.55:
            return min(1.0, base_confidence + 0.06)
        elif sim < 0.30:
            # Very low similarity = reduce confidence (probably wrong match)
            return max(0.0, base_confidence - 0.15)

        return base_confidence


# ═══════════════════════════════════════════════════════════════════════════
# LLM-BASED REASONING (optional enhancement)
# ═══════════════════════════════════════════════════════════════════════════

async def llm_reasoning_inference(
    capsule_titles: list[str],
) -> list[dict]:
    """
    Use LLM to detect reasoning relationships between capsules.
    Returns list of {source_idx, target_idx, edge_type, confidence}.

    Only runs if OPENAI_API_KEY is configured. Falls back gracefully.
    """
    try:
        from app.config import get_settings
        settings = get_settings()
        if not settings.openai_api_key:
            return []

        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)

        titles_text = "\n".join(
            f"{i}. {t}" for i, t in enumerate(capsule_titles[:10])
        )

        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a reasoning analyst. Given numbered page titles from "
                        "a browsing session, detect logical relationships.\n\n"
                        "Edge types: CAUSES, ANSWERS, EXPLAINS, CONTRADICTS, "
                        "DECISION_RESULT, IMPLEMENTS\n\n"
                        "Output ONLY lines in this format (one per relationship found):\n"
                        "source_idx|target_idx|edge_type|confidence\n\n"
                        "Example: 0|2|ANSWERS|0.85\n"
                        "Output NONE if no clear relationships exist."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Pages:\n{titles_text}",
                },
            ],
            max_tokens=150,
            temperature=0.2,
        )

        text = response.choices[0].message.content.strip()
        if text == "NONE":
            return []

        results = []
        for line in text.strip().split("\n"):
            parts = line.strip().split("|")
            if len(parts) == 4:
                try:
                    results.append({
                        "source_idx": int(parts[0]),
                        "target_idx": int(parts[1]),
                        "edge_type": parts[2].strip().lower(),
                        "confidence": float(parts[3]),
                    })
                except (ValueError, IndexError):
                    continue

        return results

    except Exception as e:
        logger.warning(f"LLM reasoning inference failed: {e}")
        return []
