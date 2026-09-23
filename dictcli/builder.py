"""Database bootstrap and dictionary dataset indexer."""

import re
import json
import time
import urllib.request
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from .config import DB_PATH, DICTIONARY_SOURCE_URL
from .db import init_db, insert_entries_batch, get_connection, count_entries

# Curated seed dictionary of gaming, fantasy, cinema, and literary words
# Loaded immediately on first run so the tool works with zero network setup
SEED_ENTRIES: List[Dict[str, Any]] = [
    {
        "word": "ephemeral",
        "pos": "adj.",
        "phonetic": "/ɪˈfɛm.ər.əl/",
        "definition": "Lasting for a very short time; transitory; fleeting.",
        "example": "The ephemeral beauty of the cherry blossoms vanished with the evening wind.",
        "synonyms": ["fleeting", "transitory", "evanescent", "short-lived", "momentary"],
        "source": "seed"
    },
    {
        "word": "sepulcher",
        "pos": "n.",
        "phonetic": "/ˈsɛp.əl.kər/",
        "definition": "A tomb, grave, or burial chamber carved into rock or made of stone.",
        "example": "The ancient hero lay entombed within a forgotten sepulcher deep in the crypt.",
        "synonyms": ["tomb", "grave", "crypt", "mausoleum", "vault"],
        "source": "seed"
    },
    {
        "word": "miasma",
        "pos": "n.",
        "phonetic": "/maɪˈæz.mə/",
        "definition": "A noxious atmosphere or vapor; an oppressive or unpleasant atmosphere.",
        "example": "A suffocating poisonous miasma drifted through the decaying swamps.",
        "synonyms": ["fume", "stench", "effluvium", "smog", "vapor"],
        "source": "seed"
    },
    {
        "word": "eldritch",
        "pos": "adj.",
        "phonetic": "/ˈɛl.drɪtʃ/",
        "definition": "Weird, sinister, or otherworldly; unearthly and eerie.",
        "example": "An eldritch screech echoed through the sunken ruins under the pale moon.",
        "synonyms": ["eerie", "unearthly", "uncanny", "spectral", "sinister"],
        "source": "seed"
    },
    {
        "word": "anathema",
        "pos": "n.",
        "phonetic": "/əˈnæθ.ə.mə/",
        "definition": "Something or someone that is vehemently disliked, cursed, or shunned.",
        "example": "To the paladins of the sacred order, necromancy was absolute anathema.",
        "synonyms": ["abomination", "curse", "bane", "outcast", "detestation"],
        "source": "seed"
    },
    {
        "word": "paladin",
        "pos": "n.",
        "phonetic": "/ˈpæl.ə.dɪn/",
        "definition": "A heroic champion of a noble cause; a holy knight upholding righteousness.",
        "example": "The lone paladin held the mountain pass against the horde until reinforcements arrived.",
        "synonyms": ["knight", "champion", "defender", "hero", "crusader"],
        "source": "seed"
    },
    {
        "word": "penumbra",
        "pos": "n.",
        "phonetic": "/pɪˈnʌm.brə/",
        "definition": "A shadowy, indistinct, or indefinite margin or border; a partially shaded area.",
        "example": "He lurked in the quiet penumbra between the lantern's glow and the darkness.",
        "synonyms": ["shadow", "shroud", "fringe", "margin", "half-light"],
        "source": "seed"
    },
    {
        "word": "chitinous",
        "pos": "adj.",
        "phonetic": "/ˈkaɪ.tɪ.nəs/",
        "definition": "Composed of or resembling chitin, a tough, protective outer exoskeleton.",
        "example": "The dungeon crawler was startled by the clatter of giant chitinous legs across stone.",
        "synonyms": ["armored", "carapaced", "crustaceous", "shelled"],
        "source": "seed"
    },
    {
        "word": "serendipity",
        "pos": "n.",
        "phonetic": "/ˌsɛr.ənˈdɪp.ɪ.ti/",
        "definition": "The occurrence of events by chance in a happy or beneficial way; fortunate discovery.",
        "example": "By pure serendipity, the wanderer uncovered a hidden chest behind the waterfall.",
        "synonyms": ["fluke", "fortune", "chance", "providence", "luck"],
        "source": "seed"
    },
    {
        "word": "sanctum",
        "pos": "n.",
        "phonetic": "/ˈsæŋk.təm/",
        "definition": "A sacred place; a private sanctuary, refuge, or retreat where one cannot be intruded upon.",
        "example": "Only high mages were granted access to the inner sanctum of the citadel.",
        "synonyms": ["sanctuary", "refuge", "haven", "retreat", "shrine"],
        "source": "seed"
    },
    {
        "word": "esoteric",
        "pos": "adj.",
        "phonetic": "/ˌɛs.əˈtɛr.ɪk/",
        "definition": "Intended for or likely to be understood by only a small number of people with specialized knowledge.",
        "example": "The grimoire was inscribed with esoteric runes decipherable only by ancient scholars.",
        "synonyms": ["abstruse", "obscure", "arcane", "cryptic", "recondite"],
        "source": "seed"
    },
    {
        "word": "petrichor",
        "pos": "n.",
        "phonetic": "/ˈpɛt.rɪˌkɔːr/",
        "definition": "A pleasant, distinctive smell that frequently accompanies the first rain after a long period of warm, dry weather.",
        "example": "As rain finally fell upon the parched earth, the sweet scent of petrichor filled the forest.",
        "synonyms": ["rain scent", "earth smell"],
        "source": "seed"
    },
    {
        "word": "apotheosis",
        "pos": "n.",
        "phonetic": "/əˌpɒθ.iˈoʊ.sɪs/",
        "definition": "The highest point in the development of something; culmination; elevation to divine status.",
        "example": "The final battle represented the dramatic apotheosis of the protagonist's journey.",
        "synonyms": ["zenith", "culmination", "deification", "pinnacle", "epitome"],
        "source": "seed"
    },
    {
        "word": "panoply",
        "pos": "n.",
        "phonetic": "/ˈpæn.ə.pli/",
        "definition": "A complete or impressive collection of things; a splendid display; a full suit of armor.",
        "example": "The warlord marched into battle adorned in a magnificent panoply of gilded plate.",
        "synonyms": ["array", "display", "spectrum", "regalia", "assortment"],
        "source": "seed"
    },
    {
        "word": "surreptitious",
        "pos": "adj.",
        "phonetic": "/ˌsɜːr.əpˈtɪʃ.əs/",
        "definition": "Kept secret, especially because it would not be approved of; stealthy.",
        "example": "The rogue made a surreptitious glance toward the guard before picking the lock.",
        "synonyms": ["stealthy", "clandestine", "furtive", "covert", "sneaky"],
        "source": "seed"
    },
    {
        "word": "vicissitude",
        "pos": "n.",
        "phonetic": "/vɪˈsɪs.ɪ.tjuːd/",
        "definition": "A change of circumstances or fortune, typically one that is unwelcome or unpleasant; ups and downs.",
        "example": "The kingdom persevered despite the cruel vicissitudes of endless war.",
        "synonyms": ["fluctuation", "shift", "reversal", "alteration", "mutation"],
        "source": "seed"
    },
    {
        "word": "lugubrious",
        "pos": "adj.",
        "phonetic": "/luːˈɡuː.bri.əs/",
        "definition": "Looking or sounding sad, dismal, or mournful.",
        "example": "The cello played a lugubrious melody that reflected the tragic fate of the fallen hero.",
        "synonyms": ["gloomy", "mournful", "dismal", "melancholy", "somber"],
        "source": "seed"
    },
    {
        "word": "supercilious",
        "pos": "adj.",
        "phonetic": "/ˌsuː.pərˈsɪl.i.əs/",
        "definition": "Behaving or looking as though one thinks one is superior to others; arrogant.",
        "example": "The corrupt nobleman cast a supercilious sneer at the peasants assembled below.",
        "synonyms": ["arrogant", "haughty", "condescending", "scornful", "pompous"],
        "source": "seed"
    },
    {
        "word": "taciturn",
        "pos": "adj.",
        "phonetic": "/ˈtæs.ɪ.tɜːrn/",
        "definition": "Reserved or uncommunicative in speech; saying little.",
        "example": "The veteran bounty hunter was a taciturn man who rarely spoke more than three words.",
        "synonyms": ["untalkative", "reticent", "silent", "quiet", "reserved"],
        "source": "seed"
    },
    {
        "word": "obviate",
        "pos": "v.",
        "phonetic": "/ˈɒb.vi.eɪt/",
        "definition": "Remove a need or difficulty; prevent or avoid.",
        "example": "Crafting the enchanted talisman obviated the need to cast protective wards daily.",
        "synonyms": ["preclude", "prevent", "eliminate", "neutralize", "forestall"],
        "source": "seed"
    }
]

