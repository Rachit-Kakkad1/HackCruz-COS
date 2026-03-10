"""
COS Backend — Context Map API.

GET /api/v1/context/map — Returns graph data for the Cognitive Map UI.
This is the endpoint that feeds the React Flow visualization.
"""

import uuid

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.database import repositories as repo
from cos_brain.brain import CognitiveBrain

router = APIRouter(prefix="/api/v1/context", tags=["Context Map"])

brain = CognitiveBrain()


@router.get("/map")
async def get_context_map(
    userId: str = Query(..., description="User ID"),
    limit: int = Query(100, ge=1, le=200, description="Max nodes"),
    db: AsyncSession = Depends(get_db),
):
    """
    Return the cognitive graph data for the Cognitive Map UI.
    Nodes = capsules, Edges = relationships, Clusters = groupings.
    Limited to the most recent N nodes for performance.
    """
    try:
        user_id = uuid.UUID(userId)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid userId — must be a valid UUID")

    # Get recent capsules (nodes)
    capsules = await repo.get_recent_capsules(db, user_id, limit)
    capsule_ids = [c.id for c in capsules]

    # Get edges between these capsules
    edges = await repo.get_edges_for_capsules(db, capsule_ids)

    # Get active clusters
    clusters = await repo.get_active_clusters(db, user_id)

    # Format for the React Flow UI
    capsule_dicts = [
        {
            "id": str(c.id),
            "title": c.title,
            "domain": c.domain,
            "url": c.url,
            "timestamp": c.timestamp.strftime("%H:%M"),
            "cluster_id": str(c.cluster_id) if c.cluster_id else None,
        }
        for c in capsules
    ]

    edge_dicts = [
        {
            "source_id": str(e.source_id),
            "target_id": str(e.target_id),
            "edge_type": e.edge_type,
            "weight": e.weight,
        }
        for e in edges
    ]

    cluster_dicts = [
        {
            "id": str(c.id),
            "label": c.label or "Unnamed Cluster",
            "nodeIds": [
                str(cap.id) for cap in capsules
                if cap.cluster_id and cap.cluster_id == c.id
            ],
        }
        for c in clusters
    ]

    return brain.format_graph_for_ui(capsule_dicts, edge_dicts, cluster_dicts)
