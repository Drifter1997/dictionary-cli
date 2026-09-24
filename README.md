# dictionary-cli 📖⚡

> A blazing-fast, offline-first dictionary CLI engineered for non-native English speakers to look up vocabulary during games and movies **without breaking immersion**.

Built with an instant SQLite FTS5 local database, sub-millisecond lookup latency, desktop notification overlays (Mako), and centered floating HUD popups (Sway + Foot).

---

## 🚀 Features

- **⚡ Sub-millisecond Offline Lookups (<0.5ms)**: Backed by SQLite FTS5 (Full-Text Search) with WAL mode and memory caching. Lookups execute in `~0.15ms` locally.
- **🎮 Zero-Immersion HUD Overlays**:
  - **Centered Floating HUD Popup** (`Mod4+Shift+d` / `dict-cli -i`): Centered floating popup terminal (`foot --app-id=popup-dict`) with live autocompletion, closed instantly with `Esc`, `q`, or `Enter`.
  - **Screen / Subtitle Clipboard Overlay** (`Mod4+Shift+v` / `dict-cli --notify --clipboard`): Reads highlighted text from Wayland primary selection (`wl-paste -p`) or clipboard and flashes a notification without stealing window focus.
  - **Quick Search Bar Overlay** (`Mod4+Shift+s` / `dict-cli --wofi`): 1-line fast Wofi input dialog that looks up words and displays definitions via notification overlay without interrupting fullscreen games or media.
- **📚 102,000+ Words Offline**: Bundles Webster's Unabridged Dictionary with rich literary, gaming, and cinematic vocabulary, plus automatic Wiktionary & Datamuse online fallback caching.
- **🔍 Typo-Tolerant & Morphological Search**: Handles plurals, past tense (`paladins` -> `paladin`), and generates "Did you mean?" suggestions for misheard or misspelled words.
- **🧠 Vocabulary Study Vault**:
  - Automatically logs words encountered while gaming/watching movies.
  - Export directly to **Anki flashcards** (`--export vocab.tsv --export-format anki`), TSV, or JSON.
  - Interactive terminal recall quiz (`--quiz`) to test retention.

---

## 📦 Quick Installation

```bash
cd ~/repo/dictionary-cli
./setup.sh
```

To index the full 102,000+ words Webster English dictionary (~5 seconds):
```bash
./setup.sh --full
# or anytime later:
dict-cli --update-db
```

The setup script automatically creates symlinks in `~/.local/bin/dict-cli`, so you can run `dict-cli` from any terminal or hotkey!

---

## ⌨️ Sway & Wayland Immersion Setup

Add these shortcuts to your `~/.config/sway/config`:

```sway
# 1. Centered floating dictionary HUD popup (Foot)
bindsym Mod4+Shift+d exec foot --app-id=popup-dict dict-cli -i

# 2. Instant notification overlay from highlighted text / clipboard
bindsym Mod4+Shift+v exec dict-cli --notify --clipboard

# 3. Quick 1-line Wofi search bar -> Notification
bindsym Mod4+Shift+s exec dict-cli --wofi
```

### Hotkey Behavior Breakdown

- **`Mod4+Shift+d` — Centered Floating Dictionary HUD Popup (Foot)**:
  - Opens a clean, centered floating terminal window (`foot --app-id=popup-dict`) powered by live autocompletion over your active game or movie.
  - Sway's floating window rule applies automatically:
    ```sway
    for_window [app_id="popup-.*"] floating enable, resize set 750 450, move position center
    ```
  - Type any word, press `TAB` to autocomplete, or select numbered suggestions for misspelled queries.
  - Pressing `q`, `Esc`, or `Enter` on an empty prompt immediately closes the window and restores focus to your background application.

- **`Mod4+Shift+v` — Screen / Subtitle Clipboard Lookup (Overlay Notification)**:
  - Instantly grabs whatever text or subtitle you highlighted with your cursor (Wayland primary selection via `wl-paste -p`) or standard clipboard.
  - Triggers a desktop notification via Mako / Dunst displaying the phonetic pronunciation, part of speech, definition, and example sentence.
  - **Zero Immersion Break**: Does not steal window focus, minimize fullscreen games, or interrupt video playback.

- **`Mod4+Shift+s` — Quick Wofi Search Bar Overlay (Overlay Notification)**:
  - Summons a fast, minimalist 1-line input dialog on screen (`wofi --dmenu -p "Dictionary Search:"`).
  - Type a query and hit `Enter`; the definition immediately pops up as a desktop notification without switching workspaces.
  - Hit `Esc` anytime to cancel and dismiss the search prompt.

---

## 💡 Usage Examples

### 1. Instant Word Lookup
```bash
dict-cli ephemeral
dict-cli sepulcher
dict-cli miasma
```

### 2. 1-Line Compact Mode
Ideal for rapid glances or shell scripts:
```bash
dict-cli -c eldritch
# Output: eldritch (/ˈɛl.drɪtʃ/) [adj.] • Weird, sinister, or otherworldly; unearthly and eerie.
```

### 3. Notification & Clipboard Overlays
```bash
# Define word directly via desktop notification:
dict-cli --notify serendipity

# Define whatever text you just highlighted with mouse / subtitles (Mod4+Shift+v):
dict-cli --notify --clipboard

# Quick 1-line Wofi search bar -> Notification (Mod4+Shift+s):
dict-cli --wofi
```

### 4. Interactive HUD Mode (Mod4+Shift+d)
```bash
dict-cli -i
```
Type any word and press `Enter`. Press `TAB` for live autocompletion. Type `q`, `Esc`, or press `Ctrl+C` to exit.

### 5. Vocabulary Study Vault & Anki Export
```bash
# View recent lookups and frequency
dict-cli --history

# Star a word as a favorite
dict-cli --favorite sepulcher
dict-cli --favorites

# Export vocabulary into Anki flashcard deck format
dict-cli --export ~/Documents/gaming_vocab.tsv --export-format anki

# Test your recall with a rapid 5-question terminal quiz
dict-cli --quiz
```

---

## 🛠 Command-Line Reference

| Option | Description |
|---|---|
| `<word>` | Look up definition of word |
| `-c, --compact` | 1-line compact summary |
| `-j, --json` | Output raw JSON data |
| `-i, --interactive` | Launch interactive HUD session with autocompletion |
| `-n, --notify` | Display definition via desktop notification |
| `--clipboard` | Look up word from Wayland clipboard (`wl-paste`) |
| `--wofi` | Open 1-line wofi input dialog for notification lookup |
| `--history` | Display recent lookup history table |
| `--favorites` | Display starred favorite vocabulary |
| `--favorite <word>` | Star / unstar a word in history |
| `--quiz` | Run vocabulary recall quiz on recent lookups |
| `--export <file>` | Export vocabulary vault (`anki`, `tsv`, `json`) |
| `--update-db` | Download and index full 102,000+ words dictionary |
| `--info` | Show database statistics and storage paths |
| `--clear-history` | Clear lookup history |

---

## 🧪 Running Tests

```bash
cd ~/repo/dictionary-cli
.venv/bin/pytest tests/ -v
```
