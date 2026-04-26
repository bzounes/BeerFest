#!/usr/bin/env bash
# Start the BeerFest app.
# Usage: ./run.sh [port]
#
# Set ADMIN_PASSWORD env var to override the default password.
# Set SECRET_KEY env var for a stable session secret.

PORT="${1:-5000}"

cd "$(dirname "$0")"

if ! command -v python3 &>/dev/null; then
  echo "Python 3 is required." >&2; exit 1
fi

if [ ! -d .venv ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate

pip install -q -r requirements.txt

mkdir -p static/uploads

echo ""
echo "  ╔══════════════════════════════════════╗"
echo "  ║  🍺  BeerFest is starting up!        ║"
echo "  ║                                      ║"
echo "  ║  Open: http://$(hostname -I | awk '{print $1}'):${PORT}      ║"
echo "  ║  Admin password: ${ADMIN_PASSWORD:-beerfest}              ║"
echo "  ╚══════════════════════════════════════╝"
echo ""

python3 app.py
