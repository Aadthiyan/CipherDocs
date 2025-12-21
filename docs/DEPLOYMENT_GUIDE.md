# Deployment Guide - CipherDocs

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Prerequisites](#prerequisites)
3. [Quick Start (Docker)](#quick-start-docker)
4. [Manual Deployment](#manual-deployment)
5. [Configuration](#configuration)
6. [Health Checks](#health-checks)
7. [Scaling](#scaling)
8. [Troubleshooting](#troubleshooting)
9. [Production Checklist](#production-checklist)

---

## System Requirements

### Minimum (Development)
- CPU: 2 cores
- RAM: 4GB
- Storage: 10GB SSD
- OS: Linux, macOS, or Windows (with WSL2)

### Recommended (Production)
- CPU: 4+ cores
- RAM: 16GB
- Storage: 50GB+ SSD (NVMe preferred)
- Network: 1Gbps+ connection
- Load Balancer: Required for HA setup

### Scaling
- Each additional 10,000 documents: +2GB RAM, +50GB storage
- Peak search load: 500+ concurrent users needs 8+ cores
- Embedding generation: GPU acceleration recommended for high volume

---

## Prerequisites

### Required Software
- **Docker**: 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose**: 2.0+ (included with Docker Desktop)
- **Git**: 2.25+
- **curl**: 7.64+ (for health checks)

### Verify Installation

```bash
# Check Docker
docker --version
# Output: Docker version 20.10.x, build xxxxx

# Check Docker Compose
docker-compose --version
# Output: Docker Compose version 2.x.x

# Check Git
git --version
# Output: git version 2.25.x
```

### Optional Software
- **PostgreSQL Client** (psql): For direct database access
- **Node.js 18+**: For running frontend locally
- **Python 3.10+**: For running backend locally
- **VS Code**: For development

---

## Quick Start (Docker)

### Step 1: Clone Repository

```bash
git clone https://github.com/your-org/cipherdocs.git
cd cipherdocs
```

### Step 2: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration (important settings)
nano .env
```

**Key environment variables to set**:
```bash
# Database
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=cipherdocs
POSTGRES_USER=postgres

# JWT Secret (generate: python -c "import secrets; print(secrets.token_urlsafe(32))")
JWT_SECRET_KEY=your_jwt_secret_key_here

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Embedding Service
EMBEDDING_API_URL=http://embedding_service:8001
HF_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2

# CyborgDB (encrypted vector database)
CYBORGDB_API_URL=http://cyborgdb:8002
CYBORGDB_API_KEY=your_cyborgdb_api_key_here
```

### Step 3: Start Services

```bash
# Build and start all services
docker-compose -f docker/docker-compose.yml up -d

# Expected output:
# [+] Building 5.2s (42/42)
# [+] Running 5/5
```

### Step 4: Verify Services

```bash
# Check service status
docker-compose -f docker/docker-compose.yml ps

# Expected output:
# NAME                  STATUS          PORTS
# cyborgdb_postgres     Up 2 minutes     5432/tcp
# cyborgdb_redis        Up 2 minutes     6379/tcp
# cyborgdb_embedding    Up 2 minutes     8001/tcp
# cyborgdb_backend      Up 2 minutes     0.0.0.0:8000->8000/tcp
# cyborgdb_frontend     Up 2 minutes     0.0.0.0:3000->3000/tcp
```

### Step 5: Access Application

- **Backend API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000
- **Health Check**: http://localhost:8000/health

### Step 6: Test Deployment

```bash
# Test API health
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","version":"1.0.0","timestamp":"2025-12-16T10:30:00Z"}

# Create test account
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!",
    "full_name": "Test User"
  }'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }' | jq '.access_token'
```

✅ **Deployment Complete!** (< 5 minutes)

---

## Manual Deployment

### Backend Setup

#### 1. Clone and Navigate

```bash
git clone https://github.com/your-org/cipherdocs.git
cd cipherdocs/backend
```

#### 2. Create Virtual Environment

```bash
# Python 3.10+
python -m venv venv

# Activate
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Configure Environment

```bash
# Copy and edit .env
cp .env.example .env
nano .env
```

#### 5. Initialize Database

```bash
# Run migrations
alembic upgrade head

# Verify database
python -c "from app.db.database import SessionLocal; SessionLocal().execute('SELECT 1')"
```

#### 6. Start Backend

```bash
# Development
python main.py

# Production (with Uvicorn)
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Embedding Service Setup

```bash
cd cipherdocs/embedding_service

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start service
python main.py
# Runs on http://localhost:8001
```

### Frontend Setup

```bash
cd cipherdocs/frontend

# Install dependencies
npm install

# Configure API
echo "REACT_APP_API_URL=http://localhost:8000" > .env

# Start development server
npm start
# Runs on http://localhost:3000
```

### Database Setup

```bash
# Start PostgreSQL (Docker)
docker run -d \
  --name cyborgdb_postgres \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=cipherdocs \
  -p 5432:5432 \
  postgres:15-alpine

# Wait for startup
sleep 5

# Run migrations
cd backend
alembic upgrade head
```

---

## Configuration

### Environment Variables

**Critical (.env file)**:
```bash
# Security
JWT_SECRET_KEY=<generate-with: python -c "import secrets; print(secrets.token_urlsafe(32))">
ENCRYPTION_KEY=<generate-with: python -c "import secrets; print(secrets.token_urlsafe(32))">

# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=cipherdocs
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
LOG_LEVEL=INFO

# Embedding Service
EMBEDDING_API_URL=http://embedding_service:8001
HF_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2

# CyborgDB
CYBORGDB_API_URL=http://cyborgdb:8002
CYBORGDB_API_KEY=your_cyborgdb_key

# Feature Flags
ENABLE_CACHE=true
ENABLE_AUDIT_LOGGING=true
MAX_FILE_SIZE_MB=100
```

### Docker Compose Overrides

For production, create `docker-compose.override.yml`:

```yaml
services:
  backend:
    environment:
      - LOG_LEVEL=WARNING
      - API_WORKERS=8
    resources:
      limits:
        cpus: '4'
        memory: 8G
      reservations:
        cpus: '2'
        memory: 4G
    
  postgres:
    environment:
      - POSTGRES_INITDB_ARGS=-c max_connections=200
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

---

## Health Checks

### API Health

```bash
# Simple health check
curl http://localhost:8000/health

# Response (200 OK):
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-12-16T10:30:00Z"
}
```

### Service Health (Docker)

```bash
# Check all services
docker-compose -f docker/docker-compose.yml ps

# Check specific service logs
docker logs cyborgdb_backend --tail 50
docker logs cyborgdb_embedding --tail 50
docker logs cyborgdb_postgres --tail 50

# Check service health
docker-compose -f docker/docker-compose.yml exec backend \
  curl -s http://localhost:8000/health | jq '.'
```

### Database Health

```bash
# Connect to PostgreSQL
docker exec -it cyborgdb_postgres psql -U postgres -d cipherdocs

# Check tables
\dt

# Check document count
SELECT COUNT(*) FROM documents;

# Exit
\q
```

---

## Scaling

### Horizontal Scaling (Multiple Instances)

1. **Load Balancer Setup** (nginx)

```nginx
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

server {
    listen 80;
    location /api/ {
        proxy_pass http://backend;
    }
}
```

2. **Database Connection Pool**

```bash
# Edit docker-compose.yml
# Increase max_connections for PostgreSQL
POSTGRES_INITDB_ARGS: "-c max_connections=300"
```

3. **Multiple Backend Instances**

```bash
# Scale backend to 3 instances
docker-compose -f docker/docker-compose.yml up -d --scale backend=3
```

### Vertical Scaling (Single Powerful Instance)

```yaml
# docker-compose.override.yml
services:
  backend:
    environment:
      - API_WORKERS=16  # Increase workers
    resources:
      limits:
        cpus: '16'
        memory: 32G
```

### Caching (Redis)

```bash
# Already configured in docker-compose.yml
# Verify Redis running
docker logs cyborgdb_redis

# Check Redis stats
docker exec cyborgdb_redis redis-cli INFO stats
```

---

## Troubleshooting

### Common Issues

#### 1. Services Won't Start

**Error**: `docker: no such file or directory`

**Solution**:
```bash
# Ensure Docker is running
docker ps

# Reinstall Docker Desktop
# https://docs.docker.com/get-docker/
```

#### 2. Port Already in Use

**Error**: `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process or change port in .env
API_PORT=8001
```

#### 3. Database Connection Failed

**Error**: `psycopg2.OperationalError: could not connect to server`

**Solution**:
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check logs
docker logs cyborgdb_postgres

# Restart PostgreSQL
docker restart cyborgdb_postgres

# Verify connectivity
docker exec cyborgdb_backend \
  psql -h postgres -U postgres -d cipherdocs -c "SELECT 1"
```

#### 4. Embedding Service Timeout

**Error**: `Connection timeout to http://embedding_service:8001`

**Solution**:
```bash
# Wait longer for model download (~2GB)
docker logs cyborgdb_embedding --tail 100

# Check disk space
docker exec cyborgdb_embedding df -h

# Reduce model size in .env
HF_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2  # Smaller
```

#### 5. Out of Memory

**Error**: `Container killed, Out of memory`

**Solution**:
```bash
# Increase Docker memory limit
# Docker Desktop: Settings → Resources → Memory → Increase to 8GB+

# Or reduce services
docker-compose -f docker/docker-compose.yml down redis

# Check memory usage
docker stats
```

#### 6. CORS Errors

**Error**: `Cross-Origin Request Blocked`

**Solution**:
```bash
# Update .env with correct frontend URL
CORS_ORIGINS=["http://localhost:3000"]

# Restart backend
docker-compose -f docker/docker-compose.yml restart backend
```

### Debugging

#### View Logs

```bash
# Follow backend logs
docker logs -f cyborgdb_backend

# All services
docker-compose -f docker/docker-compose.yml logs -f

# Specific time range
docker logs --since 10m cyborgdb_backend
docker logs --until 1h cyborgdb_backend
```

#### Execute Commands in Container

```bash
# Run bash in backend
docker exec -it cyborgdb_backend bash

# Check environment
env | grep -i postgres

# Test API locally
curl -s http://localhost:8000/health | jq '.'
```

#### Database Debugging

```bash
# Connect to database
docker exec -it cyborgdb_postgres psql -U postgres -d cipherdocs

# List tables
\dt

# Check user permissions
SELECT * FROM pg_roles;

# Check current connections
SELECT * FROM pg_stat_activity;

# Check table sizes
\d+

# Exit
\q
```

---

## Production Checklist

### Pre-Deployment

- [ ] All tests passing: `pytest tests/ -v`
- [ ] Security scan complete: `bandit -r app/`
- [ ] Dependencies updated: `pip list --outdated`
- [ ] Environment variables configured
- [ ] Database backup strategy defined
- [ ] SSL certificates obtained
- [ ] Domain name configured
- [ ] Monitoring/alerting set up

### Deployment

- [ ] Database migrations tested: `alembic upgrade head --sql`
- [ ] Secrets stored in secure vault (not in .env)
- [ ] Services started in correct order
- [ ] Health checks passing
- [ ] API responding correctly
- [ ] Frontend accessible
- [ ] Load balancer configured
- [ ] Auto-scaling configured

### Post-Deployment

- [ ] Monitor error logs for 1 hour
- [ ] Test user workflows (signup → upload → search)
- [ ] Verify database replication (if HA setup)
- [ ] Confirm backups running
- [ ] Document deployment changes
- [ ] Set up alerts for key metrics
- [ ] Schedule post-deployment review

### Security

- [ ] HTTPS enforced (redirect HTTP → HTTPS)
- [ ] API rate limiting enabled
- [ ] CORS configured correctly
- [ ] Secrets not in logs
- [ ] Audit logging enabled
- [ ] Regular security updates scheduled
- [ ] Incident response procedure documented

### Monitoring

- [ ] Application metrics (latency, throughput)
- [ ] System metrics (CPU, memory, disk)
- [ ] Database metrics (connection pool, slow queries)
- [ ] Error tracking configured
- [ ] Log aggregation set up
- [ ] Alerts configured (response time, error rate, disk usage)
- [ ] On-call rotation established

---

## Backup & Disaster Recovery

### Database Backup

```bash
# Daily backup (add to cron)
docker exec cyborgdb_postgres \
  pg_dump -U postgres cipherdocs | gzip > backup_$(date +%Y%m%d).sql.gz

# Restore from backup
docker exec -i cyborgdb_postgres \
  psql -U postgres cipherdocs < backup_20251216.sql

# Verify backup
gzip -t backup_20251216.sql.gz && echo "Backup OK"
```

### Docker Volume Backup

```bash
# Backup named volumes
docker run --rm -v postgres_data:/data -v $(pwd):/backup \
  ubuntu tar czf /backup/postgres_data.tar.gz -C / data

# Restore
docker run --rm -v postgres_data:/data -v $(pwd):/backup \
  ubuntu tar xzf /backup/postgres_data.tar.gz -C /
```

### Disaster Recovery Procedure

1. **Database Lost**:
   - Stop services: `docker-compose down`
   - Restore volume: `docker run ... restore postgres_data.tar.gz`
   - Start services: `docker-compose up -d`

2. **Application Code Corrupted**:
   - Stop container: `docker-compose down`
   - Pull latest: `git pull origin main`
   - Rebuild: `docker-compose build`
   - Start: `docker-compose up -d`

3. **Complete System Failure**:
   - Follow production deployment from scratch
   - Restore database from latest backup
   - Run migrations: `alembic upgrade head`

---

## Performance Tuning

### PostgreSQL

```bash
# Update docker-compose.yml
environment:
  POSTGRES_INITDB_ARGS: |
    -c max_connections=300
    -c shared_buffers=4GB
    -c effective_cache_size=12GB
    -c work_mem=20MB
    -c maintenance_work_mem=1GB
```

### Backend (Uvicorn)

```bash
# Increase worker processes
uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 8 \
  --worker-class uvicorn.workers.UvicornWorker
```

### Redis Caching

```bash
# Configure cache in .env
CACHE_TTL=3600  # 1 hour
CACHE_MAX_SIZE=1000
```

---

## Support & Updates

### Getting Help

1. **Check logs**: `docker logs cyborgdb_backend`
2. **Review docs**: [API Docs](API_DOCUMENTATION.md)
3. **Check issues**: GitHub Issues
4. **Contact support**: support@example.com

### Staying Updated

```bash
# Pull latest changes
git pull origin main

# Rebuild images
docker-compose build

# Restart services
docker-compose up -d
```

---

**Last Updated**: December 16, 2025  
**Version**: 1.0  
**Status**: ✅ Production Ready
