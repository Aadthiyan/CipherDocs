"""
Pydantic schemas for user management endpoints.
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import uuid

from app.core.rbac import UserRole


class UserCreate(BaseModel):
    """Request model for creating a new user (admin only)"""
    
    email: EmailStr = Field(..., description="User email address")
    role: UserRole = Field(default=UserRole.USER, description="User role")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "newuser@company.com",
                "role": "user"
            }
        }


class UserUpdate(BaseModel):
    """Request model for updating user details"""
    
    role: Optional[UserRole] = Field(None, description="New user role")
    is_active: Optional[bool] = Field(None, description="Whether user is active")
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "admin",
                "is_active": True
            }
        }


class UserRoleUpdate(BaseModel):
    """Request model for updating user role"""
    
    role: UserRole = Field(..., description="New user role")
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "admin"
            }
        }


class UserListResponse(BaseModel):
    """User information in list responses"""
    
    id: uuid.UUID = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    role: str = Field(..., description="User role")
    is_active: bool = Field(..., description="Whether user is active")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    created_at: datetime = Field(..., description="Account creation timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@company.com",
                "role": "user",
                "is_active": True,
                "last_login": "2025-12-15T08:00:00Z",
                "created_at": "2025-12-15T07:00:00Z"
            }
        }


class UserDetailResponse(BaseModel):
    """Detailed user information"""
    
    id: uuid.UUID = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    role: str = Field(..., description="User role")
    tenant_id: uuid.UUID = Field(..., description="Tenant ID")
    is_active: bool = Field(..., description="Whether user is active")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@company.com",
                "role": "user",
                "tenant_id": "660e8400-e29b-41d4-a716-446655440001",
                "is_active": True,
                "last_login": "2025-12-15T08:00:00Z",
                "created_at": "2025-12-15T07:00:00Z",
                "updated_at": "2025-12-15T08:00:00Z"
            }
        }


class UserInviteResponse(BaseModel):
    """Response after inviting a new user"""
    
    user: UserDetailResponse = Field(..., description="Created user details")
    temporary_password: str = Field(..., description="Temporary password for first login")
    message: str = Field(..., description="Success message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "email": "newuser@company.com",
                    "role": "user",
                    "tenant_id": "660e8400-e29b-41d4-a716-446655440001",
                    "is_active": True,
                    "last_login": None,
                    "created_at": "2025-12-15T08:00:00Z",
                    "updated_at": "2025-12-15T08:00:00Z"
                },
                "temporary_password": "TempPass123!",
                "message": "User invited successfully. Send them the temporary password."
            }
        }


class UsersListResponse(BaseModel):
    """Paginated list of users"""
    
    users: list[UserListResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")
    skip: int = Field(..., description="Number of users skipped")
    limit: int = Field(..., description="Number of users returned")
    
    class Config:
        json_schema_extra = {
            "example": {
                "users": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "email": "admin@company.com",
                        "role": "admin",
                        "is_active": True,
                        "last_login": "2025-12-15T08:00:00Z",
                        "created_at": "2025-12-15T07:00:00Z"
                    }
                ],
                "total": 1,
                "skip": 0,
                "limit": 10
            }
        }
