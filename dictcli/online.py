"""Graceful online fallback enrichment via Wiktionary and Datamuse with SQLite auto-caching."""

import re
import json
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional
from .config import ONLINE_TIMEOUT_SECONDS
from .db import insert_entry, get_connection

HTML_TAG_REGEX = re.compile(r'<[^>]+>')


def clean_html(text: str) -> str:
    """Strip HTML markup from API responses."""
    cleaned = HTML_TAG_REGEX.sub('', text)
    return " ".join(cleaned.split()).strip()


def fetch_from_wiktionary(word: str) -> List[Dict[str, Any]]:
    """Fetch structured word definition from Wiktionary REST API."""
    encoded_word = urllib.parse.quote(word.strip().lower())
    url = f"https://en.wiktionary.org/api/rest_v1/page/definition/{encoded_word}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "dictionary-cli/1.0 (offline-first CLI tool)"}
    )

    try:
        with urllib.request.urlopen(req, timeout=ONLINE_TIMEOUT_SECONDS) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        entries = []
        en_sections = data.get("en", [])
        for section in en_sections:
            pos = section.get("partOfSpeech", "").lower()
            definitions = section.get("definitions", [])
            for d in definitions:
                raw_def = d.get("definition", "")
                clean_def = clean_html(raw_def)
                if not clean_def or len(clean_def) < 3:
                    continue

                example = ""
                examples = d.get("examples", [])
                if examples:
                    example = clean_html(examples[0])

                entries.append({
                    "word": word.strip().lower(),
                    "pos": pos,
                    "phonetic": "",
                    "definition": clean_def,
                    "example": example,
                    "synonyms": [],
                    "source": "wiktionary"
                })
        return entries
    except Exception:
        return []


def fetch_from_datamuse(word: str) -> List[Dict[str, Any]]:
    """Fallback fetch from Datamuse dictionary API."""
    encoded_word = urllib.parse.quote(word.strip().lower())
    url = f"https://api.datamuse.com/words?sp={encoded_word}&md=dpfs"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "dictionary-cli/1.0"}
    )

    try:
        with urllib.request.urlopen(req, timeout=ONLINE_TIMEOUT_SECONDS) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if not data:
            return []

        item = data[0]
        if item.get("word", "").lower() != word.strip().lower():
            return []

        defs = item.get("defs", [])
        entries = []
        for d in defs:
            # Format: 'n\tdefinition text'
            pos = ""
            defn = d
            if "\t" in d:
                parts = d.split("\t", 1)
                pos = parts[0] + "."
                defn = parts[1]

            entries.append({
                "word": word.strip().lower(),
                "pos": pos,
                "phonetic": "",
                "definition": clean_html(defn),
                "example": "",
                "synonyms": [],
                "source": "datamuse"
            })
        return entries
    except Exception:
        return []


def fetch_online_and_cache(word: str) -> List[Dict[str, Any]]:
    """Attempt online fetch and automatically cache into SQLite database."""
    # Try Wiktionary first
    results = fetch_from_wiktionary(word)
    if not results:
        results = fetch_from_datamuse(word)

    if results:
        # Cache to local SQLite so subsequent queries take 0.1ms
        try:
            conn = get_connection()
            for entry in results:
                insert_entry(entry, conn)
            conn.close()
        except Exception:
            pass

    return results
