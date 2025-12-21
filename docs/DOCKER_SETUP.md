# CyborgDB Docker Setup Guide

## Quick Start (5 Minutes)

This guide will help you set up the complete CyborgDB development environment using Docker Compose.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
  - Version 20.10 or higher
  - Download: https://www.docker.com/get-started
- **Docker Compose** (usually included with Docker Desktop)
  - Version 2.0 or higher
- **Git** (to clone the repository)

## Step-by-Step Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Cipherdocs
```

### 2. Configure Environment Variables

Copy the example environment file and customize it:

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your preferred text editor
# Windows: notepad .env
# Mac/Linux: nano .env or vim .env
```

**Important variables to configure:**

```env
# Database credentials (change in production!)
POSTGRES_USER=cyborgdb_user
POSTGRES_PASSWORD=cyborgdb_password
POSTGRES_DB=cyborgdb

# JWT Secret (generate a strong random key!)
JWT_SECRET=your_super_secret_jwt_key_change_this

# Master Encryption Key (32 bytes, base64 encoded)
MASTER_ENCRYPTION_KEY=your_master_encryption_key_32_bytes

# CyborgDB API Key (get from CyborgDB dashboard)
CYBORGDB_API_KEY=your_cyborgdb_api_key_here
```

**Generate secure secrets:**

```bash
# Generate JWT secret (Linux/Mac)
openssl rand -base64 32

# Generate master encryption key (Linux/Mac)
openssl rand -base64 32

# On Windows (PowerShell)
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))
```

### 3. Start All Services

Navigate to the docker directory and start the services:

```bash
cd docker
docker-compose up --build
```

**What happens:**
- PostgreSQL database starts and initializes schema
- Redis cache starts
- Embedding service starts (may take 1-2 minutes to download model)
- Backend API starts
- Frontend React app starts

**Expected startup time:** 30-60 seconds (first run may take longer due to image builds)

### 4. Verify Services

Once all services are running, verify they're healthy:

**Check service logs:**
```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs postgres
docker-compose logs embedding_service
```

**Access the services:**

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Embedding Service**: http://localhost:8001/health
- **PgAdmin** (optional): http://localhost:5050
  - Email: admin@cyborgdb.com
  - Password: admin

### 5. Test the Setup

**Test backend health:**
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "cyborgdb-backend",
  "version": "1.0.0",
  "timestamp": "2025-12-03T...",
  "environment": "development"
}
```

**Test embedding service:**
```bash
curl http://localhost:8001/health
```

**Test database connection:**
```bash
docker-compose exec postgres psql -U cyborgdb_user -d cyborgdb -c "\dt"
```

You should see the list of tables: tenants, users, documents, etc.

## Service Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (React)                                        │
│  http://localhost:3000                                   │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Backend (FastAPI)                                       │
│  http://localhost:8000                                   │
└─────────────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐ ┌─────────────┐ ┌──────────────┐
│  PostgreSQL  │ │  Embedding  │ │    Redis     │
│  :5432       │ │  Service    │ │    :6379     │
│              │ │  :8001      │ │              │
└──────────────┘ └─────────────┘ └──────────────┘
```

## Port Mappings

| Service | Internal Port | External Port | Description |
|---------|--------------|---------------|-------------|
| Frontend | 3000 | 3000 | React development server |
| Backend | 8000 | 8000 | FastAPI application |
| Embedding Service | 8001 | 8001 | ML embedding service |
| PostgreSQL | 5432 | 5432 | Database |
| Redis | 6379 | 6379 | Cache |
| PgAdmin | 80 | 5050 | Database management UI |

## Volume Mounts

Docker Compose creates persistent volumes for:

- **postgres_data**: PostgreSQL database files
- **redis_data**: Redis persistence
- **model_cache**: Hugging Face model weights
- **document_storage**: Uploaded documents
- **pgadmin_data**: PgAdmin configuration

## Common Commands

### Start services
```bash
docker-compose up
```

### Start in background (detached mode)
```bash
docker-compose up -d
```

### Stop services
```bash
docker-compose down
```

### Stop and remove volumes (⚠️ deletes all data!)
```bash
docker-compose down -v
```

