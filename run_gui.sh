#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate
python src/interactive_gui.py
