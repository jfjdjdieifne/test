#!/bin/bash
set -e
set -o allexport
[ -f "$HOME/jarvis-ceo.env" ] && . "$HOME/jarvis-ceo.env"
set +o allexport
cd "$(dirname "$0")"
exec python3 agent.py
