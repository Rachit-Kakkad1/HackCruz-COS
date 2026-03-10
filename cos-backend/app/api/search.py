"""
COS Backend — Semantic Search API.

POST /api/v1/search/recall — Search browsing memory by meaning.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.database import repositories as repo
from cos_brain.brain import CognitiveBrain

router = APIRouter(prefix="/api/v1/search", tags=["Search"])

brain = CognitiveBrain()


class RecallRequest(BaseModel):
    userId: str
    query: str
    limit: Optional[int] = 10


@router.post("/recall")
async def semantic_recall(
    request: RecallRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Search browsing memory semantically.

    Pipeline: query → embedding → pgvector nearest-neighbor → ranked results
    """
    query_embedding = brain.search(request.query)
    user_id = uuid.UUID(request.userId)

    capsules = await repo.search_capsules_by_vector(
        db, user_id, query_embedding, limit=request.limit
    )

    # Convert to dicts with embeddings for re-ranking
    capsule_dicts = [
        {
            "id": str(c.id),
            "title": c.title,
            "domain": c.domain,
            "url": c.url,
            "timestamp": c.timestamp.isoformat(),
            "embedding": list(c.embedding) if c.embedding else None,
        }
        for c in capsules
    ]

    ranked = brain.recall.rank_results(query_embedding, capsule_dicts)
    return brain.recall.format_recall_results(ranked)
