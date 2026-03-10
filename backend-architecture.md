# Context Scope (COS) Backend Architecture Guide

While the current repository provides the **Frontend UI** and the **Chrome Extension Injection mechanism**, a robust backend is required to power the actual data processing, analytics, and AI-driven insights shown in the interface.

This document outlines the necessary backend components, data pipelines, and intelligent services required to bring Context Scope to life.

---

## 1. Core Architecture Overview

To support a privacy-first, real-time context analyzer, the backend should be built on a fast, asynchronous foundation capable of handling a high volume of small events (tab switches, time tracking).

**Recommended Tech Stack:**
*   **API Layer**: Node.js (Express/Fastify) or Python (FastAPI) for AI native integration.
*   **Database**: PostgreSQL (via Supabase or Prisma) for relational user data, time-logs, and settings.
*   **Vector Store**: Pinecone, Milvus, or pgvector for storing text embeddings to power the "Recall Context" search.
*   **LLM Provider**: OpenAI (GPT-4o mini) or Anthropic (Claude 3 Haiku) for fast classification and summarization.
*   **Caching**: Redis (for real-time live presence tracking and focus states).

---

## 2. Event Ingestion Pipeline (The "Tracker")

The Chrome Extension's `background.js` (Service Worker) will act as the data producer. It needs a high-throughput endpoint to receive context events.

### Required Endpoints:
- `POST /api/v1/events/track`
  - **Payload**: `{ userId, tabUrl, tabTitle, timestamp, eventType: 'SWITCH_IN' | 'SWITCH_OUT' | 'HEARTBEAT' }`
  - **Function**: Calculates time spent on a URL. If a user switches from YouTube to GitHub, it logs the duration of the YouTube session.

### Focus Lock Enforcement:
The backend needs to maintain the user's blocklist and current `isFocusLocked` state.
- `GET /api/v1/rules/focus-lock`
  - Returns a strict list of regex rules for URLs to block when the toggle is active.

---

## 3. Analytics Engine (The "Dashboard Data")

The graphs and scores shown in the Sliding Panel require analytical processing over the raw event data.

### Required Endpoints:
- `GET /api/v1/analytics/usage-today`
  - **Function**: Aggregates total time spent per domain (e.g., `youtube.com: 45m`, `github.com: 2h`).
  - Powers the **App Usage** bar charts.
- `GET /api/v1/analytics/focus-score`
  - **Function**: An algorithm that calculates a 0-100 score based on the ratio of "Productive" domains vs "Distracting" domains, penalized by the frequency of rapid context switching.
  - Powers the **Focus Score** radial dial.

---

## 4. AI & Context Intelligence (The "Brain")

This is what makes COS an "Operating System" rather than just a time-tracker. The backend needs to semantically understand *what* the user is doing.

### The Auto-Grouping Cluster Logic
When a user visits several pages (e.g., an AWS doc, a StackOverflow thread, and a GitHub issue), the backend must group these into a "Session".
1.  **Text Extraction**: The extension sends a snippet of the page text to the backend.
2.  **LLM Classification**: A background prompt is sent to an LLM: *"Given these 5 recent page titles, cluster them into a single ongoing project task."*
3.  **Output**: Returns the generated cluster: e.g., "Analyzing RAG architectures across 3 context sources."

### Required Endpoints:
- `GET /api/v1/clusters/active`
  - Returns the LLM-generated smart clusters shown in the **Active Cluster** UI section.

---

## 5. Semantic Search & Recall

The UI features a Search icon and "Recall Context" buttons. To find past work without needing exact keywords, you need a Vector Database pipeline.

1.  **Embedding Generation**: Every 5 minutes, the backend batches recent URL titles and text snippets and converts them into dense vector embeddings using an embedding model (like `text-embedding-3-small`).
2.  **Vector Storage**: Stores these vectors alongside the original URL and timestamp in a database like `pgvector`.
3.  **Semantic Querying**: 
    - `POST /api/v1/search/recall`
    - When a user searches "That video about budget drafts", the backend embeds the query and performs a nearest-neighbor vector search to return the exact YouTube link from 3 days ago.

---

## 6. Privacy & Security Infrastructure

Since Context Scope tracks browser history, the backend must be exceptionally secure.

*   **Zero-Knowledge Architecture (Optional but ideal)**: End-to-end encrypt the URLs on the client side before sending them to the backend. The backend only sees encrypted strings and performs analytics blindly.
*   **Data Retention Policies**: A cron job that permanently deletes all raw timeline data older than 30 days, keeping only anonymous aggregated analytics to protect user privacy.
*   **Authentication**: standard JWT-based authentication (Supabase Auth / Clerk) to link the Chrome Extension instance to a user account.
