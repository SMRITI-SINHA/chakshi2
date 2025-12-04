@echo off
REM eCourts Chatbot Startup Script for Windows

echo Starting eCourts Chatbot...
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then: venv\Scripts\activate
    echo Then: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if dependencies are installed
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo Dependencies not installed!
    echo Please run: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Start the backend
echo Starting FastAPI backend on http://localhost:8000 ...
echo.
echo Backend logs:
echo ─────────────────────────────────────────────────

cd backend
start "eCourts Backend" python app.py

REM Wait for backend to start
timeout /t 3 /nobreak >nul

echo.
echo ─────────────────────────────────────────────────
echo Backend is running!
echo.
echo Open the frontend:
echo   Open frontend\index.html in your browser
echo   OR run in another terminal: cd frontend ^&^& python -m http.server 3000
echo.
echo API Documentation: http://localhost:8000/docs
echo.
echo Press any key to stop the server...
pause >nul

REM Kill the backend process
taskkill /FI "WindowTitle eq eCourts Backend*" /F
