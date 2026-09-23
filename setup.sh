#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

echo "=================================================="
echo "      dictionary-cli Setup & Bootstrap           "
echo "=================================================="

# Check Python version
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 is not installed. Please install Python 3.10+."
    exit 1
fi

echo -n "Checking Python version... "
python3 --version

# Check Wayland & Desktop Integration Tools
echo -n "Checking for notify-send (mako/dunst)... "
if command -v notify-send >/dev/null 2>&1; then
    echo "found"
else
    echo "WARNING: notify-send not found. Desktop notification HUD will be disabled."
fi

echo -n "Checking for wl-paste (Wayland clipboard)... "
if command -v wl-paste >/dev/null 2>&1; then
    echo "found"
else
    echo "WARNING: wl-paste not found. Clipboard auto-lookup will be disabled."
fi

echo -n "Checking for foot terminal... "
if command -v foot >/dev/null 2>&1; then
    echo "found"
else
    echo "INFO: foot not found. Any terminal can still run interactive HUD."
fi

echo -n "Checking for wofi... "
if command -v wofi >/dev/null 2>&1; then
    echo "found"
else
    echo "INFO: wofi not found. Standard CLI & notification lookup available."
fi

# Create virtual environment if needed
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python virtual environment in $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

echo "Installing dependencies..."
"$VENV_DIR/bin/pip" install --upgrade pip --quiet
"$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt" --quiet

chmod +x "$SCRIPT_DIR/dict-cli" "$SCRIPT_DIR/setup.sh"

# Initialize local database
echo "Bootstrapping offline SQLite dictionary database..."
"$VENV_DIR/bin/python" -c "
from dictcli.db import get_connection
from dictcli.builder import seed_database
conn = get_connection()
seed_database(conn)
conn.close()
print('Starter vocabulary seeded successfully.')
"

# Option to download full 102k dictionary
if [ "$1" == "--full" ] || [ "$FULL_DB" == "1" ]; then
    echo "Downloading and indexing full 102,000+ words Webster dictionary (takes ~5s)..."
    "$VENV_DIR/bin/python" "$SCRIPT_DIR/main.py" --update-db
fi

# Symlink to ~/.local/bin
mkdir -p "$HOME/.local/bin"
ln -sf "$SCRIPT_DIR/dict-cli" "$HOME/.local/bin/dict-cli"
ln -sf "$SCRIPT_DIR/dict-cli" "$HOME/.local/bin/dictionary-cli"
echo "Created symlinks in ~/.local/bin/ (dict-cli, dictionary-cli)"

echo ""
echo "=================================================="
echo "        Setup completed successfully!             "
echo "=================================================="
echo ""
echo "Quick start:"
echo "  dict-cli ephemeral                # Instant lookup"
echo "  dict-cli -c miasma                # 1-line compact mode"
echo "  dict-cli -i                       # Interactive search HUD"
echo "  dict-cli --notify [word]          # Mako notification overlay"
echo "  dict-cli --notify --clipboard     # Lookup highlighted word from screen"
echo "  dict-cli --update-db              # Index full 102,000+ words dictionary"
echo ""
echo "Recommended Sway keybindings (~/.config/sway/config):"
echo '  bindsym Mod4+Shift+d exec foot --app-id=popup-dict dict-cli -i'
echo '  bindsym Mod4+Shift+v exec dict-cli --notify --clipboard'
echo ""
