from typing import Dict, Any, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from sqlalchemy.orm import Session
import uuid

from app.core import security
from app.core.tenant_context import set_tenant_context
from app.schemas.auth import TokenPayload
from app.db.database import get_db
from app.models.database import User, Tenant

# OAuth2PasswordBearer defines where the client should look for the token (Authorization header)
# and where to send the user for authentication (tokenUrl) in the Swagger UI.
# We'll assume a standard login route for now.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user_claims(
    token: str = Depends(oauth2_scheme)
) -> TokenPayload:
    """
    Dependency to validate the JWT token and return the claims.
    This ensures that the request is authenticated.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify the token signature and expiration
    payload_dict = security.verify_token(token)
    if payload_dict is None:
        raise credentials_exception
        
    try:
        # Validate the payload structure
        token_payload = TokenPayload(**payload_dict)
        
        # Ensure critical fields are present
        if token_payload.sub is None or token_payload.tenant_id is None:
            raise credentials_exception
            
        return token_payload
        
    except (ValidationError, ValueError):
        raise credentials_exception

async def get_current_user(
    claims: TokenPayload = Depends(get_current_user_claims),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from database.
    Validates that user exists and is active.
    """
    try:
        user_id = uuid.UUID(claims.sub)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


async def get_current_tenant(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Tenant:
    """
    Dependency to get the current tenant from database.
    Validates that tenant exists and is active.
    """
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tenant not found"
        )
    
    if not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant account is suspended"
        )
    
    return tenant


async def get_current_tenant_id(
    claims: TokenPayload = Depends(get_current_user_claims)
) -> str:
    """
    Dependency to extract just the tenant_id from the valid token.
    Useful for endpoints that only care about tenant isolation.
    Fast alternative to get_current_tenant when you don't need the full object.
    """
    if not claims.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing tenant context"
        )
    
    # Ensure tenant context is set (failsafe if middleware didn't run)
    set_tenant_context(claims.tenant_id, claims.sub)
    
    return claims.tenant_id


def verify_tenant_access(resource_tenant_id: uuid.UUID, current_tenant_id: str) -> None:
    """
    Verify that the current tenant has access to a resource.
    Raises 403 Forbidden if tenant IDs don't match.
    
    Args:
        resource_tenant_id: The tenant_id of the resource being accessed
        current_tenant_id: The tenant_id from the JWT token
        
    Raises:
        HTTPException: 403 if tenant IDs don't match
    """
    try:
        current_tenant_uuid = uuid.UUID(current_tenant_id)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid tenant ID in token"
        )
    
    if resource_tenant_id != current_tenant_uuid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: resource belongs to different tenant"
        )