### Rebuild services after code changes
```bash
docker-compose up --build
```

### View logs
```bash
docker-compose logs -f
```

### Execute commands in containers
```bash
# Access PostgreSQL
docker-compose exec postgres psql -U cyborgdb_user -d cyborgdb

# Access backend shell
docker-compose exec backend bash

# Run database migrations (Phase 1, Task 1.4)
docker-compose exec backend alembic upgrade head
```

### Restart a specific service
```bash
docker-compose restart backend
```

## Troubleshooting

### Issue: Port already in use

**Error:** `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solution:**
```bash
# Find process using the port (Windows)
netstat -ano | findstr :8000

# Find process using the port (Mac/Linux)
lsof -i :8000

# Kill the process or change port in docker-compose.yml
```

### Issue: Database connection failed

**Error:** `could not connect to server: Connection refused`

**Solution:**
```bash
# Check if PostgreSQL is running
docker-compose ps

# Check PostgreSQL logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres

# Wait for health check to pass
docker-compose ps | grep postgres
```

### Issue: Out of disk space

**Error:** `no space left on device`

**Solution:**
```bash
# Remove unused Docker images
docker system prune -a

# Remove unused volumes
docker volume prune

# Check disk usage
docker system df
```

### Issue: Services not communicating

**Error:** `Connection refused` between services

**Solution:**
- Ensure all services are on the same Docker network (`cyborgdb_network`)
- Use service names (not localhost) in inter-service URLs
- Example: `http://backend:8000` not `http://localhost:8000`
- Check `docker-compose logs` for network errors

### Issue: Frontend can't reach backend

**Error:** `Network Error` in browser console

**Solution:**
- Check CORS configuration in backend
- Verify `CORS_ORIGINS` includes `http://localhost:3000`
- Ensure backend is running: `curl http://localhost:8000/health`
- Check browser console for specific error messages

## Development Workflow

### Making Code Changes

**Backend changes:**
```bash
# Backend has hot-reload enabled in development
# Just edit files and save - changes apply automatically
```

**Frontend changes:**
```bash
# Frontend also has hot-reload
# Edit files in frontend/src/ and save
# Browser will auto-refresh
```

**Dependency changes:**
```bash
# If you add new Python packages to requirements.txt
docker-compose up --build backend

# If you add new npm packages to package.json
docker-compose up --build frontend
```

### Database Management

**Access database with PgAdmin:**
1. Go to http://localhost:5050
2. Login with admin@cyborgdb.com / admin
3. Add server:
   - Host: postgres
   - Port: 5432
   - Database: cyborgdb
   - Username: cyborgdb_user
   - Password: cyborgdb_password

**Run SQL queries:**
```bash
docker-compose exec postgres psql -U cyborgdb_user -d cyborgdb

# Example queries
SELECT * FROM tenants;
SELECT * FROM users;
\dt  # List all tables
\d tenants  # Describe tenants table
```

## Production Deployment

For production deployment, you'll need to:

1. **Change all default passwords and secrets**
2. **Use environment-specific .env files**
3. **Enable HTTPS/TLS**
4. **Use managed database services** (AWS RDS, etc.)
5. **Set up proper logging and monitoring**
6. **Configure backup and disaster recovery**
7. **Use Kubernetes or similar orchestration** (not Docker Compose)

See [deployment guide](../docs/deployment/README.md) for details.

## Next Steps

Now that your environment is running:

1. ✅ Verify all services are healthy
2. ✅ Check the frontend at http://localhost:3000
3. ✅ Explore API docs at http://localhost:8000/docs
4. 📝 Proceed to **Phase 2: Authentication & Multi-Tenancy**
5. 📝 Implement database models and migrations

## Support

If you encounter issues:

1. Check the [troubleshooting section](#troubleshooting) above
2. Review service logs: `docker-compose logs`
3. Verify environment variables in `.env`
4. Ensure Docker has enough resources (4GB+ RAM recommended)
5. Check Docker network: `docker network inspect cyborgdb_network`

---

**Setup complete! You're ready to build CyborgDB! 🚀**
