# Local Setup Script for URL Shortener
Write-Host "Setting up local environment..." -ForegroundColor Cyan

# Check for Python
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Python is not installed. Please install Python 3.10+ and try again." -ForegroundColor Red
    exit
}

# Create Virtual Environment
if (!(Test-Path venv)) {
    Write-Host "Creating Virtual Environment..."
    python -m venv venv
}

# Activate and Install
Write-Host "Installing dependencies..."
.\venv\Scripts\pip install -r requirements.txt

# Create .env if not exists
if (!(Test-Path .env)) {
    Write-Host "Creating default .env for local development (SQLite/Memory)..."
    Add-Content .env "DATABASE_URL=sqlite+aiosqlite:///./test.db"
    Add-Content .env "REDIS_URL=memory"
}

Write-Host "`nSetup Complete!" -ForegroundColor Green
Write-Host "To start the server, run:" -ForegroundColor Yellow
Write-Host ".\venv\Scripts\python -m uvicorn app.main:app --reload" -ForegroundColor Yellow
