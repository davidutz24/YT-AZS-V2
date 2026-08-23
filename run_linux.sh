#!/usr/bin/env bash
# =============================================================================
#  YT AZS V12.0  -  Linux Runner
# =============================================================================
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

PYTHON_BIN=$(which python3 || which python)

if [ ! -d "venv" ]; then
    echo "[YT-AZS] Configurare mediu virtual..."
    "$PYTHON_BIN" -m venv venv
    source venv/bin/activate
    pip install -r requirements_ytazs.txt
else
    source venv/bin/activate
fi

if [ "$1" == "--web" ] || [ -z "$DISPLAY" -a -z "$WAYLAND_DISPLAY" ]; then
    echo "[YT-AZS] Pornire in mod Web Browser..."
    python3 YT-AZS.py --web
else
    python3 YT-AZS.py "$@"
fi
