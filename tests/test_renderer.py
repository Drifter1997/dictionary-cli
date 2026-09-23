"""Unit tests for output formatting."""

import json
from dictcli.renderer import format_compact, render_json


def test_format_compact():
    sample_result = {
        "found": True,
        "word": "miasma",
        "entries": [
            {
                "word": "miasma",
                "pos": "n.",
                "phonetic": "/maɪˈæz.mə/",
                "definition": "A noxious atmosphere or vapor.",
                "example": "",
                "synonyms": [],
                "source": "seed"
            }
        ]
    }
    compact = format_compact(sample_result)
    assert "miasma" in compact
    assert "[n.]" in compact
    assert "/maɪˈæz.mə/" in compact
    assert "noxious" in compact


def test_format_compact_not_found():
    sample_not_found = {
        "found": False,
        "word": "xyzabc",
        "suggestions": ["xyz", "abc"]
    }
    compact = format_compact(sample_not_found)
    assert "Not found: 'xyzabc'" in compact
    assert "xyz, abc" in compact


def test_render_json():
    sample_result = {
        "found": True,
        "word": "eldritch",
        "entries": []
    }
    raw_json = render_json(sample_result)
    parsed = json.loads(raw_json)
    assert parsed["word"] == "eldritch"
    assert parsed["found"] is True
