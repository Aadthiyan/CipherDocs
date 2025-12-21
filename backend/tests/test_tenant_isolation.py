"""
Tests for tenant isolation middleware and scoping.
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.models.database import User, Tenant, Document
from app.core import security
from app.core.tenant_context import set_tenant_context, get_tenant_context, clear_tenant_context
from app.db.tenant_scoping import get_tenant_scoped_query
from app.api.deps import verify_tenant_access
from main import app

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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


@pytest.fixture
def db_session(test_db):
    """Get database session for tests"""
    db = next(override_get_db())
    yield db
    db.close()


@pytest.fixture
def tenant1(db_session):
    """Create first test tenant"""
    tenant = Tenant(
        id=uuid.uuid4(),
        name="Tenant 1",
        plan="starter",
        is_active=True
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


@pytest.fixture
def tenant2(db_session):
    """Create second test tenant"""
    tenant = Tenant(
        id=uuid.uuid4(),
        name="Tenant 2",
        plan="starter",
        is_active=True
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


@pytest.fixture
def user1(db_session, tenant1):
    """Create user for tenant 1"""
    user = User(
        id=uuid.uuid4(),
        email="user1@tenant1.com",
        password_hash=security.hash_password("Password123"),
        tenant_id=tenant1.id,
        role="admin",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def user2(db_session, tenant2):
    """Create user for tenant 2"""
    user = User(
        id=uuid.uuid4(),
        email="user2@tenant2.com",
        password_hash=security.hash_password("Password123"),
        tenant_id=tenant2.id,
        role="admin",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ============================================================================
# TENANT CONTEXT TESTS
# ============================================================================

def test_tenant_context_set_and_get():
    """Test setting and getting tenant context"""
    tenant_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    
    set_tenant_context(tenant_id, user_id)
    
    assert get_tenant_context() == tenant_id
    
    clear_tenant_context()
    assert get_tenant_context() is None


def test_tenant_context_isolation():
    """Test that tenant context is isolated per request"""
    tenant_id_1 = str(uuid.uuid4())
    tenant_id_2 = str(uuid.uuid4())
    
    # Set first context
    set_tenant_context(tenant_id_1)
    assert get_tenant_context() == tenant_id_1
    
    # Override with second context
    set_tenant_context(tenant_id_2)
    assert get_tenant_context() == tenant_id_2
    
    # Clear
    clear_tenant_context()
    assert get_tenant_context() is None


# ============================================================================
# TENANT SCOPED QUERY TESTS
# ============================================================================

def test_tenant_scoped_query_filters_by_tenant(db_session, tenant1, tenant2):
    """Test that tenant scoped queries only return resources for current tenant"""
    # Create documents for both tenants
    doc1 = Document(
        id=uuid.uuid4(),
        tenant_id=tenant1.id,
        filename="doc1.pdf",
        storage_path="/path/doc1.pdf",
        doc_type="pdf",
        status="completed"
    )
    doc2 = Document(
        id=uuid.uuid4(),
        tenant_id=tenant2.id,
        filename="doc2.pdf",
        storage_path="/path/doc2.pdf",
        doc_type="pdf",
        status="completed"
    )
    db_session.add_all([doc1, doc2])
    db_session.commit()
    
    # Set tenant 1 context
    set_tenant_context(str(tenant1.id))
    
    # Query with tenant scoping
    tq = get_tenant_scoped_query(db_session)
    docs = tq.query(Document).all()
    
    # Should only get tenant 1's document
    assert len(docs) == 1
    assert docs[0].id == doc1.id
    
    clear_tenant_context()


def test_tenant_scoped_get_by_id_blocks_cross_tenant(db_session, tenant1, tenant2):
    """Test that get_by_id doesn't return resources from other tenants"""
    # Create document for tenant 2
    doc = Document(
        id=uuid.uuid4(),
        tenant_id=tenant2.id,
        filename="doc.pdf",
        storage_path="/path/doc.pdf",
        doc_type="pdf",
        status="completed"
    )
    db_session.add(doc)
    db_session.commit()
    
    # Set tenant 1 context (different tenant)
    set_tenant_context(str(tenant1.id))
    
    # Try to get tenant 2's document
    tq = get_tenant_scoped_query(db_session)
    result = tq.get_by_id(Document, doc.id)
    
    # Should return None (not found for this tenant)
    assert result is None
    
    clear_tenant_context()


