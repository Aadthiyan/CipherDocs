# Developer Guide - CipherDocs

## Quick Start for Developers

Get CipherDocs running locally in 10 minutes.

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 13+
- Git

### Local Setup

```bash
# 1. Clone repo
git clone https://github.com/your-org/cipherdocs.git
cd cipherdocs

# 2. Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt

# 3. Configure local .env
cat > .env << EOF
POSTGRES_HOST=localhost
POSTGRES_DB=cipherdocs_dev
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
JWT_SECRET_KEY=dev-key-not-for-production
API_PORT=8000
EMBEDDING_API_URL=http://localhost:8001
EOF

# 4. Start PostgreSQL (Docker)
docker run -d \
  --name cyborgdb_postgres_dev \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=cipherdocs_dev \
  -p 5432:5432 \
  postgres:15-alpine

# 5. Initialize database
alembic upgrade head

# 6. Start backend
python main.py
# Runs on http://localhost:8000

# 7. In another terminal, start embedding service
cd embedding_service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
# Runs on http://localhost:8001

# 8. In another terminal, start frontend
cd frontend
npm install
echo "REACT_APP_API_URL=http://localhost:8000" > .env
npm start
# Runs on http://localhost:3000
```

✅ **Development environment running!**

---

## Project Structure

```
cipherdocs/
├── backend/                          # Python FastAPI backend
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py              # Authentication endpoints
│   │   │   ├── documents.py         # Document management
│   │   │   ├── search.py            # Search endpoints
│   │   │   └── analytics.py         # Analytics endpoints
│   │   ├── core/
│   │   │   ├── config.py            # Configuration
│   │   │   ├── security.py          # Security utilities
│   │   │   └── exceptions.py        # Custom exceptions
│   │   ├── models/
│   │   │   ├── user.py              # User database model
│   │   │   ├── document.py          # Document model
│   │   │   └── chunk.py             # Document chunk model
│   │   ├── schemas/
│   │   │   ├── auth.py              # Pydantic schemas for auth
│   │   │   ├── document.py          # Document schemas
│   │   │   └── search.py            # Search schemas
│   │   ├── services/
│   │   │   ├── auth_service.py      # Auth logic
│   │   │   ├── document_service.py  # Document processing
│   │   │   ├── search_service.py    # Search logic
│   │   │   └── embedding_service.py # Embedding calls
│   │   ├── db/
│   │   │   ├── database.py          # Database connection
│   │   │   └── models.py            # SQLAlchemy models
│   │   └── middleware/
│   │       ├── auth.py              # Auth middleware
│   │       └── logging.py           # Request logging
│   ├── tests/
│   │   ├── test_auth.py
│   │   ├── test_documents.py
│   │   ├── test_search.py
│   │   └── conftest.py              # Pytest fixtures
│   ├── main.py                      # Application entry point
│   ├── requirements.txt             # Python dependencies
│   └── README.md                    # Backend documentation
│
├── embedding_service/                # Embedding generation microservice
│   ├── main.py                       # Service entry point
│   ├── requirements.txt
│   └── README.md
│
├── frontend/                         # React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── App.tsx
│   │   └── index.tsx
│   ├── public/
│   ├── package.json
│   └── README.md
│
├── docker/                           # Docker configuration
│   ├── docker-compose.yml
│   ├── backend.Dockerfile
│   ├── embedding.Dockerfile
│   └── frontend.Dockerfile
│
├── tests/                            # Integration tests
│   ├── test_auth_flow.py
│   ├── test_document_flow.py
│   ├── test_search_flow.py
│   └── conftest.py
│
├── docs/                             # Documentation
│   ├── API_DOCUMENTATION.md
│   ├── DEPLOYMENT_GUIDE.md
│   ├── ARCHITECTURE.md
│   └── SECURITY.md
│
└── README.md                         # Main project README
```

---

## Key Components

### 1. Authentication Service (`app/services/auth_service.py`)

