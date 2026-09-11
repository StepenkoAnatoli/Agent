@echo off
title Agent
cd /d "%~dp0"

echo.
echo  ============================================
echo   Agent - local AI assistant
echo  ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found on this computer.
    echo.
    echo  Fix:  go to https://www.python.org/downloads/
    echo        download Python 3.11 or newer, run the installer,
    echo        and CHECK the box "Add python.exe to PATH".
    echo        Then double-click this file again.
    echo.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] First run: creating a private Python environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Could not create the Python environment.
        pause
        exit /b 1
    )
) else (
    echo [1/3] Environment found.
)

echo [2/3] Checking dependencies (first run downloads them)...
".venv\Scripts\python.exe" -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Could not install dependencies. Check your internet connection and try again.
    pause
    exit /b 1
)

echo [3/3] Starting the server at http://localhost:8000
echo        (Keep this window open while using Agent.)
start "" /b cmd /c "timeout /t 3 /nobreak >nul & start http://localhost:8000"

".venv\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000

echo.
echo Server stopped. You can close this window.
pause >nul
