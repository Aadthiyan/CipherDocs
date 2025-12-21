"""
Tests for document upload and management.
"""

import pytest
import uuid
import os
import shutil
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import MagicMock, patch

from app.db.database import Base, get_db
from app.models.database import User, Tenant, Document
from app.core import security
from app.core.storage import LocalFileSystemStorage
from main import app

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Temporary storage for tests
TEST_STORAGE_PATH = "./test_storage"

def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def test_db():
    """Create test database tables"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(test_db):
    """Create test client with database override"""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def clean_storage():
    """Clean up test storage before and after tests"""
    if os.path.exists(TEST_STORAGE_PATH):
        shutil.rmtree(TEST_STORAGE_PATH)
    os.makedirs(TEST_STORAGE_PATH)
    yield
    if os.path.exists(TEST_STORAGE_PATH):
        shutil.rmtree(TEST_STORAGE_PATH)

@pytest.fixture
def db_session():
    """Get database session for tests"""
    db = next(override_get_db())
    yield db
    db.close()

@pytest.fixture
def tenant(db_session):
    """Create test tenant"""
    tenant = Tenant(
        id=uuid.uuid4(),
        name="Test Corp",
        plan="starter",
        is_active=True
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant

@pytest.fixture
def user(db_session, tenant):
    """Create test user (who has upload permission)"""
    user = User(
        id=uuid.uuid4(),
        email="user@test.com",
        password_hash=security.hash_password("TestPass123"),
        tenant_id=tenant.id,
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def viewer(db_session, tenant):
    """Create viewer user (who CANNOT upload)"""
    user = User(
        id=uuid.uuid4(),
        email="viewer@test.com",
        password_hash=security.hash_password("ViewerPass123"),
        tenant_id=tenant.id,
        role="viewer",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

def get_auth_header(user, tenant):
    """Get authorization header for user"""
    token = security.create_access_token(
        subject=str(user.id),
        tenant_id=str(tenant.id),
        role=user.role
    )
    return {"Authorization": f"Bearer {token}"}

# Mock storage backend used in API
@pytest.fixture
def mock_storage():
    """Mock storage backend"""
    storage = LocalFileSystemStorage(base_path=TEST_STORAGE_PATH)
    with patch("app.api.documents.get_storage_backend", return_value=storage):
        yield storage

# ============================================================================
# DOCUMENT UPLOAD TESTS
# ============================================================================

def test_upload_document_success(client, user, tenant, mock_storage, clean_storage):
    """Test successful document upload"""
    headers = get_auth_header(user, tenant)
    
    # Create a dummy PDF file
    file_content = b"%PDF-1.4\nTest PDF content"
    files = {
        "file": ("test.pdf", file_content, "application/pdf")
    }
    
    response = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files=files
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "test.pdf"
    assert data["status"] == "uploaded"
    assert "id" in data
    
    # Verify file exists on disk (mocked storage points to TEST_STORAGE_PATH)
    storage_path = data["storage_path"]
    assert os.path.exists(os.path.join(TEST_STORAGE_PATH, storage_path))

def test_upload_invalid_file_type(client, user, tenant):
    """Test upload with unsupported file type"""
    headers = get_auth_header(user, tenant)
    
    files = {
        "file": ("test.exe", b"executable content", "application/x-msdownload")
    }
    
    response = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files=files
    )
    
    assert response.status_code == 400
    assert "unsupported file type" in response.json()["detail"].lower()

def test_unique_file_check(client, user, tenant, mock_storage, clean_storage):
    """Test duplicate file upload detection"""
    headers = get_auth_header(user, tenant)
    
    file_content = b"%PDF-1.4\nSame content"
    files = {
        "file": ("test1.pdf", file_content, "application/pdf")
    }
    
    # First upload
    response1 = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files=files
    )
    assert response1.status_code == 201
    
    # Second upload (same content, distinct filename in request but hash same)
    # The endpoint uses hash for detection. 
    # Logic in endpoint: if hash exists -> return existing doc details + message
    
    files["file"] = ("test2.pdf", file_content, "application/pdf") # Reset file stream
    
    response2 = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files=files
    )
    
    assert response2.status_code == 201 # Duplicate returns 200/201 with existing data
    data = response2.json()
    assert data["id"] == response1.json()["id"]
    assert "already exists" in data["message"].lower()

def test_viewer_cannot_upload(client, viewer, tenant, mock_storage):
    """Test viewer role cannot upload"""
    headers = get_auth_header(viewer, tenant)
    
    files = {
        "file": ("test.pdf", b"content", "application/pdf")
    }
    
    response = client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files=files
    )
    
    assert response.status_code == 403

def test_list_documents(client, user, tenant, mock_storage, clean_storage):
    """Test listing documents"""
    headers = get_auth_header(user, tenant)
    
    # Upload 2 docs
    for i in range(2):
        files = {"file": (f"doc{i}.pdf", f"content{i}".encode(), "application/pdf")}
        client.post("/api/v1/documents/upload", headers=headers, files=files)
    
    response = client.get("/api/v1/documents", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["documents"]) == 2
    assert data["total"] == 2

def test_delete_document(client, user, tenant, mock_storage, clean_storage):
    """Test deleting document"""
    headers = get_auth_header(user, tenant)
    
    # Upload doc
    files = {"file": ("todelete.pdf", b"content", "application/pdf")}
    res = client.post("/api/v1/documents/upload", headers=headers, files=files)
    doc_id = res.json()["id"]
    
    # Delete doc
    del_res = client.delete(f"/api/v1/documents/{doc_id}", headers=headers)
    assert del_res.status_code == 200
    
    # Verify deletion in DB
    get_res = client.get(f"/api/v1/documents/{doc_id}", headers=headers)
    assert get_res.status_code == 404

def test_tenant_isolation_list(client, user, tenant, db_session, mock_storage, clean_storage):
    """Test that listing only shows own tenant's documents"""
    headers = get_auth_header(user, tenant)
    
    # Create another tenant & user
    tenant2 = Tenant(id=uuid.uuid4(), name="Other", plan="starter", is_active=True)
    db_session.add(tenant2)
    db_session.commit()
    
    # Upload doc for user (tenant 1)
    files = {"file": ("doc1.pdf", b"content1", "application/pdf")}
    client.post("/api/v1/documents/upload", headers=headers, files=files)
    
    # Manually create a doc for tenant 2 in DB (since we need another token to upload via API)
    doc2 = Document(
        id=uuid.uuid4(),
        tenant_id=tenant2.id,
        filename="doc2.pdf",
        doc_type="pdf",
        file_size_bytes=123,
        file_hash="hash2",
        status="uploaded",
        storage_path="path/to/doc2"
    )
    db_session.add(doc2)
    db_session.commit()
    
    response = client.get("/api/v1/documents", headers=headers)
    data = response.json()
    assert len(data["documents"]) == 1
    assert data["documents"][0]["filename"] == "doc1.pdf"
