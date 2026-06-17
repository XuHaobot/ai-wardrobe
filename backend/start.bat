@echo off
chcp 65001 >nul 2>&1

echo ================================
echo   AI Outfit - Python Backend
echo ================================
echo.

cd /d "%~dp0"

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH
    pause
    exit /b 1
)

REM Create venv if not exists
if not exist "venv\Scripts\activate.bat" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

REM Activate venv
call "venv\Scripts\activate.bat"

REM Install dependencies
echo [INFO] Installing dependencies...
pip install -r requirements.txt -q

REM Ensure directories exist
if not exist "data" mkdir data
if not exist "uploads" mkdir uploads

echo.
echo [INFO] Starting FastAPI on port 8080...
echo [INFO] API docs: http://localhost:8080/docs
echo.
python -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload
