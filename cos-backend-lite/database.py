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
    """Create tables if they do not exist with migration support."""
    conn = _get_conn()
    cursor = conn.cursor()

    # Check if we need to migrate
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contexts'")
    exists = cursor.fetchone()

    if exists:
        # Check if timestamp is already INTEGER (or at least if we've done this migration)
        cursor.execute("PRAGMA table_info(contexts)")
        columns = {row['name']: row['type'] for row in cursor.fetchall()}
        if columns.get('timestamp') == 'TEXT':
            logger.info("Migrating database schema for Memory Time-Travel...")
            
            # Check if contexts_old already exists (possibly from a failed previous attempt)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contexts_old'")
            if cursor.fetchone():
                cursor.execute("DROP TABLE contexts_old")
            
            cursor.execute("ALTER TABLE contexts RENAME TO contexts_old")
            cursor.execute("""
                CREATE TABLE contexts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    summary TEXT,
                    app TEXT,
                    workspace TEXT,
                    cluster_id INTEGER,
                    timestamp INTEGER NOT NULL
                )
            """)
            
            # Migration logic (shared)
            _run_migration(conn)
            
        else:
            # Check if we are in a stuck state: contexts is empty but contexts_old exists
            cursor.execute("SELECT COUNT(*) FROM contexts")
            contexts_count = cursor.fetchone()[0]
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contexts_old'")
            old_table_exists = cursor.fetchone()
            
            if contexts_count == 0 and old_table_exists:
                logger.info("Empty contexts table found with existing contexts_old. Resuming migration...")
                _run_migration(conn)
            else:
                # Table exists and is migrated, ensure columns exist
                try: cursor.execute("ALTER TABLE contexts ADD COLUMN cluster_id INTEGER")
                except sqlite3.OperationalError: pass
                conn.commit()
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contexts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                summary TEXT,
                app TEXT,
                workspace TEXT,
                cluster_id INTEGER,
                timestamp INTEGER NOT NULL
            )
        """)

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


def _run_migration(conn):
    """Internal helper to run the migration from contexts_old to contexts."""
    cursor = conn.cursor()
    
    # Check what columns exist in contexts_old to avoid errors
    cursor.execute("PRAGMA table_info(contexts_old)")
    old_columns = [row['name'] for row in cursor.fetchall()]
    
    # Build the SELECT clause with defaults for missing columns
    app_val = "app" if "app" in old_columns else "'unknown'"
    workspace_val = "workspace" if "workspace" in old_columns else "'default'"
    
    # Perform insertion
    cursor.execute(f"""
        INSERT INTO contexts (id, title, url, summary, app, workspace, timestamp)
        SELECT 
            id, 
            title, 
            url, 
            summary, 
            {app_val}, 
            {workspace_val},
            CAST(strftime('%s', timestamp) AS INTEGER)
        FROM contexts_old
    """)
    
    # Safety check: Compare row counts
    cursor.execute("SELECT COUNT(*) FROM contexts")
    new_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM contexts_old")
    old_count = cursor.fetchone()[0]
    
    if new_count == old_count:
        cursor.execute("DROP TABLE contexts_old")
        conn.commit()
        logger.info(f"Database migration complete. {new_count} rows migrated.")
    else:
        logger.error(f"Migration mismatch: {old_count} old rows vs {new_count} new rows. Keeping contexts_old.")
        conn.rollback()


def insert_context(title: str, url: str, summary: str, timestamp: int = None, app: str = None, workspace: str = None) -> int:
    """
    Insert a new context record and return its ID.
    Timestamp should be Unix epoch seconds.
    """
    if timestamp is None:
        import time
        timestamp = int(time.time())
    
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
    """Retrieve the most recent context records."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, url, summary, app, workspace, timestamp FROM contexts ORDER BY timestamp DESC LIMIT ?",
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


def get_contexts_before(timestamp: int, since: Optional[int] = None) -> list[dict]:
    """Retrieve contexts up to a specific Unix timestamp, optionally within a window."""
    conn = _get_conn()
    cursor = conn.cursor()
    if since:
        cursor.execute(
            "SELECT * FROM contexts WHERE timestamp <= ? AND timestamp >= ? ORDER BY timestamp ASC",
            (timestamp, since),
        )
    else:
        cursor.execute(
            "SELECT * FROM contexts WHERE timestamp <= ? ORDER BY timestamp ASC",
            (timestamp,),
        )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_context_by_id(context_id: int) -> Optional[dict]:
    """Retrieve a single context by its ID."""
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, url, summary, app, workspace, timestamp FROM contexts WHERE id = ?",
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
