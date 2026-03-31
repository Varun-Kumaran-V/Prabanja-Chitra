@echo off
REM Aether Constellation Manager - Backend Startup Script (Windows)
REM This script starts the FastAPI backend server

echo Starting Aether Constellation Manager Backend...
echo.

cd /d "%~dp0backend"

REM Check if virtual environment exists
if exist "..\\.venv\\Scripts\\activate.bat" (
    echo Activating virtual environment...
    call "..\.venv\Scripts\activate.bat"
)

echo Starting uvicorn server on port 8000...
echo API will be available at: http://localhost:8000
echo API docs available at: http://localhost:8000/docs
echo.

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
