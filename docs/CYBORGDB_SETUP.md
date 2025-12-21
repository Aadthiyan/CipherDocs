# CyborgDB Integration Setup Guide

## 🎉 Your CyborgDB API Key
```
cyborg_917046e34dfd49e08aa7531af35396dc
```

## ✅ What's Been Configured

### 1. Docker Compose Updated
- ✅ Added CyborgDB service container
- ✅ Configured to use PostgreSQL backend
- ✅ Health checks enabled
- ✅ Persistent volume for data

### 2. Backend Requirements Updated
- ✅ Added `cyborgdb>=1.0.0` to requirements.txt

### 3. Environment Variables Needed

Add these to your `backend/.env` file:

```bash
# CyborgDB Configuration
CYBORGDB_API_KEY=cyborg_917046e34dfd49e08aa7531af35396dc
CYBORGDB_ENDPOINT=http://cyborgdb:8002
CYBORGDB_TIMEOUT=30
```

## 🚀 Installation Steps

### Step 1: Pull CyborgDB Docker Image

```bash
cd docker
docker pull cyborgdb-service
```

### Step 2: Install Python SDK

```bash
cd ../backend
pip install cyborgdb
```

### Step 3: Create/Update .env File

```bash
# Copy minimal template
cp .env.minimal .env

# Add CyborgDB settings
echo "" >> .env
echo "# CyborgDB" >> .env
echo "CYBORGDB_API_KEY=cyborg_917046e34dfd49e08aa7531af35396dc" >> .env
echo "CYBORGDB_ENDPOINT=http://cyborgdb:8002" >> .env
echo "CYBORGDB_TIMEOUT=30" >> .env
```

### Step 4: Start All Services

```bash
cd ../docker
docker-compose up --build
```

## 📊 Service URLs

Once running, you'll have:

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | React Dashboard |
| Backend API | http://localhost:8000 | FastAPI |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Embedding Service | http://localhost:8001 | ML Service |
| **CyborgDB** | **http://localhost:8002** | **Vector Database** |
| PostgreSQL | localhost:5432 | Metadata DB |
| Redis | localhost:6379 | Cache |

## 🔧 Verify CyborgDB is Running

```bash
# Check if CyborgDB container is running
docker ps | grep cyborgdb

# Check CyborgDB health
curl http://localhost:8002/health

# View CyborgDB logs
docker-compose logs -f cyborgdb
```

## 📝 Using CyborgDB in Your Code

### Example: Create Tenant Index

```python
from cyborgdb import Client

# Initialize client
client = Client(
    api_key="cyborg_917046e34dfd49e08aa7531af35396dc",
    endpoint="http://cyborgdb:8002"
)

# Create index for tenant
index = client.create_index(
    name="tenant_123",
    dimension=384,
    encrypted=True
)
```

### Example: Insert Vectors

```python
# Upsert encrypted vectors
index.upsert(vectors=[
    {
        "id": "chunk_1",
        "values": [0.1, 0.2, ...],  # 384-dim vector
        "metadata": {
            "doc_id": "doc_123",
            "tenant_id": "tenant_123"
        }
    }
])
```

### Example: Search

```python
# Search encrypted vectors
results = index.query(
    vector=[0.1, 0.2, ...],  # query vector
    top_k=10,
    encrypted=True
)
```

## 🐛 Troubleshooting

### CyborgDB Container Won't Start

```bash
# Check logs
docker-compose logs cyborgdb

# Verify PostgreSQL is running
docker-compose ps postgres

# Restart CyborgDB
docker-compose restart cyborgdb
```

### Connection Refused

```bash
# Make sure you're using the correct endpoint
# Inside Docker network: http://cyborgdb:8002
# From host machine: http://localhost:8002
```

### API Key Issues

```bash
# Verify API key is set
docker-compose exec cyborgdb env | grep CYBORGDB_API_KEY

# Should show: CYBORGDB_API_KEY=cyborg_917046e34dfd49e08aa7531af35396dc
```

## 📦 Complete Architecture

```
┌─────────────────────────────────────────────────────┐
│           Docker Compose Network                     │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Frontend (React) ──► Backend (FastAPI)             │
│      :3000               :8000                       │
│                            │                         │
│                            ├──► PostgreSQL :5432     │
│                            │    (Metadata + Vectors) │
│                            │                         │
│                            ├──► Redis :6379          │
│                            │    (Cache)              │
│                            │                         │
│                            ├──► Embedding :8001      │
│                            │    (Generate Vectors)   │
│                            │                         │
│                            └──► CyborgDB :8002       │
│                                 (Encrypted Search)   │
│                                                      │
└─────────────────────────────────────────────────────┘
```

## ✅ Next Steps

1. **Fix .env file** - Add the 3 required variables
2. **Run migrations** - Create database tables
3. **Start services** - `docker-compose up`
4. **Test CyborgDB** - Verify it's running
5. **Implement Phase 5** - CyborgDB integration code

## 📚 Resources

- **CyborgDB Docs**: https://docs.cyborgdb.com
- **Python SDK**: https://github.com/cyborgdb/python-sdk
- **API Reference**: http://localhost:8002/docs (when running)

---

**Your API Key (save this!):**
```
cyborg_917046e34dfd49e08aa7531af35396dc
```
