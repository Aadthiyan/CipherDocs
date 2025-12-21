# CyborgDB Docker Quick Start Script
# This script starts all services using Docker Compose

Write-Host "🐳 Starting CyborgDB with Docker..." -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
Write-Host "🔍 Checking Docker..." -ForegroundColor Yellow
$dockerRunning = docker ps 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ Docker is running" -ForegroundColor Green
Write-Host ""

# Check if .env.docker exists
if (-not (Test-Path ".env.docker")) {
    Write-Host "❌ .env.docker file not found!" -ForegroundColor Red
    Write-Host "Please create .env.docker with required environment variables." -ForegroundColor Yellow
    exit 1
}

# Navigate to docker directory
Write-Host "📁 Navigating to docker directory..." -ForegroundColor Yellow
Set-Location docker

Write-Host ""
Write-Host "🚀 Starting all services..." -ForegroundColor Green
Write-Host ""
Write-Host "This will start:" -ForegroundColor Cyan
Write-Host "  🔴 Redis (Cache)" -ForegroundColor White
Write-Host "  🟢 Backend API (FastAPI)" -ForegroundColor White
Write-Host "  🔵 Frontend (React)" -ForegroundColor White
Write-Host ""
Write-Host "Services will be available at:" -ForegroundColor Cyan
Write-Host "  🌐 Frontend:    http://localhost:3000" -ForegroundColor White
Write-Host "  📡 Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "  📚 API Docs:    http://localhost:8000/docs" -ForegroundColor White
Write-Host "  ❤️  Health:      http://localhost:8000/health" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host ""
Write-Host "Starting containers... (this may take a few minutes on first run)" -ForegroundColor Yellow
Write-Host ""

# Start Docker Compose
docker-compose up --build
