"""Wayland & desktop notification HUD integration for zero-immersion-break lookups."""

import subprocess
import shutil
import re
from typing import Optional, Dict, Any
from .config import NOTIFICATION_TIMEOUT_MS, NOTIFICATION_APP_NAME
from .lookup import lookup_word


def get_clipboard_text(primary: bool = True) -> Optional[str]:
    """Retrieve text from Wayland clipboard or primary selection (highlighted text)."""
    # Prefer wl-paste on Wayland
    if shutil.which("wl-paste"):
        cmd = ["wl-paste"]
        if primary:
            cmd.append("--primary")
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=1.0)
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass

        # If primary was empty, try standard clipboard
        if primary:
            try:
                res = subprocess.run(["wl-paste"], capture_output=True, text=True, timeout=1.0)
                if res.returncode == 0 and res.stdout.strip():
                    return res.stdout.strip()
            except Exception:
                pass

    # Fallback to xclip if on X11
    if shutil.which("xclip"):
        sel = "primary" if primary else "clipboard"
        try:
            res = subprocess.run(["xclip", "-o", "-selection", sel], capture_output=True, text=True, timeout=1.0)
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass

    return None


def extract_search_word(text: str) -> str:
    """Extract a single clean word from raw clipboard text."""
    # Take first word or line
    tokens = re.findall(r"[a-zA-Z\-']+", text)
    if tokens:
        return tokens[0]
    return text.strip()


def send_notification(summary: str, body: str, timeout_ms: int = NOTIFICATION_TIMEOUT_MS) -> bool:
    """Send a desktop notification via notify-send (mako/dunst)."""
    if not shutil.which("notify-send"):
        return False

    cmd = [
        "notify-send",
        "-a", NOTIFICATION_APP_NAME,
        "-t", str(timeout_ms),
        "-i", "accessories-dictionary",
        "-u", "normal",
        summary,
        body
    ]
    try:
        subprocess.run(cmd, check=True, timeout=2.0)
        return True
    except Exception:
        return False


def prompt_wofi() -> Optional[str]:
    """Summon a fast single-line wofi input dialog to type a word."""
    if not shutil.which("wofi"):
        return None

    cmd = ["wofi", "--dmenu", "-p", "Dictionary Search:", "--lines", "1", "--width", "400"]
    try:
        res = subprocess.run(cmd, input="", capture_output=True, text=True, timeout=15.0)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass
    return None


def handle_notification_lookup(
    word: Optional[str] = None,
    from_clipboard: bool = False,
    from_wofi: bool = False
) -> bool:
    """Execute lookup and display definition as an overlay notification."""
    target_word = word

    if from_wofi:
        target_word = prompt_wofi()
        if not target_word:
            return False

    if from_clipboard or not target_word:
        clip = get_clipboard_text(primary=True)
        if clip:
            target_word = extract_search_word(clip)

    if not target_word:
        send_notification("Dictionary", "No word selected or copied in clipboard.")
        return False

    result = lookup_word(target_word)

    if result.get("found"):
        matched_word = result.get("word", target_word)
        entries = result.get("entries", [])
        first_entry = entries[0]
        pos = first_entry.get("pos", "")
        phonetic = first_entry.get("phonetic", "")
        defn = first_entry.get("definition", "").strip()

        # Format summary line
        summary_parts = [matched_word]
        if phonetic:
            summary_parts.append(phonetic)
        if pos:
            summary_parts.append(f"[{pos}]")
        summary = " ".join(summary_parts)

        # Body: definition + example
        body_parts = [defn]
        example = first_entry.get("example", "").strip()
        if example:
            body_parts.append(f"\nEx: \"{example}\"")

        send_notification(summary, "\n".join(body_parts))
        return True
    else:
        suggs = result.get("suggestions", [])
        if suggs:
            send_notification(
                f"Word Not Found: '{target_word}'",
                f"Did you mean: {', '.join(suggs)}?"
            )
        else:
            send_notification("Word Not Found", f"No definition found for '{target_word}'.")
        return False
