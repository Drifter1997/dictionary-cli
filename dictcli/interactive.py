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
    # Don't split words on hyphens
    readline.set_completer_delims(" \t\n;")

    console.print(Panel(
        "[bold cyan]📖 Dictionary HUD[/bold cyan]\n"
        "[dim]Type any word to define. Press [bold]TAB[/bold] for autocomplete.\n"
        "Press [bold]Ctrl+C[/bold] or type [bold]q[/bold] / [bold]exit[/bold] to return to your game/movie.[/dim]",
        border_style="cyan",
        expand=False
    ))

    while True:
        try:
            query = input("\n🔍 Search: ").strip()
            if not query:
                continue

            if query.lower() in ("q", ":q", "exit", "quit"):
                console.print("[dim]Exiting dictionary HUD.[/dim]")
                break

            # Handle commands
            if query.startswith(":"):
                cmd = query[1:].lower()
                if cmd == "clear":
                    console.clear()
                    continue

            result = lookup_word(query)
            render_full(result, console=console)

        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Closed.[/dim]")
            break
