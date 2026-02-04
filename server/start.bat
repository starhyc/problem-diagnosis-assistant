@echo off
echo ========================================
echo AIOps Diagnosis Platform - Backend Server
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not detected. Please install Python 3.8+
    pause
    exit /b 1
)

echo [1/4] Checking virtual environment...
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/4] Installing dependencies...
pip install -r requirements.txt -q

echo [4/4] Initializing database...
python init_db.py

echo.
echo ========================================
echo Starting FastAPI server...
echo ========================================
echo.
echo API Documentation: http://localhost:8000/docs
echo Press Ctrl+C to stop the server
echo.

uvicorn main:app --reload --host 0.0.0.0 --port 8000
