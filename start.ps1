Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  NLP-to-SQL  —  Starting Backend + Frontend" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Activate venv
& "$PSScriptRoot\.venv\Scripts\Activate.ps1"

# Install frontend deps if needed
Write-Host "[1/3] Checking frontend dependencies..." -ForegroundColor Yellow
if (-not (Test-Path "$PSScriptRoot\webui\node_modules")) {
    Write-Host "      Installing npm packages..."
    Push-Location "$PSScriptRoot\webui"
    npm install
    Pop-Location
}

# Start backend in a new window
Write-Host "[2/3] Starting Python backend (port 8000)..." -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/k", "cd /d $PSScriptRoot\agent && $PSScriptRoot\.venv\Scripts\python.exe server.py" -WindowStyle Normal

# Wait for backend
Write-Host "      Waiting for backend to start..."
Start-Sleep -Seconds 4

# Start frontend in a new window
Write-Host "[3/3] Starting React frontend (port 3000)..." -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/k", "cd /d $PSScriptRoot\webui && npm run dev" -WindowStyle Normal

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  App running at: http://localhost:3000" -ForegroundColor Green
Write-Host "  Backend API at: http://localhost:8000" -ForegroundColor Green
Write-Host "  Close the terminal windows to stop." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green

# Open browser
Start-Process "http://localhost:3000"
