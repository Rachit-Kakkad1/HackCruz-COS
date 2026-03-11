"""
COS Backend Lite — SQLite Database.

Stores context metadata and graph edges in a local SQLite database.
No external dependencies beyond the Python stdlib.
"""

import os
import sqlite3
import logging
from typing import Optional

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "cos.db")


def _get_conn() -> sqlite3.Connection:
    """Get a SQLite connection with row factory enabled."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they do not exist."""
    conn = _get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contexts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            summary TEXT,
            app TEXT,
            workspace TEXT,
            timestamp TEXT NOT NULL
        )
    """)
    
    # Migration: Add columns if they don't exist
    try:
        cursor.execute("ALTER TABLE contexts ADD COLUMN app TEXT")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE contexts ADD COLUMN workspace TEXT")
    except sqlite3.OperationalError: pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS context_edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER NOT NULL,
            target_id INTEGER NOT NULL,
            weight REAL NOT NULL,
            FOREIGN KEY (source_id) REFERENCES contexts(id),
            FOREIGN KEY (target_id) REFERENCES contexts(id)
        )
    """)

    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {DB_PATH}")


def insert_context(title: str, url: str, summary: str, timestamp: str, app: str = None, workspace: str = None) -> int:
    """
    Insert a new context record and return its ID.
    """
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO contexts (title, url, summary, app, workspace, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
        (title, url, summary, app, workspace, timestamp),
    )
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return row_id


def get_recent(limit: int = 1) -> list[dict]:
    """
    Retrieve the most recent context records.

    Args:
        limit: Number of records to return (default 1).

    Returns:
        List of context dicts sorted by most recent first.
    """
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, url, summary, timestamp FROM contexts ORDER BY timestamp DESC LIMIT ?",
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_contexts() -> list[dict]:
    """Retrieve all context records sorted by most recent timestamp."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, url, summary, app, workspace, timestamp FROM contexts ORDER BY timestamp DESC"
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_context_by_id(context_id: int) -> Optional[dict]:
    """Retrieve a single context by its ID."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, url, summary, timestamp FROM contexts WHERE id = ?",
        (context_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def insert_edge(source_id: int, target_id: int, weight: float):
    """
    Insert a similarity edge between two context records.

    Args:
        source_id: ID of the new context.
        target_id: ID of the similar existing context.
        weight: Cosine similarity score.
    """
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO context_edges (source_id, target_id, weight) VALUES (?, ?, ?)",
        (source_id, target_id, weight),
    )
    conn.commit()
    conn.close()


def get_all_edges() -> list[dict]:
    """Retrieve all context relationships."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, source_id, target_id, weight FROM context_edges")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_context_count() -> int:
    """Return total number of stored contexts."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM contexts")
    count = cursor.fetchone()[0]
    conn.close()
    return count
