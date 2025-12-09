@echo off
echo ========================================
echo Quick Database Connection Test
echo ========================================
echo.

cd /d "c:\Project GameWeb\backend"
call venv\Scripts\activate
python test_db.py

echo.
pause
