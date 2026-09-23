# dictionary-cli 📖⚡

> A blazing-fast, offline-first dictionary CLI engineered for non-native English speakers to look up vocabulary during games and movies **without breaking immersion**.

Built with an instant SQLite FTS5 local database, sub-millisecond lookup latency, desktop notification overlays (Mako), and centered floating HUD popups (Sway + Foot).

---

## 🚀 Features

- **⚡ Sub-millisecond Offline Lookups (<0.5ms)**: Backed by SQLite FTS5 (Full-Text Search) with WAL mode and memory caching. Lookups execute in `~0.15ms` locally.
- **🎮 Zero-Immersion HUD Overlays**:
  - **Desktop Notification Overlay** (`--notify [word]`): Flashes definition via Mako/Dunst desktop notification without stealing window focus or interrupting games/movies.
  - **Screen / Subtitle Clipboard Lookup** (`--notify --clipboard`): Reads highlighted text from Wayland primary selection (`wl-paste -p`) and displays a non-intrusive notification.
  - **Sway Floating HUD** (`-i` / `--interactive`): Centered floating popup terminal (`foot --app-id=popup-dict`) with live autocompletion, closed with `Esc` or `q`.
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

Because your Sway configuration already has floating rules for `popup-.*`:
```sway
for_window [app_id="popup-.*"] floating enable, resize set 750 450, move position center
```
Pressing `Mod4+Shift+d` instantly pops up a clean, centered floating dictionary window over your game or video. Pressing `q` or `Esc` immediately closes it and restores focus!

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

### 3. Notification Overlay (Zero Focus Switch)
```bash
# Define word directly via desktop notification:
dict-cli --notify serendipity

# Define whatever text you just highlighted with mouse / subtitles:
dict-cli --notify --clipboard
```

### 4. Interactive HUD Mode
```bash
dict-cli -i
```
Type any word and press `Enter`. Press `TAB` for live autocompletion. Type `q` or press `Ctrl+C` to exit.

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
