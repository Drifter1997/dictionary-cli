"""Configuration paths and defaults for dictionary-cli."""

import os
from pathlib import Path

# Base paths
HOME_DIR = Path.home()
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", HOME_DIR / ".config")) / "dictionary-cli"
DATA_DIR = Path(os.environ.get("XDG_DATA_HOME", HOME_DIR / ".local" / "share")) / "dictionary-cli"

# Ensure directories exist
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# File locations
DB_PATH = DATA_DIR / "dictionary.db"
CONFIG_FILE = CONFIG_DIR / "config.json"
HISTORY_FILE = DATA_DIR / "history.json"

# Remote dictionary dataset for bootstrap
DICTIONARY_SOURCE_URL = "https://raw.githubusercontent.com/matthewreagan/WebstersEnglishDictionary/master/dictionary.json"

# UI Defaults
NOTIFICATION_TIMEOUT_MS = 6000
NOTIFICATION_APP_NAME = "Dictionary"
ONLINE_TIMEOUT_SECONDS = 1.5

# Visual Colors (Rich terminal theme)
THEME_TITLE = "bold cyan"
THEME_POS = "bold green"
THEME_DEF = "white"
THEME_EXAMPLE = "italic bright_black"
THEME_SYNONYMS = "yellow"
THEME_MUTED = "dim"
THEME_BORDER = "cyan"
