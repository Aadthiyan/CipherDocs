import pytest
from datetime import timedelta
import time
from fastapi import HTTPException
from app.core import security
from app.api import deps
from app.schemas.auth import TokenPayload

# --- security.py tests ---

def test_create_access_token():
    user_id = "test_user"
    tenant_id = "test_tenant"
    role = "admin"
    
    token = security.create_access_token(
        subject=user_id,
        tenant_id=tenant_id,
        role=role
    )
    
    assert isinstance(token, str)
    assert len(token) > 0

def test_verify_valid_token():
    user_id = "test_user_2"
    tenant_id = "test_tenant_2"
    role = "user"
    
    token = security.create_access_token(
        subject=user_id,
        tenant_id=tenant_id,
        role=role
    )
    
    payload = security.verify_token(token)
    assert payload is not None
    assert payload["sub"] == user_id
    assert payload["tenant_id"] == tenant_id
    assert payload["role"] == role

def test_verify_expired_token():
    # Create a token that expires in the past
    token = security.create_access_token(
        subject="expired_user",
        tenant_id="t1",
        role="viewer",
        expires_delta=timedelta(seconds=-1)
    )
    
    payload = security.verify_token(token)
    assert payload is None

def test_verify_invalid_signature():
    # Create a valid token
    token = security.create_access_token("u1", "t1", "admin")
    
    # Tamper with the token (change the payload part)
    # JWT structure: header.payload.signature
    parts = token.split('.')
    # Base64 encoded '{"sub":"u1",...}' -> Let's just change simple char
    tampered_token = parts[0] + "." + parts[1][:-1] + "a" + "." + parts[2]
    
    payload = security.verify_token(tampered_token)
    assert payload is None

def test_verify_nonsense_token():
    assert security.verify_token("not_a_jwt") is None

def test_create_refresh_token():
    token = security.create_refresh_token("u_ref", "t_ref", "user")
    payload = security.verify_token(token)
    assert payload["type"] == "refresh"
    assert payload["sub"] == "u_ref"

# --- deps.py tests ---

@pytest.mark.asyncio
async def test_get_current_user_claims_valid():
    token = security.create_access_token("u_dep", "t_dep", "admin")
    claims = await deps.get_current_user_claims(token)
    
    assert isinstance(claims, TokenPayload)
    assert claims.sub == "u_dep"
    assert claims.tenant_id == "t_dep"

@pytest.mark.asyncio
async def test_get_current_user_claims_invalid():
    with pytest.raises(HTTPException) as exc:
        await deps.get_current_user_claims("invalid_token_string")
    assert exc.value.status_code == 401

@pytest.mark.asyncio
async def test_get_current_user_claims_expired():
    token = security.create_access_token(
        "u_exp", "t_exp", "admin",
        expires_delta=timedelta(seconds=-1)
    )
    with pytest.raises(HTTPException) as exc:
        await deps.get_current_user_claims(token)
    assert exc.value.status_code == 401

@pytest.mark.asyncio
async def test_get_current_tenant_id():
    token = security.create_access_token("u_ten", "target_tenant", "user")
    # Simulate dependency injection by manually calling verify and wrapping in payload
    # Or just call the async function with a mock claims object logic? 
    # Actually get_current_tenant_id depends on get_current_user_claims.
    # In unit testing deps, we can test get_current_tenant_id by passing the claims directly 
    # if we invoke it directly, but it expects a 'claims' argument due to Valid dependency overrides?
    # No, strictly speaking:
    # async def get_current_tenant_id(claims: TokenPayload = Depends(get_current_user_claims))
    # We can call it directly passing 'claims'.
    
    claims = TokenPayload(sub="u_ten", tenant_id="target_tenant", role="user")
    tid = await deps.get_current_tenant_id(claims)
    assert tid == "target_tenant"

@pytest.mark.asyncio
async def test_get_current_tenant_id_missing():
    # Payload without tenant_id (if that's even possible with our validation)
    # But let's say it slipped through or we are testing just the function
    claims = TokenPayload(sub="u_ten", tenant_id=None, role="user")
    
    with pytest.raises(HTTPException):
        await deps.get_current_tenant_id(claims)
