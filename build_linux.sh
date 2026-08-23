#!/usr/bin/env bash
# =============================================================================
#  YT AZS V12.0  -  Linux Binary Builder (PyInstaller)
# =============================================================================
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo ""
echo "=========================================="
echo "  YT AZS V12.0  -  Linux Binary Builder"
echo "=========================================="
echo ""

PYTHON_BIN=$(which python3 || which python)
if [ -z "$PYTHON_BIN" ]; then
    echo "[EROARE] Python 3 nu a fost gasit!"
    exit 1
fi
echo "[OK] Python: $PYTHON_BIN"

if [ ! -d "venv" ]; then
    echo "[1/4] Creare mediu virtual (venv)..."
    "$PYTHON_BIN" -m venv venv
fi

echo "[2/4] Activare venv si instalare dependinte..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements_ytazs.txt
pip install pyinstaller

echo "[3/4] Construire executabil Linux cu PyInstaller..."
CTK_PATH=$(python -c "import customtkinter, os; print(os.path.dirname(customtkinter.__file__))")
PIL_PATH=$(python -c "import PIL, os; print(os.path.dirname(PIL.__file__))")

pyinstaller   --noconfirm   --onedir   --windowed   --name "YT-AZS"   --add-data "logo_white_PNG.png:."   --add-data "logo_black_PNG.png:."   --add-data "YT-AZS.ico:."   --add-data "$CTK_PATH:customtkinter"   --add-data "$PIL_PATH:PIL"   --hidden-import "download_engines"   --hidden-import "web_server"   --hidden-import "customtkinter"   --hidden-import "PIL._tkinter_finder"   --hidden-import "PIL.Image"   --hidden-import "yt_dlp"   --collect-all "customtkinter"   --collect-all "yt_dlp"   YT-AZS.py

chmod +x dist/YT-AZS/YT-AZS

echo "[4/4] Generare fisier .desktop pentru Linux..."
cat << DESKTOP_EOF > yt-azs.desktop
[Desktop Entry]
Name=YT AZS
Comment=Multi-Source Video & Audio Downloader
Exec=$DIR/dist/YT-AZS/YT-AZS
Icon=$DIR/YT-AZS.ico
Terminal=false
Type=Application
Categories=AudioVideo;Audio;Video;Network;
DESKTOP_EOF

chmod +x yt-azs.desktop

echo ""
echo "=========================================="
echo "  [OK] Build Linux finalizat cu succes!"
echo "  Executabil: $DIR/dist/YT-AZS/YT-AZS"
echo "  Desktop shortcut: $DIR/yt-azs.desktop"
echo "=========================================="
echo ""
