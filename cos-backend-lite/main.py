"""
COS Backend Lite — FastAPI Application.

A lightweight, local-only cognitive memory backend.

Endpoints:
    GET  /health   — Health check
    POST /context  — Ingest a browsing context snapshot
    GET  /recall   — Retrieve the most recent relevant context
"""

import logging
import subprocess
import webbrowser
from datetime import datetime, timezone

import time
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

from embedder import generate_embedding
from vector_store import vector_store
from database import init_db, insert_context, get_recent, get_all_contexts, get_all_edges, get_contexts_before
from graph_engine import process_new_context
from clustering_engine import cluster_contexts

# ─── Logging ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger(__name__)

# ─── Initialize database on import ───────────────────────────────────────
init_db()

# ─── AI Autonomy Engine ──────────────────────────────────────────────────
import time

async def predict_next_task():
    """Predicts a high-confidence task cluster for the user to resume."""
    try:
        contexts = get_all_contexts()
        embeddings = vector_store.get_all_embeddings()
        if not contexts:
            return None
            
        nodes, _ = cluster_contexts(contexts, embeddings)
        if not nodes:
            return None
            
        # Strategy: Find the most substantial recent task that isn't the current "Browsing" or "Activity"
        # Skip the very first node if it was active within the last 60 seconds (user is likely still on it)
        now = datetime.now(timezone.utc).isoformat()
        
        candidates = []
        for n in nodes:
            # We want productive tasks (Coding, Research, Writing)
            if n['category'] in ["Coding", "Research", "Writing"]:
                # Simple score: count / (time since last active)
                # For demo, let's just pick the most recent productive one
                candidates.append(n)
        
        if not candidates:
            return None
            
        # Pick the top one
        best = sorted(candidates, key=lambda x: x['last_active'], reverse=True)[0]
        
        # Calculate confidence (simplified for now)
        confidence = 0.85 if best['count'] > 2 else 0.65
        
        return {
            "task": best['label'],
            "category": best['category'],
            "confidence": confidence,
            "context_id": best['contexts'][0]['id']
        }
    except Exception as e:
        logger.error(f"Prediction engine failed: {e}")
        return None

async def check_distraction(new_context_title: str):
    """Detects if user switched from deep work to a distraction."""
    distractions = ["youtube", "twitter", "reddit", "facebook", "netflix", "gaming"]
    title_lower = new_context_title.lower()
    
    if any(d in title_lower for d in distractions):
        # User is likely distracted. Proactively suggest resuming the last productive task.
        suggestion = await predict_next_task()
        if suggestion:
            await manager.broadcast({
                "type": "focus_radar_suggestion",
                "message": f"Detected a break. Want to jump back into '{suggestion['task']}'?",
                **suggestion
            })

# ─── WebSocket Manager ───────────────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # Connection might be closed
                pass

manager = ConnectionManager()

async def broadcast_graph_update():
    """Broadcasts the latest clustered graph to all connected clients."""
    try:
        contexts = get_all_contexts()
        embeddings = vector_store.get_all_embeddings()
        if not contexts:
            nodes, edges = [], []
        else:
            nodes, edges = cluster_contexts(contexts, embeddings)
        
        await manager.broadcast({
            "type": "graph_update",
            "nodes": nodes,
            "edges": edges
        })
    except Exception as e:
        logger.error(f"WebSocket broadcast failed: {e}")

# ─── App Initialization ───────────────────────────────────────────────────
app = FastAPI(
    title="COS Backend Lite — Cognitive Memory",
    description="Lightweight local backend for the Cognitive Operating System.",
    version="1.0.0",
)

# ─── CORS — allow Chrome extension and localhost origins ──────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("🧠 COS Backend Lite started")


# ─── Request / Response Models ────────────────────────────────────────────

class AppContext(BaseModel):
    title: str
    url: str
    text: Optional[str] = None
    app: Optional[str] = None
    workspace: Optional[str] = None
    timestamp: Optional[str] = None

class OSContext(BaseModel):
    app: str
    window_title: str
    workspace: Optional[str] = None
    timestamp: Optional[str] = None

class ScreenContextInput(BaseModel):
    text: str
    timestamp: Optional[str] = None

class VoiceCommandInput(BaseModel):
    query: str


class RecallResponse(BaseModel):
    title: str
    url: str
    summary: str
    timestamp: str


# ─── Endpoints ────────────────────────────────────────────────────────────

