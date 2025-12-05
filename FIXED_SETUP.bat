@echo off
title eCourts Chatbot - Fixed Setup
color 0A

echo.
echo ========================================
echo     eCourts Chatbot - Setup (Fixed)
echo ========================================
echo.

cd /d "%~dp0"

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    pause
    exit /b 1
)

echo [OK] Python is installed:
python --version
echo.

REM Remove old broken venv
if exist "venv\" (
    echo [CLEANUP] Removing old virtual environment...
    rmdir /s /q venv 2>nul
    echo [OK] Cleaned up
    echo.
)

REM Create venv WITHOUT pip first (to avoid ensurepip error)
echo [SETUP] Creating virtual environment (without pip)...
python -m venv venv --without-pip
if errorlevel 1 (
    echo [ERROR] Failed to create venv
    echo.
    echo ALTERNATIVE: Try installing packages globally instead
    pause
    exit /b 1
)
echo [OK] Virtual environment created
echo.

REM Activate venv
echo [SETUP] Activating virtual environment...
call venv\Scripts\activate.bat
echo [OK] Activated
echo.

REM Download and install pip manually
echo [SETUP] Installing pip manually...
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
del get-pip.py
echo [OK] Pip installed
echo.

REM Upgrade pip
echo [SETUP] Upgrading pip...
python -m pip install --upgrade pip --quiet
echo [OK] Pip upgraded
echo.

REM Install dependencies
echo [SETUP] Installing dependencies...
echo This will take 2-3 minutes...
echo.
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

REM Install Playwright browsers
echo [SETUP] Installing Playwright browsers...
echo This will take 5-10 minutes...
echo.
python -m playwright install chromium
if errorlevel 1 (
    echo [WARN] Browser installation had issues
    echo.
)
echo [OK] Setup complete!
echo.

echo ========================================
echo     Starting Backend Server...
echo ========================================
echo.
echo [INFO] Backend: http://localhost:8000
echo [INFO] API Docs: http://localhost:8000/docs
echo.
echo [NEXT] Open frontend\index.html in your browser
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

cd backend
python app.py

if errorlevel 1 (
    echo.
    echo [ERROR] Backend error
    cd ..
    pause
)
