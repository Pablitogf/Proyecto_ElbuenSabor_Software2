@echo off
REM Arranca la interfaz en http://localhost:5173 (cocina en /cocina)
cd /d "%~dp0frontend"
if not exist node_modules (
  echo Instalando dependencias...
  call npm install
)
call npm run dev