POS_REGEX = re.compile(r'^(n\.|v\.|v\. t\.|v\. i\.|a\.|adj\.|adv\.|prep\.|interj\.|conj\.)\s*', re.IGNORECASE)


def parse_webster_entry(word: str, raw_text: str) -> Dict[str, Any]:
    """Parse part of speech and clean definition from raw Webster dictionary text."""
    pos = ""
    clean_text = raw_text.strip()
    match = POS_REGEX.match(clean_text)
    if match:
        raw_pos = match.group(1).lower()
        if "n." in raw_pos:
            pos = "n."
        elif "v." in raw_pos:
            pos = "v."
        elif "a." in raw_pos or "adj." in raw_pos:
            pos = "adj."
        elif "adv." in raw_pos:
            pos = "adv."
        elif "prep." in raw_pos:
            pos = "prep."
        elif "conj." in raw_pos:
            pos = "conj."
        clean_text = clean_text[match.end():].strip()

    # Clean up bracketed etymology if present at start: [OE. ...] or [L. ...]
    clean_text = re.sub(r'^\[[^\]]+\]\s*', '', clean_text).strip()

    return {
        "word": word.strip(),
        "pos": pos,
        "phonetic": "",
        "definition": clean_text,
        "example": "",
        "synonyms": [],
        "source": "webster"
    }


