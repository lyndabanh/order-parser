#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INPUT_DIR="$SCRIPT_DIR/input"
PYTHON_SCRIPT="$SCRIPT_DIR/parse_orders.py"
PYTHON="$SCRIPT_DIR/venv/bin/python3"

# make this script executable on first run
chmod +x "$0"

echo "================================================"
echo "  Gardner Media Order Parser"
echo "================================================"
echo ""

if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "First time setup, installing dependencies..."
    echo "This may take a minute."
    echo ""
    python3 -m venv "$SCRIPT_DIR/venv"
    "$SCRIPT_DIR/venv/bin/pip" install -r "$SCRIPT_DIR/requirements.txt" --quiet
    echo "Setup complete!"
    echo ""
fi

if [ ! -d "$INPUT_DIR" ]; then
    echo "ERROR: No 'input' folder found."
    echo "Please create a folder called 'input' next to this script"
    echo "and put your PDF files in it."
    echo ""
    read -p "Press Enter to close..."
    exit 1
fi

PDF_COUNT=$(ls "$INPUT_DIR"/*.pdf 2>/dev/null | wc -l)
if [ "$PDF_COUNT" -eq 0 ]; then
    echo "ERROR: No PDF files found in the 'input' folder."
    echo ""
    read -p "Press Enter to close..."
    exit 1
fi

"$PYTHON" "$PYTHON_SCRIPT" "$INPUT_DIR"

echo ""
echo "================================================"
read -p "Press Enter to close..."
