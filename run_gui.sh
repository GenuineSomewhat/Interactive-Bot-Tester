#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate
# Run the GUI in the background and detach from terminal
python src/interactive_gui.py "$1" &
disown