async def execute_resume(context_id: int):
    """Internal helper to execute the resume action."""
    all_contexts = get_all_contexts()
    ctx = next((c for c in all_contexts if c['id'] == context_id), None)
    
    if not ctx:
        return {"status": "error", "message": "Context not found"}
        
    app_name = ctx.get('app', '').lower()
    workspace = ctx.get('workspace')
    url = ctx.get('url')
    
    logger.info(f"🚀 Executing resume for {context_id}: {app_name}")
    
    try:
        if "code" in app_name and workspace:
            subprocess.Popen(["code", workspace], shell=True)
            return {"status": "launched", "action": f"vscode {workspace}"}
        elif url and url.startswith("http"):
            webbrowser.open(url)
            return {"status": "launched", "action": f"browser {url}"}
        elif workspace:
            subprocess.Popen(["start", "", workspace], shell=True)
            return {"status": "launched", "action": f"start {workspace}"}
        else:
            return {"status": "error", "message": "No actionable workspace metadata"}
    except Exception as e:
        logger.error(f"Resume execution failed: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/resume/{context_id}")
async def resume_context(context_id: int):
    """Public endpoint to restore a context."""
    result = await execute_resume(context_id)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "COS Backend Lite",
        "contexts_stored": vector_store.count,
    }


@app.post("/context")
async def ingest_context(ctx: AppContext):
    """
    Ingest a browsing context snapshot.

    Steps:
        1. Combine title + text.
        2. Generate semantic embedding.
        3. Store metadata in SQLite.
        4. Store embedding in FAISS.
        5. Run graph engine to find similar contexts.
    """
    # Resolve timestamp
    ts = int(time.time()) if ctx.timestamp is None else int(ctx.timestamp)

    # Combine title + text for richer embedding
    combined_text = f"{ctx.title}. {ctx.text or ''}"

    # Generate embedding
    embedding = generate_embedding(combined_text)

    # Create summary (first 500 chars of combined text)
    summary = combined_text[:500]

    # Store in SQLite
    context_id = insert_context(
        title=ctx.title,
        url=ctx.url,
        summary=summary,
        app=ctx.app or "Browser",
        workspace=ctx.workspace,
        timestamp=ts,
    )

    # Store in FAISS
    vector_store.add(
        embedding=embedding,
        meta={
            "context_id": context_id,
            "title": ctx.title,
            "url": ctx.url,
            "summary": summary,
            "timestamp": ts,
        },
    )

    # Run graph engine (find similar contexts and create edges)
    process_new_context(context_id, embedding)

    # Broadcast updated graph live
    await broadcast_graph_update()
    
    # Run distraction check
    await check_distraction(ctx.title)

    logger.info(f"📦 Stored context #{context_id}: {ctx.title[:60]}")

    return {"status": "stored", "id": context_id}


@app.post("/context/os")
async def ingest_os_context(ctx: OSContext):
    """Ingest a Snapshot of the active OS Window."""
    ts = int(time.time()) if ctx.timestamp is None else int(ctx.timestamp)
    
    combined_text = f"[{ctx.app}] {ctx.window_title}"
    embedding = generate_embedding(combined_text)
    summary = combined_text[:500]
    # Step 4: Store in SQLite
    context_id = insert_context(
        title=ctx.window_title,
        url="app://" + ctx.app,
        summary=f"OS Context: {ctx.app}",
        app=ctx.app,
        workspace=ctx.workspace,
        timestamp=ts,
    )
    
    vector_store.add(
        embedding=embedding,
        meta={
            "context_id": context_id,
            "title": ctx.window_title,
            "url": f"os://{ctx.app.lower()}",
            "summary": summary,
            "timestamp": ts,
        },
    )
    # Step 5: Process similarity edges
    process_new_context(context_id, embedding)
    
    # Broadcast live update
    await broadcast_graph_update()

    logger.info(f"📦 Stored OS context #{context_id}: {ctx.window_title[:60]}")
    return {"status": "os_context_stored", "id": context_id}


@app.post("/context/screen")
async def ingest_screen_context(ctx: ScreenContextInput):
    """Ingest OCR text extracted from the user's screen."""
    import time
    ts = int(time.time()) if ctx.timestamp is None else int(ctx.timestamp)
    
    combined_text = ctx.text
    embedding = generate_embedding(combined_text)
    summary = combined_text[:500]
    
    context_id = insert_context(
        title="Screen Context",
        url="os://screen",
        summary=summary,
        timestamp=ts,
    )
    
    vector_store.add(
        embedding=embedding,
        meta={
            "context_id": context_id,
            "title": "Screen Context",
            "url": "os://screen",
            "summary": summary,
            "timestamp": ts,
        },
    )
    process_new_context(context_id, embedding)
    logger.info(f"📦 Stored Screen OCR context #{context_id}")
    return {"status": "stored", "context_id": context_id}


