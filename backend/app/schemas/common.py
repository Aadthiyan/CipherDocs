"""
CyborgDB Pydantic Schemas
Request/response models for API validation and documentation
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class HealthCheckResponse(BaseModel):
    """Health check response model"""
    
    status: str = Field(..., description="Service status", example="healthy")
    service: str = Field(..., description="Service name", example="cyborgdb-backend")
    version: str = Field(..., description="Service version", example="1.0.0")
    timestamp: datetime = Field(..., description="Current timestamp")
    environment: str = Field(..., description="Environment", example="development")
    checks: Dict[str, str] = Field(..., description="Component health checks")
    database: Optional[Dict[str, Any]] = Field(None, description="Database connection info")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service": "cyborgdb-backend",
                "version": "1.0.0",
                "timestamp": "2025-12-03T12:00:00",
                "environment": "development",
                "checks": {
                    "database": "connected",
                    "embedding_service": "reachable",
                    "cyborgdb": "configured"
                },
                "database": {
                    "pool_size": 10,
                    "checked_out": 2,
                    "checked_in": 8
                }
            }
        }


class APIInfoResponse(BaseModel):
    """API information response"""
    
    message: str = Field(..., description="Welcome message")
    version: str = Field(..., description="API version")
    docs: str = Field(..., description="Documentation URL")
    health: str = Field(..., description="Health check URL")
    description: str = Field(..., description="API description")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Welcome to CyborgDB API",
                "version": "1.0.0",
                "docs": "/docs",
                "health": "/health",
                "description": "Encrypted multi-tenant document search platform"
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response model"""
    
    error: bool = Field(True, description="Error flag")
    status_code: int = Field(..., description="HTTP status code")
    message: str = Field(..., description="Error message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Error details")
    correlation_id: Optional[str] = Field(None, description="Request correlation ID")
    timestamp: datetime = Field(..., description="Error timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": True,
                "status_code": 404,
                "message": "Resource not found",
                "details": {"resource_type": "document", "resource_id": "123"},
                "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2025-12-03T12:00:00"
            }
        }


class PaginationParams(BaseModel):
    """Pagination parameters"""
    
    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=10, ge=1, le=100, description="Number of records to return")
    
    class Config:
        json_schema_extra = {
            "example": {
                "skip": 0,
                "limit": 10
            }
        }


class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    
    items: list = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Number of items returned")
    has_more: bool = Field(..., description="Whether more items are available")
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 100,
                "skip": 0,
                "limit": 10,
                "has_more": True
            }
        }
