#!/bin/bash
# رعد — موزر موت للـ systemd timers (بدون كرون)
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY="$(command -v python3.11 || command -v python3)"
case "${1:-}" in
  night)   exec "$PY" "$REPO/raad_night.py" ;;
  resolve) exec "$PY" "$REPO/raad.py" resolve ;;
  report)  exec "$PY" "$REPO/raad.py" report ;;
  update)  exec bash "$REPO/auto_update.sh" ;;
  *) echo "unknown tick: ${1:-∅} (night|resolve|report|update)"; exit 2 ;;
esac
