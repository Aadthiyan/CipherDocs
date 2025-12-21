# CyborgDB Backend Quick Start Script
# This script starts the FastAPI backend server

Write-Host "🚀 Starting CyborgDB Backend..." -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "📦 Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Check if in backend directory, if not navigate to it
if (-not (Test-Path "backend\main.py")) {
    Write-Host "📁 Navigating to backend directory..." -ForegroundColor Yellow
    Set-Location backend
}

# Check if dependencies are installed
Write-Host "🔍 Checking dependencies..." -ForegroundColor Yellow
$fastapi = & python -c "import fastapi; print('installed')" 2>$null
if ($fastapi -ne "installed") {
    Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "✅ Dependencies already installed" -ForegroundColor Green
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found!" -ForegroundColor Yellow
    Write-Host "Creating .env from .env.complete..." -ForegroundColor Yellow
    Copy-Item ".env.complete" ".env"
    Write-Host "✅ .env file created" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚠️  IMPORTANT: Edit backend\.env and set:" -ForegroundColor Yellow
    Write-Host "   - JWT_SECRET (generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))')" -ForegroundColor White
    Write-Host "   - MASTER_ENCRYPTION_KEY (generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))')" -ForegroundColor White
    Write-Host ""
}

Write-Host ""
Write-Host "🎯 Starting FastAPI server..." -ForegroundColor Green
Write-Host ""
Write-Host "Server will be available at:" -ForegroundColor Cyan
Write-Host "  📡 API:        http://localhost:8000" -ForegroundColor White
Write-Host "  📚 API Docs:   http://localhost:8000/docs" -ForegroundColor White
Write-Host "  ❤️  Health:     http://localhost:8000/health" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
