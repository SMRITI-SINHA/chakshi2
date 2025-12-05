@echo off
title eCourts Chatbot - Setup & Start
color 0A

echo.
echo ========================================
echo     eCourts Chatbot - Setup
echo ========================================
echo.

REM Get the directory where this batch file is located
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo [OK] Python is installed:
python --version
echo.

REM Delete old venv if it exists but is broken
if exist "venv\" (
    echo [INFO] Checking existing virtual environment...
    if not exist "venv\Scripts\activate.bat" (
        echo [WARN] Virtual environment is corrupted, recreating...
        rmdir /s /q venv
    )
)

REM Create virtual environment if it doesn't exist
if not exist "venv\" (
    echo [SETUP] Creating virtual environment...
    echo This may take a minute...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        echo.
        echo Try running as Administrator or check Python installation
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
    echo.
)

REM Activate virtual environment
echo [SETUP] Activating virtual environment...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo [OK] Virtual environment activated
    echo.
) else (
    echo [ERROR] Cannot find venv\Scripts\activate.bat
    echo [FIX] Recreating virtual environment...
    rmdir /s /q venv
    python -m venv venv
    call venv\Scripts\activate.bat
)

REM Upgrade pip
echo [SETUP] Upgrading pip...
python -m pip install --upgrade pip --quiet
echo [OK] Pip upgraded
echo.

REM Install dependencies
echo [SETUP] Installing dependencies...
echo This may take 2-3 minutes on first run...
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
echo [SETUP] Checking Playwright browsers...
python -c "from playwright.sync_api import sync_playwright; import sys; p = sync_playwright().start(); b = p.chromium.launch(); b.close(); p.stop(); sys.exit(0)" 2>nul
if errorlevel 1 (
    echo [SETUP] Installing Playwright browsers...
    echo This may take 5-10 minutes...
    echo.
    python -m playwright install chromium
    if errorlevel 1 (
        echo [WARN] Playwright browser installation had issues
        echo You can try installing manually later: python -m playwright install chromium
        echo.
    ) else (
        echo [OK] Playwright browsers installed
        echo.
    )
) else (
    echo [OK] Playwright browsers already installed
    echo.
)

echo ========================================
echo     Starting Backend Server...
echo ========================================
echo.
echo [INFO] Backend URL: http://localhost:8000
echo [INFO] API Docs: http://localhost:8000/docs
echo.
echo [NEXT STEP] Open frontend\index.html in your browser
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

REM Start the backend
cd backend
python app.py

REM If backend stops, pause so user can see error messages
if errorlevel 1 (
    echo.
    echo [ERROR] Backend stopped with an error
    cd ..
    pause
)
