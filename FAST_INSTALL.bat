@echo off
title eCourts Chatbot - Fast Install
color 0A

echo.
echo ========================================
echo   eCourts Chatbot - Fast Install
echo   (Using latest compatible versions)
echo ========================================
echo.

cd /d "%~dp0"

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)

echo [OK] Python installed:
python --version
echo.

REM Upgrade pip first
echo [SETUP] Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install dependencies with latest versions (have Python 3.14 wheels)
echo [SETUP] Installing packages (fast version)...
echo.

pip install fastapi uvicorn[standard] playwright pydantic python-dotenv aiofiles python-multipart

if errorlevel 1 (
    echo [ERROR] Installation failed
    pause
    exit /b 1
)

echo [OK] Packages installed!
echo.

REM Install Playwright browser
echo [SETUP] Installing Playwright browser...
echo This takes 3-5 minutes...
echo.

python -m playwright install chromium

echo [OK] Setup complete!
echo.

echo ========================================
echo     Starting Backend...
echo ========================================
echo.
echo [INFO] Backend: http://localhost:8000
echo.
echo [NEXT] Open: frontend\index.html in your browser
echo       to search CNR: DLND010019612022
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

cd backend
python app.py

pause
