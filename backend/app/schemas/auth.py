from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
import uuid

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    tenant_id: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None
    iat: Optional[int] = None
    type: Optional[str] = "access"


class SignupRequest(BaseModel):
    """Request model for user signup"""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=72, description="User password (8-72 characters, bcrypt limit)")
    company_name: str = Field(..., min_length=2, max_length=255, description="Company/tenant name")
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Ensure password has minimum complexity and bcrypt compatibility"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v) > 72:
            raise ValueError('Password cannot be longer than 72 characters (bcrypt limit)')
        # Check byte length for bcrypt compatibility
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password cannot exceed 72 bytes when encoded (bcrypt limit)')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "admin@acmecorp.com",
                "password": "SecurePass123",
                "company_name": "Acme Corporation"
            }
        }


class LoginRequest(BaseModel):
    """Request model for user login"""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "admin@acmecorp.com",
                "password": "SecurePass123"
            }
        }


class UserResponse(BaseModel):
    """User information in responses"""
    
    id: uuid.UUID = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    role: str = Field(..., description="User role")
    tenant_id: uuid.UUID = Field(..., description="Tenant ID")
    is_active: bool = Field(..., description="Whether user is active")
    created_at: datetime = Field(..., description="Account creation timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "admin@acmecorp.com",
                "role": "admin",
                "tenant_id": "660e8400-e29b-41d4-a716-446655440001",
                "is_active": True,
                "created_at": "2025-12-15T08:00:00Z"
            }
        }


class TenantResponse(BaseModel):
    """Tenant information in responses"""
    
    id: uuid.UUID = Field(..., description="Tenant ID")
    name: str = Field(..., description="Tenant name")
    plan: str = Field(..., description="Subscription plan")
    is_active: bool = Field(..., description="Whether tenant is active")
    created_at: datetime = Field(..., description="Tenant creation timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "660e8400-e29b-41d4-a716-446655440001",
                "name": "Acme Corporation",
                "plan": "starter",
                "is_active": True,
                "created_at": "2025-12-15T08:00:00Z"
            }
        }


class AuthResponse(BaseModel):
    """Response model for signup and login"""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    user: UserResponse = Field(..., description="User information")
    tenant: TenantResponse = Field(..., description="Tenant information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "email": "admin@acmecorp.com",
                    "role": "admin",
                    "tenant_id": "660e8400-e29b-41d4-a716-446655440001",
                    "is_active": True,
                    "created_at": "2025-12-15T08:00:00Z"
                },
                "tenant": {
                    "id": "660e8400-e29b-41d4-a716-446655440001",
                    "name": "Acme Corporation",
                    "plan": "starter",
                    "is_active": True,
                    "created_at": "2025-12-15T08:00:00Z"
                }
            }
        }


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh"""
    
    refresh_token: str = Field(..., description="Refresh token")
    
    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class RefreshTokenResponse(BaseModel):
    """Response model for token refresh"""
    
    access_token: str = Field(..., description="New JWT access token")
    refresh_token: str = Field(..., description="New JWT refresh token (rotated)")
    token_type: str = Field(default="bearer", description="Token type")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }


class LogoutRequest(BaseModel):
    """Request model for logout"""
    
    all_sessions: bool = Field(default=False, description="Logout from all sessions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "all_sessions": False
            }
        }

class ChangePasswordRequest(BaseModel):
    """Request model for changing password"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
