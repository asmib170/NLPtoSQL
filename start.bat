@echo off
echo ============================================================
echo   NLP-to-SQL  —  Starting Application
echo ============================================================
echo.

:: Refresh PATH to pick up Node.js
set PATH=%PATH%;%ProgramFiles%\nodejs;%APPDATA%\npm

:: ---- Prerequisites ----
echo [1/6] Checking prerequisites...

:: Create venv if missing
if not exist "%~dp0.venv" (
    echo      Creating virtual environment...
    uv venv
)

:: Install Python dependencies
echo      Installing Python dependencies...
"%~dp0.venv\Scripts\pip.exe" install -r "%~dp0requirements.txt" --quiet

:: Create database if missing
if not exist "%~dp0prereq\DemoECommerceDB.db" (
    echo      Creating database and populating with sample data...
    "%~dp0.venv\Scripts\python.exe" "%~dp0prereq\01_create_db.py"
    "%~dp0.venv\Scripts\python.exe" "%~dp0prereq\02_populate_db.py"
    echo      Database ready.
) else (
    echo      Database already exists.
)

:: ---- Kill stale processes on ports 8000 and 3000 ----
echo [2/6] Freeing ports 8000 and 3000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000.*LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000.*LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)
echo      Ports cleared.

:: ---- Frontend dependencies ----
echo [3/6] Checking frontend dependencies...
cd /d "%~dp0webui"
if not exist node_modules (
    echo      Installing npm packages...
    call npm install
) else (
    echo      Frontend packages already installed.
)
cd /d "%~dp0"

:: ---- Start backend ----
echo [4/6] Starting Python backend (port 8000)...
start "NLPtoSQL-Backend" cmd /k "cd /d %~dp0agent && %~dp0.venv\Scripts\python.exe server.py"

:: Wait for backend to be ready
echo [5/6] Waiting for backend to start...
timeout /t 5 /nobreak >nul

:: ---- Start frontend ----
echo [6/6] Starting React frontend (port 3000)...
start "NLPtoSQL-Frontend" cmd /k "cd /d %~dp0webui && npm run dev"

:: Wait a moment then open browser
timeout /t 4 /nobreak >nul
echo.
echo ============================================================
echo   App running at: http://localhost:3000
echo   Backend API at: http://localhost:8000
echo   Close the terminal windows to stop.
echo ============================================================
start http://localhost:3000
