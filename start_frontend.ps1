# Start Frontend (React)
# This script starts the React frontend on port 3000

Write-Host "🚀 Starting CyborgDB Frontend..." -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to frontend directory
Write-Host "📁 Navigating to frontend directory..." -ForegroundColor Yellow
Set-Location frontend

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "✅ Dependencies already installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "🎯 Starting React development server..." -ForegroundColor Green
Write-Host ""
Write-Host "Frontend will be available at:" -ForegroundColor Cyan
Write-Host "  🌐 Frontend:    http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "Backend API:" -ForegroundColor Cyan
Write-Host "  📡 API:         http://localhost:8000" -ForegroundColor White
Write-Host "  📚 API Docs:    http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the frontend" -ForegroundColor Yellow
Write-Host ""

# Start the React app
npm start