def seed_database(conn: sqlite3.Connection) -> None:
    """Populate database with instant starter entries if empty."""
    init_db(conn)
    current_count = count_entries(conn)
    if current_count == 0:
        insert_entries_batch(SEED_ENTRIES, conn)


def download_and_build_db(
    db_path: Optional[Path] = None,
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> int:
    """
    Download 102,000+ words Webster English Dictionary and compile into SQLite FTS5 database.
    Takes ~5-8 seconds total.
    """
    target_path = db_path or DB_PATH
    conn = get_connection(target_path)
    init_db(conn)

    if progress_callback:
        progress_callback("Connecting to dictionary repository...", 0.05)

    req = urllib.request.Request(
        DICTIONARY_SOURCE_URL,
        headers={"User-Agent": "dictionary-cli/1.0"}
    )

    t0 = time.time()
    with urllib.request.urlopen(req, timeout=30) as resp:
        content = resp.read().decode("utf-8", errors="replace")

    if progress_callback:
        progress_callback(f"Downloaded dictionary data in {time.time()-t0:.1f}s. Parsing JSON...", 0.50)

    raw_dict = json.loads(content)
    total_words = len(raw_dict)

    if progress_callback:
        progress_callback(f"Parsed {total_words:,} words. Indexing into SQLite FTS5...", 0.70)

    entries_to_insert: List[Dict[str, Any]] = []
    for word, defn in raw_dict.items():
        if word and defn:
            entries_to_insert.append(parse_webster_entry(word, defn))

    # Also include the curated seed words to ensure rich examples/phonetics
    entries_to_insert.extend(SEED_ENTRIES)

    t1 = time.time()
    insert_entries_batch(entries_to_insert, conn)

    if progress_callback:
        progress_callback(f"Indexed {len(entries_to_insert):,} entries in {time.time()-t1:.2f}s!", 1.0)

    final_count = count_entries(conn)
    conn.close()
    return final_count
