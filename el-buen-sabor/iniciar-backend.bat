@echo off
REM Arranca la API en http://localhost:8000 (documentacion en /docs)
cd /d "%~dp0backend"
if not exist .venv (
  echo Creando entorno virtual...
  python -m venv .venv
)
call .venv\Scripts\activate
pip install -q -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
