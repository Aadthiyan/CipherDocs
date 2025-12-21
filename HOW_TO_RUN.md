# 🚀 CyborgDB - How to Run This Project

## Quick Navigation
- [Option 1: Docker (Full Stack)](#option-1-docker-full-stack-recommended) ⭐ **Recommended**
- [Option 2: Backend Only (Development)](#option-2-backend-only-development)
- [Option 3: Run Tests](#option-3-run-tests)
- [Troubleshooting](#troubleshooting)

---

## Option 1: Docker (Full Stack) ⭐ **Recommended**

This runs the complete application with all services (Backend, Frontend, Redis).

### Prerequisites
- ✅ Docker Desktop installed and running
- ✅ `.env.docker` file configured (already present)

### Steps

1. **Navigate to the docker directory:**
```powershell
cd docker
```

2. **Start all services:**
```powershell
docker-compose up --build
```

This will start:
- **Backend API** on `http://localhost:8000`
- **Frontend Dashboard** on `http://localhost:3000`
- **Redis** on `localhost:6379`

3. **Access the application:**
- 🌐 **Frontend**: http://localhost:3000
- 📡 **Backend API**: http://localhost:8000
- 📚 **API Docs (Swagger)**: http://localhost:8000/docs
- ❤️ **Health Check**: http://localhost:8000/health

### Stop Services
```powershell
# Press Ctrl+C in the terminal, then:
docker-compose down
```

### View Logs
```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

---

## Option 2: Backend Only (Development)

Run just the FastAPI backend for development or testing.

### Prerequisites
- ✅ Python 3.9+ installed
- ✅ Virtual environment activated
- ✅ `.env` file configured in `backend/` directory

### Steps

1. **Navigate to backend directory:**
```powershell
cd backend
```

2. **Create and activate virtual environment (if not already done):**
```powershell
# Create virtual environment
python -m venv .venv

# Activate it
.\.venv\Scripts\Activate.ps1
```

3. **Install dependencies:**
```powershell
pip install -r requirements.txt
```

4. **Run database migrations (first time only):**
```powershell
# Generate migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head
```

5. **Start the backend server:**
```powershell
# Development mode with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

6. **Access the backend:**
- 📡 **API**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs
- ❤️ **Health Check**: http://localhost:8000/health

### Alternative: Run with Python
```powershell
python main.py
```

---

## Option 3: Run Tests

The project has comprehensive test coverage (270+ tests, >85% coverage).

### Quick Test Run

```powershell
cd backend

# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# View HTML coverage report
start htmlcov\index.html
```

### Using Test Runner Scripts

```powershell
# Windows
.\run_tests.bat all              # All tests
.\run_tests.bat auth             # Auth tests only
.\run_tests.bat coverage         # With coverage
.\run_tests.bat report           # Generate HTML report

# Linux/Mac (if using WSL)
./run_tests.sh all
```

### Run Specific Tests

```powershell
# Run specific test module
pytest tests/test_auth_jwt_comprehensive.py -v

# Run specific test class
pytest tests/test_auth_jwt_comprehensive.py::TestPasswordHashing -v

# Run tests matching a pattern
pytest -k "encryption" -v
```

---

## Option 4: Frontend Only (React)

Run just the React frontend (requires backend to be running separately).

### Steps

1. **Navigate to frontend directory:**
```powershell
cd frontend
```

2. **Install dependencies (first time only):**
```powershell
npm install
```

3. **Start development server:**
```powershell
npm start
```

4. **Access the frontend:**
- 🌐 http://localhost:3000

---

## Environment Configuration

### Required Environment Variables

The backend requires a `.env` file in the `backend/` directory with these critical variables:

```env
# Database (Neon PostgreSQL)
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require

# Security (Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
JWT_SECRET=your_secure_jwt_secret_at_least_32_chars
MASTER_ENCRYPTION_KEY=your_master_encryption_key_at_least_32_chars

# CyborgDB (Optional for basic testing)
CYBORGDB_API_KEY=your_api_key_here
CYBORGDB_ENDPOINT=https://api.cyborg.co

# Environment
ENVIRONMENT=development
DEBUG=true
```

### Generate Secure Secrets

```powershell
# Generate JWT Secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate Master Encryption Key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Configuration Files Available
- `.env.example` - Template with all variables
- `.env.development` - Development settings
- `.env.complete` - Complete configuration
- `.env.minimal` - Minimal required settings

---

## Quick Health Checks

### Check if Backend is Running
```powershell
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-19T...",
  "version": "1.0.0"
}
```

### Check if Frontend is Running
Open browser: http://localhost:3000

### Check if Redis is Running (Docker)
```powershell
docker exec cyborgdb_redis redis-cli ping
```

Expected response: `PONG`

---

## Troubleshooting

### Backend Won't Start

**Issue**: `ModuleNotFoundError` or import errors
```powershell
# Solution: Reinstall dependencies
cd backend
pip install -r requirements.txt
```

**Issue**: Database connection errors
```powershell
# Solution: Check DATABASE_URL in .env file
# Verify Neon database is accessible
# Check if database exists
```

**Issue**: Port 8000 already in use
```powershell
# Solution: Find and kill the process
netstat -ano | findstr :8000
taskkill /PID <process_id> /F

# Or use a different port
uvicorn main:app --reload --port 8001
```

### Docker Issues

**Issue**: Docker containers won't start
```powershell
# Solution: Clean up and rebuild
cd docker
docker-compose down -v
docker-compose up --build
```

**Issue**: Permission errors
```powershell
# Solution: Run Docker Desktop as Administrator
# Or check Docker Desktop settings
```

**Issue**: Out of disk space
```powershell
# Solution: Clean up Docker
docker system prune -a
```

### Frontend Issues

**Issue**: `npm install` fails
```powershell
# Solution: Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

**Issue**: Can't connect to backend
- Check if backend is running on http://localhost:8000
- Verify CORS settings in backend `.env`
- Check `REACT_APP_API_URL` in frontend

### Test Issues

**Issue**: Tests fail with import errors
```powershell
# Solution: Ensure you're in backend directory
cd backend
pytest
```

**Issue**: Database tests fail
```powershell
# Solution: Tests use in-memory SQLite, no database needed
# If still failing, check test_fixtures.py
```

---

## Useful Commands

### Backend Development
```powershell
# Start backend with auto-reload
cd backend
uvicorn main:app --reload

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Check config
python -c "from app.core.config import settings; print('✅ Config valid')"
```

### Docker Management
```powershell
cd docker

# Start services
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild specific service
docker-compose up --build backend
```

### Testing
```powershell
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific module
pytest tests/test_auth_jwt_comprehensive.py -v

# Show slowest tests
pytest --durations=10
```

---

## Next Steps After Running

1. **Create a tenant account:**
   - Use the API docs at http://localhost:8000/docs
   - POST to `/api/v1/auth/register`

2. **Upload documents:**
   - POST to `/api/v1/documents/upload`
   - Supported formats: PDF, DOCX, TXT, PPTX, XLSX

3. **Search documents:**
   - POST to `/api/v1/search/semantic`
   - Uses encrypted vector search via CyborgDB

4. **Explore the API:**
   - Interactive docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

---

## Documentation

- 📖 **[README.md](README.md)** - Project overview
- 📖 **[TESTING_QUICK_START.md](TESTING_QUICK_START.md)** - Testing guide
- 📖 **[docs/](docs/)** - Comprehensive documentation
- 📖 **[backend/.env.example](backend/.env.example)** - Environment variables reference

---

## Support

If you encounter issues:
1. Check the [Troubleshooting](#troubleshooting) section above
2. Review the logs: `docker-compose logs -f` or backend console output
3. Verify environment variables in `.env` files
4. Check that all required services are running

---

**Built with ❤️ for the CyborgDB Hackathon**