Handles user signup, login, password hashing, and JWT token generation.

```python
from app.services.auth_service import AuthService
from app.schemas.auth import SignupRequest, LoginRequest

auth_service = AuthService()

# Sign up user
user = auth_service.signup(SignupRequest(
    email="user@example.com",
    password="secure_pass",
    full_name="John Doe"
))

# Login user
tokens = auth_service.login(LoginRequest(
    email="user@example.com",
    password="secure_pass"
))

# Verify token
user_id = auth_service.verify_token(tokens.access_token)
```

### 2. Document Service (`app/services/document_service.py`)

Handles document upload, chunking, embedding, and storage.

```python
from app.services.document_service import DocumentService

doc_service = DocumentService()

# Upload and process document
document = doc_service.upload_document(
    file=uploaded_file,
    tenant_id=tenant_id,
    user_id=user_id
)

# Get document details
doc = doc_service.get_document(document_id, tenant_id)

# Delete document (GDPR)
doc_service.delete_document(document_id, tenant_id)
```

### 3. Search Service (`app/services/search_service.py`)

Performs semantic search on encrypted embeddings.

```python
from app.services.search_service import SearchService

search_service = SearchService()

# Search documents
results = search_service.search(
    query="machine learning",
    tenant_id=tenant_id,
    top_k=10,
    threshold=0.5
)

# Results include:
# - document_id, filename, chunk_id
# - text snippet, similarity_score
# - chunk_sequence position
```

### 4. Embedding Service Client

Communicates with embedding microservice for vector generation.

```python
from app.services.embedding_service import EmbeddingServiceClient

embedding_client = EmbeddingServiceClient("http://localhost:8001")

# Generate embeddings
embeddings = embedding_client.embed_texts([
    "Text chunk 1",
    "Text chunk 2",
])
# Returns: List[List[float]] - 768-dim vectors
```

### 5. Encryption Service (`app/core/security/encryption.py`)

Manages encryption of embeddings and sensitive data.

```python
from app.core.security.encryption import EncryptionService

encryption_svc = EncryptionService()

# Encrypt embedding
encrypted = encryption_svc.encrypt_embedding(
    embedding=[0.1, 0.2, ...],
    tenant_key=tenant_encryption_key
)

# Decrypt (decryption happens server-side)
plaintext = encryption_svc.decrypt_embedding(encrypted, tenant_key)
```

---

## Database Models

### User Model

```python
class User(Base):
    __tablename__ = "users"
    
    id: UUID
    tenant_id: UUID                    # Multi-tenant isolation
    email: str                         # Unique per tenant
    password_hash: str                 # bcrypt hashed
    full_name: str
    role: str                          # admin, user, viewer
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    documents: List[Document]          # Relationship
```

### Document Model

```python
class Document(Base):
    __tablename__ = "documents"
    
    id: UUID
    tenant_id: UUID                    # Multi-tenant isolation
    filename: str
    file_size_bytes: int
    status: str                        # pending, processing, completed
    doc_type: str                      # application/pdf, text/plain
    uploaded_by: UUID                  # User who uploaded
    storage_path: str                  # S3 path
    created_at: datetime
    updated_at: datetime
    
    chunks: List[DocumentChunk]        # Relationship
```

### DocumentChunk Model

```python
class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id: UUID
    doc_id: UUID                       # Foreign key
    tenant_id: UUID                    # Multi-tenant isolation
    text: str                          # Chunk text
    chunk_sequence: int                # Order in document
    encrypted_embedding: bytes         # AES-256-GCM encrypted
    created_at: datetime
```

---

## Adding New Endpoints

### Step 1: Define Schema (Pydantic)

```python
# app/schemas/myfeature.py
from pydantic import BaseModel

class MyFeatureRequest(BaseModel):
    query: str
    param: str

class MyFeatureResponse(BaseModel):
    result: str
    timestamp: datetime
```

### Step 2: Create Service Logic

