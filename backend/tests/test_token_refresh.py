"""
Tests for token refresh and session management.
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import time

from app.db.database import Base, get_db
from app.models.database import User, Tenant
from app.core import security
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
    """Create test user"""
    user = User(
        id=uuid.uuid4(),
        email="test@test.com",
        password_hash=security.hash_password("TestPass123"),
        tenant_id=tenant.id,
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ============================================================================
# TOKEN REFRESH TESTS
# ============================================================================

def test_refresh_token_success(client, user, tenant):
    """Test successful token refresh"""
    # Create refresh token
    refresh_token = security.create_refresh_token(
        subject=str(user.id),
        tenant_id=str(tenant.id),
        role=user.role
    )
    
    # Refresh token
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    
    # Verify new tokens are different (token rotation)
    assert data["refresh_token"] != refresh_token


def test_refresh_token_with_invalid_token(client):
    """Test refresh with invalid token"""
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid_token"}
    )
    
    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


def test_refresh_token_with_access_token(client, user, tenant):
    """Test refresh with access token (should fail)"""
    # Create access token (not refresh token)
    access_token = security.create_access_token(
        subject=str(user.id),
        tenant_id=str(tenant.id),
        role=user.role
    )
    
    # Try to use access token for refresh
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": access_token}
    )
    
    assert response.status_code == 401


def test_refresh_token_for_inactive_user(client, user, tenant, db_session):
    """Test refresh token fails for inactive user"""
    # Create refresh token
    refresh_token = security.create_refresh_token(
        subject=str(user.id),
        tenant_id=str(tenant.id),
        role=user.role
    )
    
    # Deactivate user
    user.is_active = False
    db_session.commit()
    
    # Try to refresh
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    
    assert response.status_code == 403
    assert "inactive" in response.json()["detail"].lower()


def test_refresh_token_for_suspended_tenant(client, user, tenant, db_session):
    """Test refresh token fails for suspended tenant"""
    # Create refresh token
    refresh_token = security.create_refresh_token(
        subject=str(user.id),
        tenant_id=str(tenant.id),
        role=user.role
    )
    
    # Suspend tenant
    tenant.is_active = False
    db_session.commit()
    
    # Try to refresh
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    
    assert response.status_code == 403
    assert "suspended" in response.json()["detail"].lower()


def test_refresh_token_for_deleted_user(client, tenant, db_session):
    """Test refresh token fails for deleted user"""
    # Create user
    user_id = uuid.uuid4()
    
    # Create refresh token
    refresh_token = security.create_refresh_token(
        subject=str(user_id),
        tenant_id=str(tenant.id),
        role="user"
    )
    
    # Try to refresh (user doesn't exist)
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    
    assert response.status_code == 401


# ============================================================================
# LOGOUT TESTS
# ============================================================================

def test_logout_success(client, user, tenant):
    """Test successful logout"""
    # Create access token
    token = security.create_access_token(
        subject=str(user.id),
        tenant_id=str(tenant.id),
        role=user.role
    )
    
    # Logout
    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
        json={"all_sessions": False}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "logged out" in data["message"].lower()


def test_logout_without_token(client):
    """Test logout without authentication token"""
    response = client.post(
        "/api/v1/auth/logout",
        json={"all_sessions": False}
    )
    
    # Should return 401 (unauthorized)
    assert response.status_code == 401


def test_logout_all_sessions(client, user, tenant):
    """Test logout from all sessions"""
    # Create access token
    token = security.create_access_token(
        subject=str(user.id),
        tenant_id=str(tenant.id),
        role=user.role
    )
    
    # Logout from all sessions
    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
        json={"all_sessions": True}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "all sessions" in data["message"].lower()


# ============================================================================
# TOKEN LIFECYCLE TESTS
# ============================================================================

def test_full_token_lifecycle(client):
    """Test complete token lifecycle: signup -> refresh -> logout"""
    # 1. Signup
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "lifecycle@test.com",
            "password": "LifecyclePass123",
            "company_name": "Lifecycle Corp"
        }
    )
    
    assert signup_response.status_code == 201
    signup_data = signup_response.json()
    initial_refresh_token = signup_data["refresh_token"]
    
    # 2. Refresh token
    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": initial_refresh_token}
    )
    
    assert refresh_response.status_code == 200
    refresh_data = refresh_response.json()
    new_access_token = refresh_data["access_token"]
    
    # 3. Logout
    logout_response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {new_access_token}"}
    )
    
    assert logout_response.status_code == 200


def test_token_rotation_on_refresh(client, user, tenant):
    """Test that refresh tokens are rotated (changed) on each refresh"""
    # Create initial refresh token
    refresh_token_1 = security.create_refresh_token(
        subject=str(user.id),
        tenant_id=str(tenant.id),
        role=user.role
    )
    
    # First refresh
    response_1 = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token_1}
    )
    
    assert response_1.status_code == 200
    refresh_token_2 = response_1.json()["refresh_token"]
    
    # Second refresh with new token
    response_2 = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token_2}
    )
    
    assert response_2.status_code == 200
    refresh_token_3 = response_2.json()["refresh_token"]
    
    # All refresh tokens should be different
    assert refresh_token_1 != refresh_token_2
    assert refresh_token_2 != refresh_token_3
    assert refresh_token_1 != refresh_token_3
