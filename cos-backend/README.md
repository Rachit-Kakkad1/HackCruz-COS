# Context Scope (COS) — Cognitive Backend

> An AI-powered cognitive memory system that transforms raw browsing activity into structured reasoning, memory, and knowledge.

## Architecture

```
Chrome Extension → FastAPI API → Cognitive Brain → PostgreSQL + pgvector
                                      ↓
                               Context Graph → Cognitive Map UI
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI (Python 3.11+) |
| Database | PostgreSQL 16 + pgvector |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| LLM | OpenAI GPT-4o-mini (optional) |
| Background | APScheduler |
| Cache | Redis 7 |

---

## Quick Start

### 1. Clone and configure

```bash
cd cos-backend
cp .env.example .env
# Edit .env with your OPENAI_API_KEY (optional)
```

### 2. Start with Docker

```bash
docker-compose up --build
```

This starts:
- **PostgreSQL** (with pgvector) on port `5432`
- **Redis** on port `6379`
- **FastAPI API** on port `8000`
- **Background Worker** (consolidation, retention, backfill)

### 3. Verify

```bash
curl http://localhost:8000/health
# {"status":"ok","service":"COS Cognitive Backend"}
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/events/track` | Ingest browsing event |
| `GET` | `/api/v1/analytics/usage-today` | Per-domain time stats |
| `GET` | `/api/v1/analytics/focus-score` | Focus Score (0-100) |
| `GET` | `/api/v1/analytics/timeline` | Chronological capsule list |
| `POST` | `/api/v1/search/recall` | Semantic memory search |
| `GET` | `/api/v1/threads` | List reasoning threads |
| `GET` | `/api/v1/threads/{id}` | Thread detail + capsules |
| `GET` | `/api/v1/context/map` | Graph data for Cognitive Map |
| `DELETE` | `/api/v1/user/data` | Delete all user data (GDPR) |
| `GET` | `/health` | Health check |

### Example: Track an event

```bash
curl -X POST http://localhost:8000/api/v1/events/track \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "url": "https://docs.aws.amazon.com/lambda/",
    "title": "AWS Lambda Documentation",
    "textSnippet": "AWS Lambda runs code without provisioning servers",
    "timestamp": "2025-03-10T10:21:00Z"
  }'
```

### Example: Semantic recall

```bash
curl -X POST http://localhost:8000/api/v1/search/recall \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "query": "that article about fixing React state bug"
  }'
```

---

## Cognitive Brain Modules

| Module | Purpose |
|--------|---------|
| `capsule.py` | Context Capsule data model |
| `embedding_engine.py` | Sentence-transformer embeddings with SHA256 cache |
| `working_memory.py` | Active context buffer (last 20 capsules) |
| `clustering_engine.py` | Cosine similarity + time clustering |
| `thread_engine.py` | Reasoning thread management |
| `context_graph.py` | Temporal cognitive graph |
| `knowledge_engine.py` | Long-term memory consolidation |
| `decision_memory.py` | Decision detection |
| `recall_engine.py` | Semantic vector search |
| `brain.py` | Central orchestrator |

---

## Background Workers

| Task | Schedule | Description |
|------|----------|-------------|
| Memory Consolidation | 3 AM daily | Convert threads → knowledge records |
| Data Retention | 4 AM daily | Purge capsules older than 30 days |
| Embedding Backfill | Every 5 min | Process unembedded capsules |
| Reflection Engine | 11 PM daily | Generate self-improvement insights |

---

## Development (without Docker)

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Requires a running PostgreSQL with pgvector and Redis.
