"""Terminal rendering using Rich for beautiful, distraction-free output."""

import json
from typing import Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from .config import (
    THEME_TITLE, THEME_POS, THEME_DEF, THEME_EXAMPLE,
    THEME_SYNONYMS, THEME_MUTED, THEME_BORDER
)


def format_compact(result: Dict[str, Any]) -> str:
    """Format a result into a single concise line."""
    if not result.get("found"):
        suggs = result.get("suggestions", [])
        if suggs:
            return f"Not found: '{result.get('word')}'. Did you mean: {', '.join(suggs)}?"
        return f"Not found: '{result.get('word')}'"

    entries = result.get("entries", [])
    if not entries:
        return f"{result.get('word')}: (No definitions)"

    first = entries[0]
    word = result.get("word", "")
    pos = f"[{first.get('pos')}] " if first.get("pos") else ""
    phonetic = f"({first.get('phonetic')}) " if first.get("phonetic") else ""
    defn = first.get("definition", "").strip().replace("\n", " ")
    return f"{word} {phonetic}{pos}• {defn}"


def render_full(result: Dict[str, Any], console: Optional[Console] = None) -> None:
    """Render full structured card in the terminal with rich panels."""
    if console is None:
        console = Console()

    if not result.get("found"):
        word = result.get("word", "")
        elapsed = result.get("elapsed_ms", 0.0)
        suggs = result.get("suggestions", [])

        title_text = Text(f" Word Not Found: '{word}' ", style="bold red")
        content = Text()
        content.append(f"No definition found for '{word}' (looked up in {elapsed:.1f}ms).\n\n", style="dim")

        if suggs:
            content.append("Did you mean?\n", style="bold yellow")
            for i, s in enumerate(suggs, 1):
                content.append(f"  [{i}] ", style="bold green")
                content.append(f"{s}\n", style="bold white")
            content.append("\n(Type the number to view definition, or enter a new word)", style="dim italic")

        console.print(Panel(content, title=title_text, border_style="red", expand=False))
        return

    word = result.get("word", "")
    elapsed = result.get("elapsed_ms", 0.0)
    entries = result.get("entries", [])[:3]  # Keep concise: top 3 most relevant definitions

    # Header
    first_entry = entries[0]
    phonetic = first_entry.get("phonetic", "")
    header_text = Text()
    header_text.append(f" {word} ", style="bold cyan")
    if phonetic:
        header_text.append(f" {phonetic} ", style="italic bright_black")
    header_text.append(f" ⚡ {elapsed:.1f}ms ", style="dim green")

    # Body
    body_text = Text()

    for idx, entry in enumerate(entries, 1):
        pos = entry.get("pos", "")
        defn = entry.get("definition", "").strip()
        example = entry.get("example", "").strip()
        synonyms = entry.get("synonyms", [])

        # Part of speech badge
        if pos:
            body_text.append(f"[{pos.upper()}] ", style="bold green")
        body_text.append(f"{defn}\n", style="bold white")

        # Example if available
        if example:
            body_text.append(f"  • Example: \"{example}\"\n", style="italic bright_black")

        # Synonyms if available
        if synonyms:
            body_text.append(f"  • Synonyms: {', '.join(synonyms[:4])}\n", style="dim yellow")
        
        if idx < len(entries):
            body_text.append("\n")

    console.print(Panel(body_text, title=header_text, border_style="cyan", expand=False))


def render_json(result: Dict[str, Any]) -> str:
    """Return JSON representation."""
    return json.dumps(result, indent=2)
