@echo off
cd /d "%~dp0"
echo ============================================
echo   IBVAP - Starting edge API
echo ============================================
python -m pip install fastapi "uvicorn[standard]" pydantic -q
echo.
echo Server: http://127.0.0.1:8000
echo Keep this window OPEN. Browser: http://127.0.0.1:8000
echo Press CTRL+C to stop.
echo.
python -m uvicorn main:app --host 127.0.0.1 --port 8000
pause
