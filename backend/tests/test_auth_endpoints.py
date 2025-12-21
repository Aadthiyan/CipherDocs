"""
Tests for authentication endpoints (signup and login)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.models.database import User, Tenant
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


# ============================================================================
# SIGNUP TESTS
# ============================================================================

def test_signup_success(client):
    """Test successful user signup"""
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "admin@testcorp.com",
            "password": "SecurePass123",
            "company_name": "Test Corporation"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Check response structure
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert "tenant" in data
    
    # Check user data
    assert data["user"]["email"] == "admin@testcorp.com"
    assert data["user"]["role"] == "admin"
    assert data["user"]["is_active"] is True
    
    # Check tenant data
    assert data["tenant"]["name"] == "Test Corporation"
    assert data["tenant"]["plan"] == "starter"
    assert data["tenant"]["is_active"] is True


def test_signup_duplicate_email(client):
    """Test signup with duplicate email"""
    # First signup
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "duplicate@test.com",
            "password": "SecurePass123",
            "company_name": "First Company"
        }
    )
    
    # Second signup with same email
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "duplicate@test.com",
            "password": "DifferentPass456",
            "company_name": "Second Company"
        }
    )
    
    assert response.status_code == 409
    assert "already registered" in response.json()["detail"].lower()


def test_signup_invalid_email(client):
    """Test signup with invalid email format"""
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "not-an-email",
            "password": "SecurePass123",
            "company_name": "Test Corp"
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_signup_weak_password(client):
    """Test signup with weak password"""
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "test@test.com",
            "password": "weak",  # Too short, no uppercase, no digit
            "company_name": "Test Corp"
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_signup_password_no_uppercase(client):
    """Test signup with password missing uppercase"""
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "test@test.com",
            "password": "lowercase123",
            "company_name": "Test Corp"
        }
    )
    
    assert response.status_code == 422


def test_signup_password_no_digit(client):
    """Test signup with password missing digit"""
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "test@test.com",
            "password": "NoDigitsHere",
            "company_name": "Test Corp"
        }
    )
    
    assert response.status_code == 422


# ============================================================================
# LOGIN TESTS
# ============================================================================

def test_login_success(client):
    """Test successful login"""
    # First create a user
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "login@test.com",
            "password": "SecurePass123",
            "company_name": "Login Test Corp"
        }
    )
    
    # Now login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "login@test.com",
            "password": "SecurePass123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert "tenant" in data
    
    # Check user data
    assert data["user"]["email"] == "login@test.com"
    assert data["user"]["role"] == "admin"


def test_login_invalid_email(client):
    """Test login with non-existent email"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@test.com",
            "password": "SomePassword123"
        }
    )
    
    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


def test_login_wrong_password(client):
    """Test login with wrong password"""
    # Create user
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "wrongpass@test.com",
            "password": "CorrectPass123",
            "company_name": "Test Corp"
        }
    )
    
    # Try to login with wrong password
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrongpass@test.com",
            "password": "WrongPass123"
        }
    )
    
    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


def test_login_rate_limiting(client):
    """Test rate limiting on failed login attempts"""
    # Create user
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "ratelimit@test.com",
            "password": "CorrectPass123",
            "company_name": "Test Corp"
        }
    )
    
    # Make 5 failed login attempts
    for i in range(5):
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "ratelimit@test.com",
                "password": "WrongPassword123"
            }
        )
        # First 5 should be 401
        assert response.status_code == 401
    
    # 6th attempt should be rate limited
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "ratelimit@test.com",
            "password": "WrongPassword123"
        }
    )
    
    assert response.status_code == 429  # Too Many Requests
    assert "too many" in response.json()["detail"].lower()


def test_login_clears_rate_limit_on_success(client):
    """Test that successful login clears rate limiting"""
    # Create user
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "clearrate@test.com",
            "password": "CorrectPass123",
            "company_name": "Test Corp"
        }
    )
    
    # Make 3 failed attempts
    for i in range(3):
        client.post(
            "/api/v1/auth/login",
            json={
                "email": "clearrate@test.com",
                "password": "WrongPassword123"
            }
        )
    
    # Successful login should clear the counter
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "clearrate@test.com",
            "password": "CorrectPass123"
        }
    )
    
    assert response.status_code == 200


# ============================================================================
# PASSWORD HASHING TESTS
# ============================================================================

def test_password_is_hashed(client):
    """Test that passwords are hashed in database"""
    from app.core.security import verify_password
    
    # Create user
    client.post(
        "/api/v1/auth/signup",
        json={
            "email": "hashtest@test.com",
            "password": "PlainPassword123",
            "company_name": "Hash Test Corp"
        }
    )
    
    # Check database directly
    db = next(override_get_db())
    user = db.query(User).filter(User.email == "hashtest@test.com").first()
    
    # Password hash should not equal plain password
    assert user.password_hash != "PlainPassword123"
    
    # But verification should work
    assert verify_password("PlainPassword123", user.password_hash)
    
    # Wrong password should not verify
    assert not verify_password("WrongPassword123", user.password_hash)


# ============================================================================
# TOKEN VALIDATION TESTS
# ============================================================================

def test_tokens_are_valid_jwt(client):
    """Test that returned tokens are valid JWTs"""
    from app.core.security import verify_token
    
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "tokentest@test.com",
            "password": "SecurePass123",
            "company_name": "Token Test Corp"
        }
    )
    
    data = response.json()
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]
    
    # Verify access token
    access_payload = verify_token(access_token)
    assert access_payload is not None
    assert access_payload["type"] == "access"
    assert access_payload["role"] == "admin"
    
    # Verify refresh token
    refresh_payload = verify_token(refresh_token)
    assert refresh_payload is not None
    assert refresh_payload["type"] == "refresh"
