#!/usr/bin/env bash
# Arranca la API en http://localhost:8000 (documentación en /docs)
set -e
cd "$(dirname "$0")/backend"
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
