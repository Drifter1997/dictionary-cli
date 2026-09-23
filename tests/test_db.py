"""Unit tests for SQLite database layer."""

import pytest
import sqlite3
from pathlib import Path
from dictcli.db import (
    get_connection,
    init_db,
    insert_entry,
    insert_entries_batch,
    get_entry,
    search_prefix,
    count_entries,
    log_history,
    get_history_entries,
    toggle_history_favorite,
    clear_history_entries,
)


@pytest.fixture
def temp_db(tmp_path: Path):
    """Fixture to provide a temporary database."""
    db_file = tmp_path / "test_dict.db"
    conn = get_connection(db_file)
    init_db(conn)
    yield conn
    conn.close()


def test_init_and_insert_entry(temp_db: sqlite3.Connection):
    entry = {
        "word": "miasma",
        "pos": "n.",
        "phonetic": "/maɪˈæz.mə/",
        "definition": "A noxious atmosphere or vapor.",
        "example": "A miasma of dread.",
        "synonyms": ["fume", "stench"],
        "source": "test"
    }
    insert_entry(entry, conn=temp_db)

    results = get_entry("miasma", conn=temp_db)
    assert len(results) == 1
    assert results[0]["word"] == "miasma"
    assert results[0]["pos"] == "n."
    assert "noxious" in results[0]["definition"]
    assert "fume" in results[0]["synonyms"]


def test_case_insensitive_lookup(temp_db: sqlite3.Connection):
    entry = {
        "word": "Paladin",
        "pos": "n.",
        "definition": "A heroic champion.",
    }
    insert_entry(entry, conn=temp_db)

    assert len(get_entry("paladin", conn=temp_db)) == 1
    assert len(get_entry("PALADIN", conn=temp_db)) == 1
    assert len(get_entry("Paladin", conn=temp_db)) == 1


def test_search_prefix(temp_db: sqlite3.Connection):
    batch = [
        {"word": "ephemeral", "definition": "Short-lived."},
        {"word": "ephemeris", "definition": "A table of astronomical coordinates."},
        {"word": "epic", "definition": "Heroic poem."},
        {"word": "sepulcher", "definition": "A tomb."}
    ]
    insert_entries_batch(batch, conn=temp_db)

    matches = search_prefix("ephem", limit=5, conn=temp_db)
    assert "ephemeral" in matches
    assert "ephemeris" in matches
    assert "sepulcher" not in matches


def test_history_and_favorites(temp_db: sqlite3.Connection):
    log_history("eldritch", "Sinister and unearthly.", "adj.", conn=temp_db)
    log_history("eldritch", "Sinister and unearthly.", "adj.", conn=temp_db)
    log_history("sanctum", "A sacred place.", "n.", conn=temp_db)

    history = get_history_entries(limit=10, conn=temp_db)
    assert len(history) == 2

    # Verify lookup count was incremented for eldritch
    eldritch_row = next(h for h in history if h["word"] == "eldritch")
    assert eldritch_row["count"] == 2

    # Toggle favorite
    fav_state = toggle_history_favorite("eldritch", conn=temp_db)
    assert fav_state is True

    favs = get_history_entries(favorites_only=True, conn=temp_db)
    assert len(favs) == 1
    assert favs[0]["word"] == "eldritch"

    # Untoggle
    fav_state_2 = toggle_history_favorite("eldritch", conn=temp_db)
    assert fav_state_2 is False

    # Clear
    cleared = clear_history_entries(conn=temp_db)
    assert cleared == 2
    assert len(get_history_entries(conn=temp_db)) == 0