```python
# app/services/myfeature_service.py
from app.db.database import SessionLocal
from app.models import Document

class MyFeatureService:
    def __init__(self):
        self.db = SessionLocal()
    
    def process(self, request, tenant_id):
        # Your business logic here
        docs = self.db.query(Document).filter(
            Document.tenant_id == tenant_id
        ).all()
        return {"result": "success"}
```

### Step 3: Create API Endpoint

```python
# app/api/myfeature.py
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.myfeature import MyFeatureRequest, MyFeatureResponse
from app.services.myfeature_service import MyFeatureService
from app.core.security import get_current_user

router = APIRouter(prefix="/myfeature", tags=["myfeature"])
service = MyFeatureService()

@router.post("", response_model=MyFeatureResponse)
async def create_feature(
    request: MyFeatureRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create feature
    
    - **query**: Search query string
    - **param**: Optional parameter
    """
    result = service.process(request, current_user.tenant_id)
    return MyFeatureResponse(**result)
```

### Step 4: Register Router

```python
# main.py
from app.api.myfeature import router as myfeature_router

app.include_router(myfeature_router, prefix="/api")
```

### Step 5: Write Tests

```python
# tests/test_myfeature.py
import pytest
from app.schemas.myfeature import MyFeatureRequest

@pytest.mark.asyncio
async def test_create_feature(client, auth_headers):
    response = await client.post(
        "/api/myfeature",
        json={"query": "test", "param": "value"},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["result"] == "success"
```

---

## Running Tests

### Unit Tests

```bash
cd backend

# Run all unit tests
pytest tests/ -v

# Run specific test file
pytest tests/test_auth.py -v

# Run specific test
pytest tests/test_auth.py::test_login -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

### Integration Tests

```bash
# Integration tests (requires services running)
pytest tests/test_integration_*.py -v

# Specific integration test
pytest tests/test_integration_document_flow.py -v
```

### Performance Tests

```bash
# Run benchmarks
pytest benchmarks/ -v -s

