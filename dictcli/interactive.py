"""Interactive TUI / HUD mode with live prefix autocompletion for floating popup windows."""

import sys
import readline
from typing import List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from .db import search_prefix, get_connection
from .lookup import lookup_word
from .renderer import render_full


class WordCompleter:
    """Readline tab-completer backed by SQLite prefix search."""

    def __init__(self):
        self.matches: List[str] = []

    def complete(self, text: str, state: int) -> Optional[str]:
        if state == 0:
            if text:
                conn = get_connection()
                self.matches = search_prefix(text, limit=10, conn=conn)
                conn.close()
            else:
                self.matches = []
        try:
            return self.matches[state]
        except IndexError:
            return None


def run_interactive() -> None:
    """Launch the interactive dictionary HUD session."""
    console = Console()

    # Configure readline for fast autocomplete
    completer = WordCompleter()
    readline.set_completer(completer.complete)
    readline.parse_and_bind("tab: complete")
    readline.set_completer_delims(" \t\n;")

    last_suggestions: List[str] = []

    console.clear()
    console.print(
        "[bold cyan]📖 Quick Dictionary HUD[/bold cyan] [dim](TAB for autocomplete • Enter or 'q' to close)[/dim]"
    )

    while True:
        try:
            if last_suggestions:
                prompt_label = f"\n👉 Choice [1-{len(last_suggestions)}] or word: "
            else:
                prompt_label = "\n🔍 Word: "

            query = input(prompt_label).strip()

            # Empty input closes the window immediately
            if not query or query.lower() in ("q", ":q", "exit", "quit"):
                break

            # If user entered a number selecting from suggestions
            if query.isdigit() and last_suggestions:
                choice_idx = int(query) - 1
                if 0 <= choice_idx < len(last_suggestions):
                    target_word = last_suggestions[choice_idx]
                    last_suggestions = []
                    console.clear()
                    result = lookup_word(target_word)
                    render_full(result, console=console)
                    continue

            # Standard word query
            console.clear()
            result = lookup_word(query)
            render_full(result, console=console)

            if not result.get("found"):
                last_suggestions = result.get("suggestions", [])
            else:
                last_suggestions = []

        except (KeyboardInterrupt, EOFError):
            break
