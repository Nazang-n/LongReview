@echo off
echo ========================================
echo Testing Backend Database Connection
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Activating virtual environment...
call venv\Scripts\activate

echo.
echo [2/3] Testing database connection...
python test_db.py

echo.
echo [3/3] Starting FastAPI server...
echo.
echo Server will run at: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

uvicorn app.main:app --reload --port 8000

pause
