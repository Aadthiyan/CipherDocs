from datetime import datetime, timedelta
from typing import Optional, Union, Any, Dict
from jose import jwt, JWTError

# Workaround for bcrypt/passlib initialization bug with Python 3.13
# Initialize bcrypt directly before passlib tries to use it
import bcrypt
try:
    # This prevents passlib from failing during its internal bug detection
    bcrypt.hashpw(b"init", bcrypt.gensalt())
except:
    pass

from passlib.context import CryptContext
from app.core.config import settings

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Bcrypt has a 72-byte limit, so we truncate to 72 bytes.
    This is safe because our validation limits passwords to 100 chars anyway.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    # Truncate to 72 bytes (not characters) to avoid bcrypt's byte limit
    # UTF-8 characters can be multiple bytes, so we must truncate by bytes
    password_bytes = password.encode('utf-8')[:72]
    truncated = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.hash(truncated)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash using constant-time comparison.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    # Apply same 72-byte truncation as hash_password
    password_bytes = plain_password.encode('utf-8')[:72]
    truncated = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.verify(truncated, hashed_password)


def create_access_token(
    subject: Union[str, Any],
    tenant_id: str,
    role: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token with tenant context and role.
    
    Args:
        subject: The user ID or subject identifier
        tenant_id: The tenant identifier
        role: The user's role (admin, user, viewer)
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    to_encode = {
        "sub": str(subject),
        "tenant_id": str(tenant_id),
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def create_refresh_token(
    subject: Union[str, Any],
    tenant_id: str,
    role: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        subject: The user ID or subject identifier
        tenant_id: The tenant identifier
        role: The user's role (admin, user, viewer)
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRATION_DAYS)
    
    to_encode = {
        "sub": str(subject),
        "tenant_id": str(tenant_id),
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    }
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a JWT token and return its payload.
    
    Args:
        token: The JWT token string
        
    Returns:
        Dict containing the payload if valid, None otherwise
    """
    try:
        # decode validates the signature and expiration by default
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def verify_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a refresh token and return its payload.
    
    Validates that:
    - Token signature is valid
    - Token has not expired
    - Token type is 'refresh'
    
    Args:
        token: The JWT refresh token string
        
    Returns:
        Dict containing the payload if valid, None otherwise
    """
    try:
        # Decode and validate token
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Verify token type
        if payload.get("type") != "refresh":
            return None
        
        return payload
    except JWTError:
        return None

