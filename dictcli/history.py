"""Vocabulary study vault: lookup history, favorites, Anki/TSV export, and memory quiz."""

import csv
import json
import random
from pathlib import Path
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from .db import (
    get_history_entries,
    toggle_history_favorite,
    clear_history_entries,
    get_connection
)
from .lookup import lookup_word


def display_history(limit: int = 30, favorites_only: bool = False) -> None:
    """Print a clean table of looked-up words."""
    console = Console()
    entries = get_history_entries(limit=limit, favorites_only=favorites_only)

    if not entries:
        title = "Favorite Words" if favorites_only else "Lookup History"
        console.print(f"[dim]No entries found in {title.lower()}. Look up words or mark favorites to build your vocabulary vault![/dim]")
        return

    table = Table(
        title="📚 Vocabulary Study Vault" + (" (Favorites Only)" if favorites_only else ""),
        show_header=True,
        header_style="bold cyan",
        border_style="dim"
    )
    table.add_column("★", justify="center", width=3)
    table.add_column("Word", style="bold white", width=18)
    table.add_column("POS", style="green", width=8)
    table.add_column("Definition", style="dim white", ratio=2)
    table.add_column("Lookups", justify="center", width=8)
    table.add_column("Last Seen", style="dim", width=19)

    for item in entries:
        fav_icon = "[yellow]★[/yellow]" if item.get("favorite") else "[dim]☆[/dim]"
        word = item.get("word", "")
        pos = item.get("pos", "")
        defn = (item.get("definition") or "").strip().replace("\n", " ")
        if len(defn) > 75:
            defn = defn[:72] + "..."
        count = str(item.get("count", 1))
        seen = str(item.get("looked_up_at", ""))

        table.add_row(fav_icon, word, pos, defn, count, seen)

    console.print(table)


def export_history(output_path: Path, export_format: str = "anki") -> int:
    """Export history to Anki flashcards (TSV), tabular TSV, or JSON."""
    entries = get_history_entries(limit=10000, favorites_only=False)
    if not entries:
        return 0

    fmt = export_format.lower()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if fmt == "anki":
        # Format: Front (Word + POS) \t Back (Definition + Example)
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter="\t")
            for item in entries:
                word = item.get("word", "")
                pos = f"<i>({item.get('pos')})</i>" if item.get("pos") else ""
                front = f"<b>{word}</b> {pos}".strip()
                back = item.get("definition", "").strip()
                writer.writerow([front, back])
    elif fmt == "tsv":
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerow(["Word", "POS", "Definition", "Lookups", "LastSeen", "Favorite"])
            for item in entries:
                writer.writerow([
                    item.get("word", ""),
                    item.get("pos", ""),
                    item.get("definition", ""),
                    item.get("count", 1),
                    item.get("looked_up_at", ""),
                    item.get("favorite", 0)
                ])
    else:  # json
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2)

    return len(entries)


def run_quiz() -> None:
    """A rapid-fire vocabulary flashcard review quiz in the terminal."""
    console = Console()
    entries = get_history_entries(limit=100)
    # Require at least 4 entries for multiple choice quiz
    if len(entries) < 4:
        console.print("[yellow]You need at least 4 words in your history to take a quiz![/yellow]")
        console.print("[dim]Look up a few words first using `dict-cli <word>`.[/dim]")
        return

    sample_size = min(5, len(entries))
    quiz_items = random.sample(entries, sample_size)
    score = 0

    console.print(Panel(
        f"[bold cyan]🎯 Vocabulary Review Quiz[/bold cyan]\nTest your recall on {sample_size} words you recently encountered!",
        border_style="cyan"
    ))

    all_words = [e["word"] for e in entries]

    for idx, target in enumerate(quiz_items, 1):
        target_word = target["word"]
        target_def = target.get("definition", "").strip()
        if not target_def:
            continue

        # Pick 3 distractors
        distractors = [w for w in all_words if w.lower() != target_word.lower()]
        options = random.sample(distractors, min(3, len(distractors))) + [target_word]
        random.shuffle(options)

        console.print(f"\n[bold white]Question {idx}/{sample_size}:[/bold white]")
        console.print(f"[dim]Definition:[/dim] [italic yellow]\"{target_def}\"[/italic yellow]\n")

        for opt_idx, opt in enumerate(options, 1):
            console.print(f"  [bold cyan]{opt_idx})[/bold cyan] {opt}")

        choice = Prompt.ask("\nYour choice (1-4)", choices=["1", "2", "3", "4", "q"])
        if choice == "q":
            console.print("[dim]Quiz cancelled.[/dim]")
            return

        chosen_word = options[int(choice) - 1]
        if chosen_word.lower() == target_word.lower():
            console.print("[bold green]✔ Correct![/bold green]")
            score += 1
        else:
            console.print(f"[bold red]✘ Incorrect.[/bold red] The word was: [bold cyan]{target_word}[/bold cyan]")

    console.print(f"\n[bold green]🏆 Quiz Complete![/bold green] Your score: [bold]{score}/{sample_size}[/bold]\n")
