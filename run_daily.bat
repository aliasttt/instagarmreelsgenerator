@echo off
REM InstaGenerate - Fully automated daily run. No UI. No pause. No console output.
REM Task Scheduler runs this at scheduled time.
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" run_daily.py >nul 2>&1
) else (
    python run_daily.py >nul 2>&1
)
exit /b 0
