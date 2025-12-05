@echo off
title eCourts Chatbot - Simple Run (No venv)
color 0A

echo.
echo ========================================
echo   eCourts Chatbot - Simple Setup
echo   (Installs globally, no venv issues!)
echo ========================================
echo.

cd /d "%~dp0"

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Install from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python installed:
python --version
echo.

REM Install dependencies globally
echo [SETUP] Installing packages globally...
echo This takes 2-3 minutes...
echo.

pip install fastapi==0.109.0 uvicorn==0.27.0 playwright==1.41.0 pydantic==2.5.3 python-dotenv==1.0.0 aiofiles==23.2.1 python-multipart==0.0.6

if errorlevel 1 (
    echo [ERROR] Installation failed
    pause
    exit /b 1
)

echo [OK] Packages installed
echo.

REM Install Playwright browser
echo [SETUP] Installing Playwright browser...
echo This takes 5-10 minutes...
echo.

python -m playwright install chromium

echo [OK] Setup complete!
echo.

echo ========================================
echo     Starting Backend Server...
echo ========================================
echo.
echo [INFO] Backend: http://localhost:8000
echo [INFO] Docs: http://localhost:8000/docs
echo.
echo [NEXT] Open: frontend\index.html
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

cd backend
python app.py

pause
