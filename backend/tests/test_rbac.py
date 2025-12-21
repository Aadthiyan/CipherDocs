"""
Tests for Role-Based Access Control (RBAC) and user management.
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.models.database import User, Tenant
from app.core import security
from app.core.rbac import UserRole, Permission, has_permission, check_role_hierarchy
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
def admin_user(db_session, tenant):
    """Create admin user"""
    user = User(
        id=uuid.uuid4(),
        email="admin@test.com",
        password_hash=security.hash_password("AdminPass123"),
        tenant_id=tenant.id,
        role="admin",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def regular_user(db_session, tenant):
    """Create regular user"""
    user = User(
        id=uuid.uuid4(),
        email="user@test.com",
        password_hash=security.hash_password("UserPass123"),
        tenant_id=tenant.id,
        role="user",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def viewer_user(db_session, tenant):
    """Create viewer user"""
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


# ============================================================================
# RBAC PERMISSION TESTS
# ============================================================================

def test_admin_has_all_permissions():
    """Test that admin role has all permissions"""
    assert has_permission("admin", Permission.MANAGE_USERS)
    assert has_permission("admin", Permission.UPLOAD_DOCUMENTS)
    assert has_permission("admin", Permission.VIEW_ANALYTICS)
    assert has_permission("admin", Permission.MANAGE_TENANT)


def test_user_has_document_permissions():
    """Test that user role has document permissions"""
    assert has_permission("user", Permission.UPLOAD_DOCUMENTS)
    assert has_permission("user", Permission.VIEW_DOCUMENTS)
    assert has_permission("user", Permission.SEARCH_DOCUMENTS)
    assert not has_permission("user", Permission.MANAGE_USERS)
    assert not has_permission("user", Permission.VIEW_ANALYTICS)


def test_viewer_has_limited_permissions():
    """Test that viewer role has limited permissions"""
    assert has_permission("viewer", Permission.VIEW_DOCUMENTS)
    assert has_permission("viewer", Permission.SEARCH_DOCUMENTS)
    assert not has_permission("viewer", Permission.UPLOAD_DOCUMENTS)
    assert not has_permission("viewer", Permission.MANAGE_USERS)


def test_role_hierarchy():
    """Test role hierarchy checks"""
    assert check_role_hierarchy("admin", "admin")
    assert check_role_hierarchy("admin", "user")
    assert check_role_hierarchy("admin", "viewer")
    assert not check_role_hierarchy("user", "admin")
    assert not check_role_hierarchy("viewer", "user")


# ============================================================================
# USER MANAGEMENT ENDPOINT TESTS
# ============================================================================

def test_admin_can_invite_user(client, admin_user, tenant):
    """Test that admin can invite new users"""
    headers = get_auth_header(admin_user, tenant)
    
    response = client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "email": "newuser@test.com",
            "role": "user"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "user" in data
    assert "temporary_password" in data
    assert data["user"]["email"] == "newuser@test.com"
    assert data["user"]["role"] == "user"


def test_regular_user_cannot_invite_user(client, regular_user, tenant):
    """Test that regular users cannot invite new users"""
    headers = get_auth_header(regular_user, tenant)
    
    response = client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "email": "newuser@test.com",
            "role": "user"
        }
    )
    
    assert response.status_code == 403
    assert "access denied" in response.json()["detail"].lower()


def test_admin_can_list_users(client, admin_user, regular_user, tenant):
    """Test that admin can list all users"""
    headers = get_auth_header(admin_user, tenant)
    
    response = client.get("/api/v1/users", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert len(data["users"]) >= 2  # At least admin and regular user


def test_regular_user_cannot_list_users(client, regular_user, tenant):
    """Test that regular users cannot list users"""
    headers = get_auth_header(regular_user, tenant)
    
    response = client.get("/api/v1/users", headers=headers)
    
    assert response.status_code == 403


def test_admin_can_update_user_role(client, admin_user, regular_user, tenant):
    """Test that admin can update user roles"""
    headers = get_auth_header(admin_user, tenant)
    
    response = client.patch(
        f"/api/v1/users/{regular_user.id}/role",
        headers=headers,
        json={"role": "viewer"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "viewer"


def test_admin_cannot_demote_self(client, admin_user, tenant):
    """Test that admin cannot demote themselves"""
    headers = get_auth_header(admin_user, tenant)
    
    response = client.patch(
        f"/api/v1/users/{admin_user.id}/role",
        headers=headers,
        json={"role": "user"}
    )
    
    assert response.status_code == 400
    assert "cannot change your own role" in response.json()["detail"].lower()


def test_admin_can_delete_user(client, admin_user, regular_user, tenant):
    """Test that admin can delete users"""
    headers = get_auth_header(admin_user, tenant)
    
    response = client.delete(
        f"/api/v1/users/{regular_user.id}",
        headers=headers
    )
    
    assert response.status_code == 200
    assert "deleted successfully" in response.json()["message"].lower()


def test_admin_cannot_delete_self(client, admin_user, tenant):
    """Test that admin cannot delete themselves"""
    headers = get_auth_header(admin_user, tenant)
    
    response = client.delete(
        f"/api/v1/users/{admin_user.id}",
        headers=headers
    )
    
    assert response.status_code == 400
    assert "cannot delete your own account" in response.json()["detail"].lower()


def test_regular_user_cannot_delete_user(client, regular_user, viewer_user, tenant):
    """Test that regular users cannot delete other users"""
    headers = get_auth_header(regular_user, tenant)
    
    response = client.delete(
        f"/api/v1/users/{viewer_user.id}",
        headers=headers
    )
    
    assert response.status_code == 403


def test_duplicate_email_rejected(client, admin_user, regular_user, tenant):
    """Test that duplicate emails are rejected"""
    headers = get_auth_header(admin_user, tenant)
    
    response = client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "email": regular_user.email,  # Already exists
            "role": "user"
        }
    )
    
    assert response.status_code == 409
    assert "already registered" in response.json()["detail"].lower()


def test_get_user_details(client, admin_user, regular_user, tenant):
    """Test getting user details"""
    headers = get_auth_header(admin_user, tenant)
    
    response = client.get(
        f"/api/v1/users/{regular_user.id}",
        headers=headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == regular_user.email
    assert data["role"] == regular_user.role


def test_update_user_status(client, admin_user, regular_user, tenant):
    """Test updating user active status"""
    headers = get_auth_header(admin_user, tenant)
    
    response = client.patch(
        f"/api/v1/users/{regular_user.id}",
        headers=headers,
        json={"is_active": False}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False


def test_admin_cannot_deactivate_self(client, admin_user, tenant):
    """Test that admin cannot deactivate themselves"""
    headers = get_auth_header(admin_user, tenant)
    
    response = client.patch(
        f"/api/v1/users/{admin_user.id}",
        headers=headers,
        json={"is_active": False}
    )
    
    assert response.status_code == 400
    assert "cannot deactivate your own account" in response.json()["detail"].lower()


# ============================================================================
# CROSS-TENANT ACCESS TESTS
# ============================================================================

def test_cross_tenant_user_access_blocked(client, db_session):
    """Test that users cannot access users from other tenants"""
    # Create second tenant
    tenant2 = Tenant(
        id=uuid.uuid4(),
        name="Other Corp",
        plan="starter",
        is_active=True
    )
    db_session.add(tenant2)
    
    # Create admin for tenant 2
    admin2 = User(
        id=uuid.uuid4(),
        email="admin@other.com",
        password_hash=security.hash_password("AdminPass123"),
        tenant_id=tenant2.id,
        role="admin",
        is_active=True
    )
    db_session.add(admin2)
    db_session.commit()
    
    # Create user for tenant 1
    tenant1 = Tenant(
        id=uuid.uuid4(),
        name="Test Corp",
        plan="starter",
        is_active=True
    )
    db_session.add(tenant1)
    
    admin1 = User(
        id=uuid.uuid4(),
        email="admin@test.com",
        password_hash=security.hash_password("AdminPass123"),
        tenant_id=tenant1.id,
        role="admin",
        is_active=True
    )
    db_session.add(admin1)
    db_session.commit()
    
    # Try to access tenant2's admin from tenant1's admin
    headers = get_auth_header(admin1, tenant1)
    
    response = client.get(
        f"/api/v1/users/{admin2.id}",
        headers=headers
    )
    
    # Should return 404 (not found for this tenant)
    assert response.status_code == 404
