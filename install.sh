#!/bin/bash
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== ctracker install ==="
echo "Instaluję zależności Python..."
pip3 install -r "$DIR/requirements.txt" -q

echo ""
echo "Gotowe! Uruchom aplikację:"
echo "  python3 $DIR/app.py"
echo ""
echo "Przy pierwszym uruchomieniu macOS zapyta o dostęp do Keychain"
echo "(potrzebne do odczytu cookies z Chrome) — kliknij 'Allow'."
