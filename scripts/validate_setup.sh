#!/bin/bash
# CyborgDB Environment Validation Script
# Run this script to verify your Docker environment is properly configured

echo "🔍 CyborgDB Environment Validation"
echo "===================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Docker
echo "Checking Docker installation..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo -e "${GREEN}✓${NC} Docker found: $DOCKER_VERSION"
else
    echo -e "${RED}✗${NC} Docker not found. Please install Docker Desktop."
    exit 1
fi

# Check Docker Compose
echo "Checking Docker Compose..."
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    echo -e "${GREEN}✓${NC} Docker Compose found: $COMPOSE_VERSION"
else
    echo -e "${RED}✗${NC} Docker Compose not found."
    exit 1
fi

# Check if Docker is running
echo "Checking if Docker daemon is running..."
if docker info &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker daemon is running"
else
    echo -e "${RED}✗${NC} Docker daemon is not running. Please start Docker Desktop."
    exit 1
fi

# Check .env file
echo "Checking environment configuration..."
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env file exists"
    
    # Check critical variables
    if grep -q "JWT_SECRET=dev_jwt_secret" .env; then
        echo -e "${YELLOW}⚠${NC}  Warning: Using default JWT_SECRET (change in production!)"
    fi
    
    if grep -q "CYBORGDB_API_KEY=placeholder" .env; then
        echo -e "${YELLOW}⚠${NC}  Warning: Using placeholder CyborgDB API key"
    fi
else
    echo -e "${RED}✗${NC} .env file not found. Run: cp .env.example .env"
    exit 1
fi

# Check required directories
echo "Checking project structure..."
REQUIRED_DIRS=("backend" "frontend" "embedding_service" "docker" "scripts" "docs")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} Directory exists: $dir"
    else
        echo -e "${RED}✗${NC} Missing directory: $dir"
    fi
done

# Check required files
echo "Checking required files..."
REQUIRED_FILES=(
    "docker/docker-compose.yml"
    "backend/main.py"
    "backend/requirements.txt"
    "embedding_service/main.py"
    "frontend/package.json"
    "scripts/db_setup.sql"
)
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} File exists: $file"
    else
        echo -e "${RED}✗${NC} Missing file: $file"
    fi
done

# Check available ports
echo "Checking if required ports are available..."
PORTS=(3000 8000 8001 5432 6379)
for port in "${PORTS[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo -e "${YELLOW}⚠${NC}  Port $port is already in use"
    else
        echo -e "${GREEN}✓${NC} Port $port is available"
    fi
done

echo ""
echo "===================================="
echo "Validation complete!"
echo ""
echo "Next steps:"
echo "1. Review any warnings above"
echo "2. Navigate to docker directory: cd docker"
echo "3. Start services: docker-compose up --build"
echo "4. Access frontend: http://localhost:3000"
echo ""
echo "For detailed setup instructions, see: docs/DOCKER_SETUP.md"
