"""Multi-tier lookup engine with exact match, stemming, typo suggestions, and history logging."""

import difflib
import time
from typing import List, Dict, Any, Optional, Tuple
from .db import get_connection, get_entry, search_prefix, log_history, count_entries
from .builder import seed_database
from .online import fetch_online_and_cache


def stem_variations(word: str) -> List[str]:
    """Generate basic morphological variants (plurals, -ing, -ed, -ly, -ness)."""
    w = word.strip().lower()
    variants = []
    if w.endswith("ies") and len(w) > 4:
        variants.append(w[:-3] + "y")
    if w.endswith("es") and len(w) > 3:
        variants.append(w[:-2])
    if w.endswith("s") and not w.endswith("ss") and len(w) > 3:
        variants.append(w[:-1])
    if w.endswith("ing") and len(w) > 5:
        variants.append(w[:-3])
        variants.append(w[:-3] + "e")
    if w.endswith("ed") and len(w) > 4:
        variants.append(w[:-2])
        variants.append(w[:-1])
    if w.endswith("ly") and len(w) > 4:
        variants.append(w[:-2])
    return variants


def find_spelling_suggestions(query: str, limit: int = 5) -> List[str]:
    """Find close matches using multi-prefix search and difflib."""
    clean = query.strip().lower()
    if len(clean) < 2:
        return []

    candidates = set()
    # Check prefixes of various lengths (4, 3, 5)
    for prefix_len in (4, 3, 5, 2):
        if len(clean) >= prefix_len:
            prefix = clean[:prefix_len]
            matches = search_prefix(prefix, limit=60)
            candidates.update(matches)
        if len(candidates) >= 50:
            break

    if not candidates:
        return []

    # Filter out exact matches and score
    unique_candidates = [w for w in candidates if w.lower() != clean]
    close = difflib.get_close_matches(clean, unique_candidates, n=limit, cutoff=0.5)

    suggestions: List[str] = []
    seen = set()
    for s in close:
        s_lower = s.lower()
        if s_lower not in seen:
            seen.add(s_lower)
            suggestions.append(s)

    return suggestions[:limit]


def lookup_word(
    word: str,
    online_fallback: bool = True,
    record_history: bool = True
) -> Dict[str, Any]:
    """
    Search for a word definition across multiple tiers.
    Returns structured result dict.
    """
    clean_word = word.strip()
    if not clean_word:
        return {"found": False, "word": "", "entries": [], "suggestions": [], "elapsed_ms": 0.0}

    t0 = time.time()
    conn = get_connection()

    # Ensure database is initialized with at least the seed data
    if count_entries(conn) == 0:
        seed_database(conn)

    # Tier 1: Exact match in SQLite (<0.2ms)
    entries = get_entry(clean_word, conn)

    # Tier 2: Lemmatization / Stemming variants
    matched_word = clean_word
    if not entries:
        for variant in stem_variations(clean_word):
            variant_entries = get_entry(variant, conn)
            if variant_entries:
                entries = variant_entries
                matched_word = variant
                break

    # Tier 3: Local spelling suggestions (near-instant ~2ms)
    suggestions: List[str] = []
    if not entries:
        suggestions = find_spelling_suggestions(clean_word)

    # Tier 4: Online enrichment fallback (only if no local suggestions exist)
    if not entries and not suggestions and online_fallback:
        online_entries = fetch_online_and_cache(clean_word)
        if online_entries:
            entries = online_entries
            matched_word = clean_word

    elapsed_ms = (time.time() - t0) * 1000.0

    if entries:
        primary_def = entries[0]["definition"]
        primary_pos = entries[0]["pos"]
        if record_history:
            log_history(matched_word, primary_def, primary_pos, conn)

        conn.close()
        return {
            "found": True,
            "word": matched_word,
            "queried_as": clean_word,
            "entries": entries,
            "suggestions": [],
            "elapsed_ms": elapsed_ms
        }

    conn.close()
    return {
        "found": False,
        "word": clean_word,
        "entries": [],
        "suggestions": suggestions,
        "elapsed_ms": elapsed_ms
    }