# Specific benchmark
pytest benchmarks/test_search_performance.py -v
```

### Test Configuration

```python
# tests/conftest.py - Pytest fixtures
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def db():
    """In-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture
def client(db):
    """FastAPI test client"""
    from fastapi.testclient import TestClient
    from main import app
    
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)
```

---

## Code Style & Standards

### Python Code Style

```bash
# Format code
black app/ tests/

# Check style
flake8 app/ tests/

# Type checking
mypy app/

# Security scan
bandit -r app/

# All checks together
make lint  # if Makefile present
```

### Import Organization

```python
# Standard library
import json
import os
from datetime import datetime
from typing import List, Optional

# Third-party
from fastapi import FastAPI, Depends
from sqlalchemy import Column, String

# Local
from app.core.config import settings
from app.models import User
```

### Naming Conventions

```python
# Classes: PascalCase
class AuthService:
    pass

# Functions/methods: snake_case
def get_user_documents():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_FILE_SIZE_MB = 100

# Private attributes: _leading_underscore
def _private_helper():
    pass
```

### Documentation

```python
def search_documents(
    query: str,
    tenant_id: UUID,
    top_k: int = 10,
    threshold: float = 0.5
) -> List[SearchResult]:
    """
    Search documents using semantic similarity.
    
    Args:
        query: Search query string
        tenant_id: Tenant identifier
        top_k: Number of results (default: 10)
        threshold: Minimum similarity score (default: 0.5)
    
    Returns:
        List of SearchResult objects
    
    Raises:
        ValueError: If query is empty
        TenantIsolationError: If cross-tenant access attempted
    """
    if not query:
        raise ValueError("Query cannot be empty")
    # ... implementation
```

---

## Debugging

### Enable Debug Logging

```python
# main.py
import logging
logging.basicConfig(level=logging.DEBUG)

# or via environment
export LOG_LEVEL=DEBUG
python main.py
```

### Database Debugging

```python
# View SQL queries
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    print(f"Executing: {statement}")
    print(f"Parameters: {parameters}")
```

### Breakpoint Debugging

```python
# Using pdb (Python debugger)
import pdb

def my_function():
    pdb.set_trace()  # Execution will pause here
    # Use commands: n (next), s (step), c (continue), p (print)
```

### Using IDE Debugger (VS Code)

```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["main:app", "--reload"],
      "jinja": true,
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

---

## Environment Variables

### Development `.env`

```bash
# Database (local PostgreSQL)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=cipherdocs_dev
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# API
API_HOST=127.0.0.1
API_PORT=8000
DEBUG=true
LOG_LEVEL=DEBUG

# JWT
JWT_SECRET_KEY=dev-secret-change-in-production

# Services
EMBEDDING_API_URL=http://localhost:8001
CYBORGDB_API_URL=http://localhost:8002

# Features
ENABLE_DOCS=true
CORS_ORIGINS=["http://localhost:3000"]
```

### Production `.env`

```bash
# Never commit production .env!
# Use secrets manager (AWS Secrets Manager, Vault, etc.)

# Database
POSTGRES_HOST=prod-db.example.com
POSTGRES_DB=cipherdocs_prod
# ... other production settings

# Use environment variables, not file
# source /etc/cipherdocs/env.prod
```

---

## Common Tasks

### Add New Permission/Role

```python
# app/models/user.py
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    EDITOR = "editor"  # New role

# app/core/security.py
def require_role(required_role: UserRole):
    async def check_role(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return check_role

# Usage in endpoint
@app.post("/admin/users")
async def create_user(
    request: CreateUserRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    # Only admins can create users
    pass
```

### Add New Database Field

```python
# 1. Update model
# app/models/document.py
class Document(Base):
    # ... existing fields
    metadata_json: str = Column(String, nullable=True)  # New field

# 2. Create migration
alembic revision --autogenerate -m "Add metadata_json to documents"

# 3. Review migration (alembic/versions/*)
# 4. Apply migration
alembic upgrade head

# 5. Update schema
# app/schemas/document.py
class DocumentResponse(BaseModel):
    # ... existing fields
    metadata_json: Optional[str] = None

# 6. Update service logic
# app/services/document_service.py
def get_document(...):
    # Include new field in response
```

### Add New Environment Variable

```python
# 1. Update config
# app/core/config.py
class Settings(BaseSettings):
    my_new_setting: str = Field(default="value", env="MY_NEW_SETTING")

# 2. Add to .env
MY_NEW_SETTING=production_value

# 3. Use in code
from app.core.config import settings
print(settings.my_new_setting)
```

---

## Contributing

### Code Review Checklist

Before submitting a PR:
- [ ] Code follows style guide
- [ ] All tests pass: `pytest tests/ -v`
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] No hardcoded values
- [ ] No secrets in code
- [ ] Docstrings added
- [ ] Type hints included

### Commit Message Format

```
<type>: <subject>

<body>

Fixes #<issue_number>
```

Types: feat, fix, docs, style, refactor, test, chore

Example:
```
feat: Add document export functionality

- Implement CSV and JSON export formats
- Add export endpoint
- Include tests
- Update documentation

Fixes #123
```

---

## Useful Commands

```bash
# Format code
black app/ tests/

# Type checking
mypy app/

# Security scan
bandit -r app/

# Run tests with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test module
pytest tests/test_auth.py -v

# Run tests matching pattern
pytest -k "test_login" -v

# Lint
flake8 app/

# Build Docker image
docker build -f docker/backend.Dockerfile -t cipherdocs:latest .

# Start local services
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose logs -f backend

# Database migrations
alembic upgrade head       # Apply migrations
alembic downgrade -1       # Rollback one migration
alembic revision -m "description"  # Create new migration
```

---

## Further Reading

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Pydantic Validation](https://pydantic-docs.helpmanual.io/)

---

**Last Updated**: December 16, 2025  
**Version**: 1.0  
**Status**: ✅ Complete
