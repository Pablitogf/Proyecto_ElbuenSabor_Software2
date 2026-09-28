#!/usr/bin/env bash
# Arranca la interfaz en http://localhost:5173 (cocina en /cocina)
set -e
cd "$(dirname "$0")/frontend"
[ -d node_modules ] || npm install
npm run dev
