# CyborgDB Environment Validation Script (Windows PowerShell)
# Run this script to verify your Docker environment is properly configured

Write-Host "🔍 CyborgDB Environment Validation" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

$allChecksPass = $true

# Check Docker
Write-Host "Checking Docker installation..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✓ Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker not found. Please install Docker Desktop." -ForegroundColor Red
    $allChecksPass = $false
}

# Check Docker Compose
Write-Host "Checking Docker Compose..." -ForegroundColor Yellow
try {
    $composeVersion = docker-compose --version
    Write-Host "✓ Docker Compose found: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker Compose not found." -ForegroundColor Red
    $allChecksPass = $false
}

# Check if Docker is running
Write-Host "Checking if Docker daemon is running..." -ForegroundColor Yellow
try {
    docker info | Out-Null
    Write-Host "✓ Docker daemon is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker daemon is not running. Please start Docker Desktop." -ForegroundColor Red
    $allChecksPass = $false
}

# Check .env file
Write-Host "Checking environment configuration..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✓ .env file exists" -ForegroundColor Green
    
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "JWT_SECRET=dev_jwt_secret") {
        Write-Host "⚠  Warning: Using default JWT_SECRET (change in production!)" -ForegroundColor Yellow
    }
    
    if ($envContent -match "CYBORGDB_API_KEY=placeholder") {
        Write-Host "⚠  Warning: Using placeholder CyborgDB API key" -ForegroundColor Yellow
    }
} else {
    Write-Host "✗ .env file not found. Run: Copy-Item .env.example .env" -ForegroundColor Red
    $allChecksPass = $false
}

# Check required directories
Write-Host "Checking project structure..." -ForegroundColor Yellow
$requiredDirs = @("backend", "frontend", "embedding_service", "docker", "scripts", "docs")
foreach ($dir in $requiredDirs) {
    if (Test-Path $dir -PathType Container) {
        Write-Host "✓ Directory exists: $dir" -ForegroundColor Green
    } else {
        Write-Host "✗ Missing directory: $dir" -ForegroundColor Red
        $allChecksPass = $false
    }
}

# Check required files
Write-Host "Checking required files..." -ForegroundColor Yellow
$requiredFiles = @(
    "docker\docker-compose.yml",
    "backend\main.py",
    "backend\requirements.txt",
    "embedding_service\main.py",
    "frontend\package.json",
    "scripts\db_setup.sql"
)
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "✓ File exists: $file" -ForegroundColor Green
    } else {
        Write-Host "✗ Missing file: $file" -ForegroundColor Red
        $allChecksPass = $false
    }
}

# Check available ports
Write-Host "Checking if required ports are available..." -ForegroundColor Yellow
$ports = @(3000, 8000, 8001, 5432, 6379)
foreach ($port in $ports) {
    $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connection) {
        Write-Host "⚠  Port $port is already in use" -ForegroundColor Yellow
    } else {
        Write-Host "✓ Port $port is available" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
if ($allChecksPass) {
    Write-Host "✓ All critical checks passed!" -ForegroundColor Green
} else {
    Write-Host "✗ Some checks failed. Please review above." -ForegroundColor Red
}
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Review any warnings above"
Write-Host "2. Navigate to docker directory: cd docker"
Write-Host "3. Start services: docker-compose up --build"
Write-Host "4. Access frontend: http://localhost:3000"
Write-Host ""
Write-Host "For detailed setup instructions, see: docs\DOCKER_SETUP.md" -ForegroundColor Cyan
