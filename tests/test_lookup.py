"""Unit tests for lookup engine and morphology/spelling suggestions."""

import pytest
from dictcli.lookup import stem_variations, find_spelling_suggestions, lookup_word
from dictcli.db import get_connection, insert_entries_batch


def test_stem_variations():
    assert "sepulcher" in stem_variations("sepulchers")
    assert "ephemeral" in stem_variations("ephemerally")
    assert "paladin" in stem_variations("paladins")


def test_seed_lookup():
    result = lookup_word("ephemeral", online_fallback=False, record_history=False)
    assert result["found"] is True
    assert result["word"] == "ephemeral"
    assert len(result["entries"]) >= 1
    assert "transitory" in result["entries"][0]["definition"].lower() or "short" in result["entries"][0]["definition"].lower()


def test_stemmed_lookup():
    # Looking up "paladins" should find "paladin"
    result = lookup_word("paladins", online_fallback=False, record_history=False)
    assert result["found"] is True
    assert result["word"] == "paladin"


def test_typo_suggestions():
    # Misspelled word should return spelling suggestions
    result = lookup_word("ephemral", online_fallback=False, record_history=False)
    assert result["found"] is False
    assert len(result["suggestions"]) > 0
    assert any("ephem" in s for s in result["suggestions"])
