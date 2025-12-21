# Start Embedding Service
# This script starts the embedding microservice on port 8001

Write-Host "🚀 Starting Embedding Service..." -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run from the project root directory" -ForegroundColor Yellow
    exit 1
}

# Navigate to embedding service directory
Write-Host "📁 Navigating to embedding_service directory..." -ForegroundColor Yellow
Set-Location embedding_service

# Check if dependencies are installed
Write-Host "🔍 Checking dependencies..." -ForegroundColor Yellow
$fastapi = & ..\.venv\Scripts\python.exe -c "import fastapi; print('installed')" 2>$null
if ($fastapi -ne "installed") {
    Write-Host "📥 Installing embedding service dependencies..." -ForegroundColor Yellow
    & ..\.venv\Scripts\pip.exe install -r requirements.txt
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "✅ Dependencies already installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "🎯 Starting Embedding Service..." -ForegroundColor Green
Write-Host ""
Write-Host "Service will be available at:" -ForegroundColor Cyan
Write-Host "  📡 API:        http://localhost:8001" -ForegroundColor White
Write-Host "  📚 API Docs:   http://localhost:8001/docs" -ForegroundColor White
Write-Host "  ❤️  Health:     http://localhost:8001/health" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the service" -ForegroundColor Yellow
Write-Host ""

# Start the embedding service
& ..\.venv\Scripts\python.exe main.py
