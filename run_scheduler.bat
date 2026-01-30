@echo off
REM InstaGenerate - Start daily scheduler (run at Windows login or keep open)
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe run_daily.py
) else (
    python run_daily.py
)
pause
