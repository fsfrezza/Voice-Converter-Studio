@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python nao encontrado. Instale Python 3.11 ou superior.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  if errorlevel 1 goto :error
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :error
start "" cmd /c "timeout /t 4 /nobreak >nul & start http://127.0.0.1:8765"
echo Voice Converter: http://127.0.0.1:8765
echo Para encerrar, pressione Ctrl+C.
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8765
exit /b %errorlevel%
:error
echo Falha ao preparar o programa.
pause
exit /b 1