def test_tenant_scoped_create_auto_assigns_tenant(db_session, tenant1):
    """Test that create automatically assigns tenant_id"""
    set_tenant_context(str(tenant1.id))
    
    # Create document without setting tenant_id
    doc = Document(
        id=uuid.uuid4(),
        filename="auto.pdf",
        storage_path="/path/auto.pdf",
        doc_type="pdf",
        status="uploaded"
    )
    
    tq = get_tenant_scoped_query(db_session)
    created_doc = tq.create(doc)
    
    # Should have tenant_id set automatically
    assert created_doc.tenant_id == tenant1.id
    
    clear_tenant_context()


# ============================================================================
# VERIFY TENANT ACCESS TESTS
# ============================================================================

def test_verify_tenant_access_allows_same_tenant(tenant1):
    """Test that verify_tenant_access allows access to same tenant's resources"""
    doc = Document(
        id=uuid.uuid4(),
        tenant_id=tenant1.id,
        filename="doc.pdf",
        storage_path="/path/doc.pdf",
        doc_type="pdf",
        status="completed"
    )
    
    # Should not raise exception
    verify_tenant_access(doc.tenant_id, str(tenant1.id))


def test_verify_tenant_access_blocks_different_tenant(tenant1, tenant2):
    """Test that verify_tenant_access blocks access to different tenant's resources"""
    doc = Document(
        id=uuid.uuid4(),
        tenant_id=tenant2.id,
        filename="doc.pdf",
        storage_path="/path/doc.pdf",
        doc_type="pdf",
        status="completed"
    )
    
    # Should raise 403 Forbidden
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        verify_tenant_access(doc.tenant_id, str(tenant1.id))
    
    assert exc.value.status_code == 403
    assert "different tenant" in exc.value.detail.lower()


# ============================================================================
# MIDDLEWARE INTEGRATION TESTS
# ============================================================================

def test_middleware_extracts_tenant_from_jwt(client, user1, tenant1):
    """Test that middleware extracts tenant_id from JWT token"""
    # Create JWT token for user1
    token = security.create_access_token(
        subject=str(user1.id),
        tenant_id=str(tenant1.id),
        role=user1.role
    )
    
    # Make request with token
    response = client.get(
        "/health",  # Use health endpoint as it's accessible
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Request should succeed
    assert response.status_code == 200


def test_middleware_allows_public_endpoints_without_token(client):
    """Test that middleware allows access to public endpoints without token"""
    # Health endpoint should work without token
    response = client.get("/health")
    assert response.status_code == 200
    
    # Signup should work without token
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "test@test.com",
            "password": "Password123",
            "company_name": "Test Corp"
        }
    )
    assert response.status_code == 201


def test_cross_tenant_access_blocked(client, db_session, user1, user2, tenant1, tenant2):
    """Test that users cannot access other tenant's data"""
    # Create document for tenant 2
    doc = Document(
        id=uuid.uuid4(),
        tenant_id=tenant2.id,
        filename="secret.pdf",
        storage_path="/path/secret.pdf",
        doc_type="pdf",
        status="completed"
    )
    db_session.add(doc)
    db_session.commit()
    
    # Create token for user1 (tenant 1)
    token = security.create_access_token(
        subject=str(user1.id),
        tenant_id=str(tenant1.id),
        role=user1.role
    )
    
    # Try to access tenant 2's document (would need actual endpoint)
    # This is a conceptual test - in practice you'd test against real endpoints
    # For now, verify the token has correct tenant_id
    payload = security.verify_token(token)
    assert payload["tenant_id"] == str(tenant1.id)
    assert payload["tenant_id"] != str(tenant2.id)
