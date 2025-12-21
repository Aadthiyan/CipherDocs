# CyborgDB Quick Start Script
# Run this to set up your environment

Write-Host "🚀 CyborgDB Quick Start" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Copy .env file
Write-Host "Step 1: Setting up environment variables..." -ForegroundColor Yellow
if (Test-Path "backend\.env") {
    Write-Host "⚠️  .env file already exists. Backing up..." -ForegroundColor Yellow
    Copy-Item "backend\.env" "backend\.env.backup"
}

Copy-Item "backend\.env.complete" "backend\.env"
Write-Host "✅ Created backend\.env with CyborgDB API key" -ForegroundColor Green
Write-Host ""

# Step 2: Pull CyborgDB image
Write-Host "Step 2: Pulling CyborgDB Docker image..." -ForegroundColor Yellow
Set-Location docker
docker pull cyborgdb-service
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ CyborgDB image pulled successfully" -ForegroundColor Green
} else {
    Write-Host "⚠️  Failed to pull CyborgDB image. Will try to build locally." -ForegroundColor Yellow
}
Write-Host ""

# Step 3: Install Python dependencies
Write-Host "Step 3: Installing Python dependencies..." -ForegroundColor Yellow
Set-Location ..\backend
pip install cyborgdb
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ CyborgDB Python SDK installed" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install CyborgDB SDK" -ForegroundColor Red
}
Write-Host ""

# Step 4: Run database migrations
Write-Host "Step 4: Running database migrations..." -ForegroundColor Yellow
alembic revision --autogenerate -m "Initial schema"
if ($LASTEXITCODE -eq 0) {
    alembic upgrade head
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Database migrations completed" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to apply migrations" -ForegroundColor Red
    }
} else {
    Write-Host "❌ Failed to generate migrations" -ForegroundColor Red
}
Write-Host ""

# Step 5: Start services
Write-Host "Step 5: Starting all services..." -ForegroundColor Yellow
Set-Location ..\docker
Write-Host ""
Write-Host "Running: docker-compose up --build" -ForegroundColor Cyan
Write-Host ""
Write-Host "Services will be available at:" -ForegroundColor Green
Write-Host "  Frontend:    http://localhost:3000" -ForegroundColor White
Write-Host "  Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs:    http://localhost:8000/docs" -ForegroundColor White
Write-Host "  CyborgDB:    http://localhost:8002" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host ""

docker-compose up --build
