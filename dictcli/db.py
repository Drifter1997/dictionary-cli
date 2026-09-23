"""SQLite database manager with FTS5 search, WAL mode, and sub-millisecond queries."""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from .config import DB_PATH


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Create and configure an optimized SQLite connection."""
    target_path = db_path or DB_PATH
    conn = sqlite3.connect(str(target_path), timeout=5.0)
    conn.row_factory = sqlite3.Row
    # High-performance PRAGMAs
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA cache_size = -64000;")  # 64MB memory cache
    conn.execute("PRAGMA temp_store = MEMORY;")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Initialize schema: entries, FTS5 virtual table, and vocabulary history."""
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL COLLATE NOCASE,
                pos TEXT,
                phonetic TEXT,
                definition TEXT NOT NULL,
                example TEXT,
                synonyms TEXT,
                source TEXT DEFAULT 'offline'
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_entries_word ON entries(word COLLATE NOCASE);")

        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
                word,
                definition,
                tokenize='porter unicode61'
            );
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL UNIQUE COLLATE NOCASE,
                pos TEXT,
                definition TEXT,
                looked_up_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                count INTEGER DEFAULT 1,
                favorite INTEGER DEFAULT 0
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_history_time ON history(looked_up_at DESC);")


def get_entry(word: str, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
    """Fetch all definitions for a given word exact match (case-insensitive)."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True

    try:
        cur = conn.execute(
            "SELECT word, pos, phonetic, definition, example, synonyms, source FROM entries WHERE word = ? COLLATE NOCASE",
            (word.strip(),)
        )
        rows = cur.fetchall()
        results = []
        for r in rows:
            syns = []
            if r["synonyms"]:
                try:
                    syns = json.loads(r["synonyms"]) if r["synonyms"].startswith("[") else [s.strip() for s in r["synonyms"].split(",") if s.strip()]
                except Exception:
                    syns = [s.strip() for s in r["synonyms"].split(",") if s.strip()]
            results.append({
                "word": r["word"],
                "pos": r["pos"] or "",
                "phonetic": r["phonetic"] or "",
                "definition": r["definition"],
                "example": r["example"] or "",
                "synonyms": syns,
                "source": r["source"] or "offline"
            })
        return results
    finally:
        if close_after:
            conn.close()


def search_prefix(prefix: str, limit: int = 15, conn: Optional[sqlite3.Connection] = None) -> List[str]:
    """Find words starting with prefix for live autocompletion."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True

    try:
        clean = prefix.strip()
        if not clean:
            return []
        cur = conn.execute(
            "SELECT DISTINCT word FROM entries WHERE word LIKE ? ORDER BY LENGTH(word) ASC, word ASC LIMIT ?",
            (f"{clean}%", limit)
        )
        return [row[0] for row in cur.fetchall()]
    finally:
        if close_after:
            conn.close()


def search_fts(query: str, limit: int = 10, conn: Optional[sqlite3.Connection] = None) -> List[str]:
    """Search full-text search index."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True

    try:
        clean = query.strip().replace('"', '""')
        if not clean:
            return []
        cur = conn.execute(
            "SELECT DISTINCT word FROM entries_fts WHERE entries_fts MATCH ? LIMIT ?",
            (f'"{clean}"*', limit)
        )
        return [row[0] for row in cur.fetchall()]
    except sqlite3.OperationalError:
        return []
    finally:
        if close_after:
            conn.close()


def insert_entry(entry: Dict[str, Any], conn: Optional[sqlite3.Connection] = None) -> None:
    """Insert a single entry into entries and FTS table."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True

    try:
        syns_str = json.dumps(entry.get("synonyms", []))
        with conn:
            conn.execute(
                """
                INSERT INTO entries (word, pos, phonetic, definition, example, synonyms, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry["word"].strip(),
                    entry.get("pos", ""),
                    entry.get("phonetic", ""),
                    entry["definition"].strip(),
                    entry.get("example", ""),
                    syns_str,
                    entry.get("source", "offline")
                )
            )
            conn.execute(
                "INSERT INTO entries_fts (word, definition) VALUES (?, ?)",
                (entry["word"].strip(), entry["definition"].strip())
            )
    finally:
        if close_after:
            conn.close()


def insert_entries_batch(entries: List[Dict[str, Any]], conn: Optional[sqlite3.Connection] = None) -> None:
    """Bulk insert entries for maximum bootstrap speed."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True

    try:
        entries_data = []
        fts_data = []
        for e in entries:
            word = e["word"].strip()
            definition = e["definition"].strip()
            pos = e.get("pos", "")
            phonetic = e.get("phonetic", "")
            example = e.get("example", "")
            synonyms = json.dumps(e.get("synonyms", []))
            source = e.get("source", "offline")
            entries_data.append((word, pos, phonetic, definition, example, synonyms, source))
            fts_data.append((word, definition))

        with conn:
            conn.executemany(
                """
                INSERT INTO entries (word, pos, phonetic, definition, example, synonyms, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                entries_data
            )
            conn.executemany(
                "INSERT INTO entries_fts (word, definition) VALUES (?, ?)",
                fts_data
            )
    finally:
        if close_after:
            conn.close()


def count_entries(conn: Optional[sqlite3.Connection] = None) -> int:
    """Return total number of entries in the database."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True

    try:
        cur = conn.execute("SELECT COUNT(*) FROM entries")
        return cur.fetchone()[0]
    except Exception:
        return 0
    finally:
        if close_after:
            conn.close()


def log_history(word: str, definition: str, pos: str = "", conn: Optional[sqlite3.Connection] = None) -> None:
    """Log or increment lookup frequency in user's history."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True

    try:
        with conn:
            conn.execute(
                """
                INSERT INTO history (word, pos, definition, count, looked_up_at)
                VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(word) DO UPDATE SET
                    count = count + 1,
                    looked_up_at = CURRENT_TIMESTAMP,
                    definition = COALESCE(NULLIF(excluded.definition, ''), history.definition)
                """,
                (word.strip(), pos, definition.strip()[:200])
            )
    finally:
        if close_after:
            conn.close()


def get_history_entries(limit: int = 50, favorites_only: bool = False, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
    """Retrieve history records."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True

    try:
        query = "SELECT word, pos, definition, count, looked_up_at, favorite FROM history"
        params = []
        if favorites_only:
            query += " WHERE favorite = 1"
        query += " ORDER BY looked_up_at DESC LIMIT ?"
        params.append(limit)

        cur = conn.execute(query, params)
        return [dict(row) for row in cur.fetchall()]
    finally:
        if close_after:
            conn.close()


def toggle_history_favorite(word: str, conn: Optional[sqlite3.Connection] = None) -> bool:
    """Toggle favorite star for a word in history."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True

    try:
        with conn:
            cur = conn.execute("SELECT favorite FROM history WHERE word = ? COLLATE NOCASE", (word.strip(),))
            row = cur.fetchone()
            if not row:
                # Add it as a favorite
                conn.execute("INSERT INTO history (word, favorite) VALUES (?, 1)", (word.strip(),))
                return True
            new_val = 0 if row["favorite"] else 1
            conn.execute("UPDATE history SET favorite = ? WHERE word = ? COLLATE NOCASE", (new_val, word.strip()))
            return bool(new_val)
    finally:
        if close_after:
            conn.close()


def clear_history_entries(conn: Optional[sqlite3.Connection] = None) -> int:
    """Clear all lookup history."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True

    try:
        with conn:
            cur = conn.execute("DELETE FROM history")
            return cur.rowcount
    finally:
        if close_after:
            conn.close()
