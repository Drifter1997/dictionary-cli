"""Unit tests for vocabulary study vault and exports."""

import json
from pathlib import Path
from dictcli.db import log_history, clear_history_entries
from dictcli.history import export_history, get_history_entries


def test_export_anki(tmp_path: Path):
    clear_history_entries()
    log_history("serendipity", "Fortunate discovery.", "n.")
    log_history("petrichor", "Smell of earth after rain.", "n.")

    export_file = tmp_path / "vocab_anki.tsv"
    count = export_history(export_file, export_format="anki")
    assert count == 2
    assert export_file.exists()

    content = export_file.read_text(encoding="utf-8")
    assert "serendipity" in content
    assert "petrichor" in content
    assert "\t" in content


def test_export_tsv(tmp_path: Path):
    clear_history_entries()
    log_history("esoteric", "Understood by few.", "adj.")

    export_file = tmp_path / "vocab.tsv"
    count = export_history(export_file, export_format="tsv")
    assert count == 1

    content = export_file.read_text(encoding="utf-8")
    lines = content.strip().split("\n")
    assert len(lines) == 2  # header + 1 row
    assert lines[0].startswith("Word\tPOS")
    assert "esoteric" in lines[1]


def test_export_json(tmp_path: Path):
    clear_history_entries()
    log_history("panoply", "Splendid display.", "n.")

    export_file = tmp_path / "vocab.json"
    count = export_history(export_file, export_format="json")
    assert count == 1

    data = json.loads(export_file.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data[0]["word"] == "panoply"
