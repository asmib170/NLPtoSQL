Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  NLP-to-SQL  —  Starting Application" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ---- Prerequisites ----
Write-Host "[1/6] Checking prerequisites..." -ForegroundColor Yellow

# Create venv if missing
if (-not (Test-Path "$PSScriptRoot\.venv")) {
    Write-Host "      Creating virtual environment..."
    uv venv
}

# Activate venv
& "$PSScriptRoot\.venv\Scripts\Activate.ps1"

# Install Python dependencies
Write-Host "      Installing Python dependencies..."
& "$PSScriptRoot\.venv\Scripts\pip.exe" install -r "$PSScriptRoot\requirements.txt" --quiet

# Create database if missing
if (-not (Test-Path "$PSScriptRoot\prereq\DemoECommerceDB.db")) {
    Write-Host "      Creating database and populating with sample data..."
    & "$PSScriptRoot\.venv\Scripts\python.exe" "$PSScriptRoot\prereq\01_create_db.py"
    & "$PSScriptRoot\.venv\Scripts\python.exe" "$PSScriptRoot\prereq\02_populate_db.py"
    Write-Host "      Database ready."
} else {
    Write-Host "      Database already exists."
}

# ---- Kill stale processes on ports 8000 and 3000 ----
Write-Host "[2/6] Freeing ports 8000 and 3000..." -ForegroundColor Yellow
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Write-Host "      Ports cleared."

# ---- Frontend dependencies ----
Write-Host "[3/6] Checking frontend dependencies..." -ForegroundColor Yellow
if (-not (Test-Path "$PSScriptRoot\webui\node_modules")) {
    Write-Host "      Installing npm packages..."
    Push-Location "$PSScriptRoot\webui"
    npm install
    Pop-Location
} else {
    Write-Host "      Frontend packages already installed."
}

# ---- Start backend ----
Write-Host "[4/6] Starting Python backend (port 8000)..." -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/k", "cd /d $PSScriptRoot\agent && $PSScriptRoot\.venv\Scripts\python.exe server.py" -WindowStyle Normal

# Wait for backend to be ready
Write-Host "[5/6] Waiting for backend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# ---- Start frontend ----
Write-Host "[6/6] Starting React frontend (port 3000)..." -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/k", "cd /d $PSScriptRoot\webui && npm run dev" -WindowStyle Normal

# Wait a moment then open browser
Start-Sleep -Seconds 4

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  App running at: http://localhost:3000" -ForegroundColor Green
Write-Host "  Backend API at: http://localhost:8000" -ForegroundColor Green
Write-Host "  Close the terminal windows to stop." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green

Start-Process "http://localhost:3000"
