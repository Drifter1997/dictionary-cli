#!/usr/bin/env python3
"""Main entry point for dictionary-cli."""

import sys
import argparse
from pathlib import Path
from rich.console import Console

from dictcli.config import DB_PATH
from dictcli.lookup import lookup_word
from dictcli.renderer import render_full, format_compact, render_json
from dictcli.notify import handle_notification_lookup
from dictcli.interactive import run_interactive
from dictcli.history import (
    display_history,
    export_history,
    run_quiz,
)
from dictcli.db import toggle_history_favorite, clear_history_entries, count_entries, get_connection
from dictcli.builder import download_and_build_db, seed_database


def main():
    parser = argparse.ArgumentParser(
        prog="dict-cli",
        description="Fast, offline-first dictionary CLI for gaming and movie immersion."
    )

    # Word or phrase argument
    parser.add_argument("word", nargs="?", default=None, help="Word to look up in the dictionary")

    # Display & Lookup flags
    parser.add_argument("-c", "--compact", action="store_true", help="Display 1-line compact definition")
    parser.add_argument("-j", "--json", action="store_true", help="Output raw JSON format")
    parser.add_argument("--offline", action="store_true", help="Enforce pure offline local lookup (sub-millisecond, no online fallback)")

    # Immersion HUD modes
    parser.add_argument("-i", "--interactive", action="store_true", help="Launch interactive HUD with live autocompletion")
    parser.add_argument("-n", "--notify", action="store_true", help="Send definition as desktop notification (mako/dunst)")
    parser.add_argument("--clipboard", action="store_true", help="Look up selected/copied word from Wayland clipboard (wl-paste)")
    parser.add_argument("--wofi", action="store_true", help="Summon fast 1-line wofi input for notification lookup")

    # Study vault & history subcommands
    parser.add_argument("--history", action="store_true", help="Show recent lookup history")
    parser.add_argument("--favorites", action="store_true", help="Show starred favorite vocabulary")
    parser.add_argument("--favorite", type=str, metavar="WORD", help="Toggle favorite star for a word")
    parser.add_argument("--clear-history", action="store_true", help="Clear all lookup history")
    parser.add_argument("--quiz", action="store_true", help="Run a vocabulary recall quiz on recent lookups")
    parser.add_argument("--export", type=str, metavar="FILE", help="Export vocabulary vault (default: Anki flashcard format)")
    parser.add_argument("--export-format", choices=["anki", "tsv", "json"], default="anki", help="Export format (anki, tsv, json)")

    # Maintenance
    parser.add_argument("--update-db", action="store_true", help="Download and index the full 102,000+ words Webster dictionary")
    parser.add_argument("--info", action="store_true", help="Show dictionary database status and stats")

    args = parser.parse_args()
    console = Console()

    # Maintenance: Update / index DB
    if args.update_db:
        console.print("[bold cyan]📥 Updating offline dictionary database...[/bold cyan]")
        try:
            total = download_and_build_db(
                progress_callback=lambda msg, pct: console.print(f"[dim]{msg}[/dim]")
            )
            console.print(f"[bold green]✔ Successfully indexed {total:,} words into {DB_PATH}![/bold green]")
        except Exception as e:
            console.print(f"[bold red]✘ Failed to download/build dictionary:[/bold red] {e}")
            sys.exit(1)
        return

    # Maintenance: Database info
    if args.info:
        conn = get_connection()
        total = count_entries(conn)
        conn.close()
        console.print(f"[bold cyan]Dictionary CLI Info:[/bold cyan]")
        console.print(f"  Database path: [dim]{DB_PATH}[/dim]")
        console.print(f"  Total words: [bold green]{total:,}[/bold green]")
        return

    # Vault: Clear history
    if args.clear_history:
        cleared = clear_history_entries()
        console.print(f"[bold green]Cleared {cleared} history entries.[/bold green]")
        return

    # Vault: Toggle favorite
    if args.favorite:
        fav = toggle_history_favorite(args.favorite)
        status = "added to favorites ★" if fav else "removed from favorites ☆"
        console.print(f"Word '[bold cyan]{args.favorite}[/bold cyan]' {status}.")
        return

    # Vault: History view
    if args.history or args.favorites:
        display_history(limit=50, favorites_only=args.favorites)
        return

    # Vault: Vocabulary quiz
    if args.quiz:
        run_quiz()
        return

    # Vault: Export
    if args.export:
        out_path = Path(args.export)
        count = export_history(out_path, export_format=args.export_format)
        console.print(f"[bold green]✔ Exported {count} vocabulary items to {out_path} ({args.export_format})![/bold green]")
        return

    # Immersion: Notification HUD mode
    if args.notify or args.clipboard or args.wofi:
        success = handle_notification_lookup(
            word=args.word,
            from_clipboard=args.clipboard,
            from_wofi=args.wofi
        )
        if not success and not (args.clipboard or args.wofi):
            sys.exit(1)
        return

    # Immersion: Interactive mode
    if args.interactive or (not args.word and not args.history and not args.favorites):
        run_interactive()
        return

    # Direct word lookup
    if args.word:
        result = lookup_word(args.word, online_fallback=(not args.offline))

        if args.json:
            print(render_json(result))
        elif args.compact:
            print(format_compact(result))
        else:
            render_full(result, console=console)

        if not result.get("found"):
            suggs = result.get("suggestions", [])
            if suggs and sys.stdin.isatty() and not (args.json or args.compact):
                try:
                    choice = input(f"\n👉 Select option [1-{len(suggs)}] or type word (Enter to exit): ").strip()
                    if choice.isdigit():
                        idx = int(choice) - 1
                        if 0 <= idx < len(suggs):
                            chosen_word = suggs[idx]
                            res2 = lookup_word(chosen_word)
                            render_full(res2, console=console)
                            return
                    elif choice and choice.lower() not in ("q", ":q", "exit", "quit"):
                        res2 = lookup_word(choice)
                        render_full(res2, console=console)
                        return
                except (KeyboardInterrupt, EOFError):
                    pass
            sys.exit(1)


if __name__ == "__main__":
    main()