@app.post("/voice/command")
async def handle_voice_command(cmd: VoiceCommandInput):
    """Processes a spoken query with intent parsing and automation triggers."""
    query = cmd.query.lower()
    
    # 1. Intent Detection: Resume/Open
    if any(w in query for w in ["resume", "open", "continue", "back"]):
        suggestion = await predict_next_task()
        if suggestion:
            await execute_resume(suggestion['context_id'])
            return {
                "response": f"Resuming your {suggestion['category']} task: '{suggestion['task']}'.",
                "action": "resume"
            }
            
    # 2. Intent Detection: Confirmation (Yes/Sure)
    if any(w in query for w in ["yes", "sure", "do it", "yeah"]):
        suggestion = await predict_next_task()
        if suggestion:
            await execute_resume(suggestion['context_id'])
            return {"response": "Understood. Resuming now.", "action": "resume"}

    # 3. Fallback: Semantic Search
    query_embedding = generate_embedding(cmd.query)
    results = vector_store.search(query_embedding, k=1)
    
    if results:
        top = results[0]
        app_source = top.get("url", "").replace("os://", "")
        if not app_source or app_source.startswith("http"): 
            app_source = "your browser"
        elif app_source == "screen": 
            app_source = "a recent screen capture"
            
        title = top.get("title", "Unknown Task")
        response = f"You were recently looking at '{title[:50]}' in {app_source}. Would you like me to reopen it?"
        return {"response": response, "context": top}
        
    return {"response": "I couldn't find any recent context, but I'm monitoring your activity."}


@app.get("/recall", response_model=RecallResponse)
async def recall_context():
    """
    Recall the most relevant recent context.

    Strategy:
        1. Get the most recent context from SQLite.
        2. Use its embedding to search FAISS for the best semantic match.
        3. Return the top result.
    """
    recent = get_recent(limit=1)
    if not recent:
        return RecallResponse(
            title="No context yet",
            url="",
            summary="Start browsing to build your cognitive memory!",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    latest = recent[0]

    # Generate embedding for the most recent context to find related ones
    query_text = f"{latest['title']}. {latest['summary'] or ''}"
    query_embedding = generate_embedding(query_text)

    # Search FAISS for most similar context
    results = vector_store.search(query_embedding, k=1)

    if results:
        top = results[0]
        return RecallResponse(
            title=top.get("title", latest["title"]),
            url=top.get("url", latest["url"]),
            summary=top.get("summary", latest.get("summary", "")),
            timestamp=top.get("timestamp", latest["timestamp"]),
        )

    return RecallResponse(
        title=latest["title"],
        url=latest["url"],
        summary=latest.get("summary", ""),
        timestamp=latest["timestamp"],
    )


# ─── Temporal Reconstruction Engine ──────────────────────────────────────
import numpy as np

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def build_graph_at_time(timestamp: int):
    """
    Rebuilds the cognitive graph for a specific historical point.
    1. Fetches contexts in a 24-hour window: [timestamp - 24h, timestamp]
    2. Clusters contexts into Task-Level nodes
    3. Recomputes graph for tasks
    """
    from database import get_contexts_before
    from vector_store import vector_store
    from clustering_engine import cluster_contexts
    
    # 24 hour window in seconds
    WINDOW_SIZE = 24 * 60 * 60 
    since = timestamp - WINDOW_SIZE
    
    contexts = get_contexts_before(timestamp, since=since)
    
    if not contexts:
        return {"nodes": [], "edges": []}
        
    # Retrieve embeddings for the window
    embeddings = []
    valid_contexts = []
    for ctx in contexts:
        meta_id = vector_store.get_index_by_context_id(ctx["id"])
        if meta_id is not None:
            embeddings.append(vector_store.index.reconstruct(meta_id))
            valid_contexts.append(ctx)
            
    if not valid_contexts:
        return {"nodes": [], "edges": []}
        
    embeddings_np = np.array(embeddings).astype('float32')
    
    # Run clustering to get Task-Level nodes
    task_nodes, task_edges = cluster_contexts(valid_contexts, embeddings_np)
    
    # Format for frontend
    return {
        "nodes": task_nodes,
        "edges": task_edges,
        "is_windowed": True,
        "window_start": since,
        "window_end": timestamp
    }

@app.get("/contexts_at_time")
async def get_contexts_at_time(timestamp: int):
    """Temporal query endpoint for Memory Time-Travel."""
    try:
        graph = build_graph_at_time(timestamp)
        return graph
    except Exception as e:
        logger.error(f"Time-travel query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/time_range")
async def get_time_range():
    """Returns the earliest and latest context timestamps."""
    contexts = get_all_contexts()
    if not contexts:
        now = int(time.time())
        return {"min": now, "max": now}
    
    timestamps = [c['timestamp'] for c in contexts]
    return {
        "min": min(timestamps),
        "max": max(timestamps)
    }

@app.post("/reset")
async def reset_memory():
    """Wipes all local cognitive memory."""
    # Wipe FAISS
    import os
    from vector_store import INDEX_PATH, META_PATH
    from database import DB_PATH
    
    # Simple strategy: remove files and re-init
    for path in [INDEX_PATH, META_PATH, DB_PATH]:
        if os.path.exists(path):
            os.remove(path)
            
    vector_store._load()
    init_db()
    
    # Notify dashboard to clear
    await manager.broadcast({
        "type": "graph_update",
        "nodes": [],
        "edges": []
    })
    
    logger.warning("🗑️ Memory reset triggered and executed.")
    return {"status": "cleared"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
