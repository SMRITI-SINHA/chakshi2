@echo off
title eCourts Chatbot - Startup
color 0A

echo.
echo ========================================
echo     eCourts Chatbot - Starting...
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

echo [OK] Python is installed
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo [SETUP] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
    echo.
)

REM Activate virtual environment
echo [SETUP] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

echo [OK] Virtual environment activated
echo.

REM Check if dependencies are installed
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo [SETUP] Installing dependencies (this may take a few minutes)...
    echo.
    python -m pip install --upgrade pip --quiet
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
    echo [OK] Dependencies installed
    echo.
)

REM Check if Playwright is installed
python -c "from playwright.sync_api import sync_playwright" 2>nul
if errorlevel 1 (
    echo [SETUP] Installing Playwright browsers...
    echo This may take several minutes...
    echo.
    python -m playwright install chromium
    if errorlevel 1 (
        echo [WARNING] Playwright browser installation failed
        echo You may need to install it manually: python -m playwright install chromium
        echo.
    ) else (
        echo [OK] Playwright browsers installed
        echo.
    )
)

echo ========================================
echo     Starting Backend Server...
echo ========================================
echo.
echo [INFO] Backend will run on: http://localhost:8000
echo [INFO] API Docs available at: http://localhost:8000/docs
echo.
echo [NEXT STEP] Open frontend\index.html in your browser
echo             to use the chatbot
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
    pause
)
