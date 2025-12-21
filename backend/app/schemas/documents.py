"""
Pydantic schemas for document operations.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import uuid


class DocumentUploadResponse(BaseModel):
    """Response model for document upload"""
    
    id: uuid.UUID = Field(..., description="Document ID")
    filename: str = Field(..., description="Original filename")
    doc_type: str = Field(..., description="Document type (pdf, docx, txt, etc.)")
    file_size_bytes: int = Field(..., description="File size in bytes")
    file_hash: str = Field(..., description="SHA-256 hash of file")
    status: str = Field(..., description="Processing status")
    storage_path: str = Field(..., description="Storage path/key")
    tenant_id: uuid.UUID = Field(..., description="Tenant ID")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    message: str = Field(..., description="Success message")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "contract.pdf",
                "doc_type": "pdf",
                "file_size_bytes": 1024000,
                "file_hash": "a3b2c1...",
                "status": "uploaded",
                "storage_path": "tenant-id/doc-id/contract.pdf",
                "tenant_id": "660e8400-e29b-41d4-a716-446655440001",
                "uploaded_at": "2025-12-15T08:00:00Z",
                "message": "Document uploaded successfully"
            }
        }


class DocumentListItem(BaseModel):
    """Document information in list responses"""
    
    id: uuid.UUID = Field(..., description="Document ID")
    filename: str = Field(..., description="Original filename")
    doc_type: str = Field(..., description="Document type")
    file_size_bytes: int = Field(..., description="File size in bytes")
    status: str = Field(..., description="Processing status")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class DocumentDetail(BaseModel):
    """Detailed document information"""
    
    id: uuid.UUID = Field(..., description="Document ID")
    filename: str = Field(..., description="Original filename")
    doc_type: str = Field(..., description="Document type")
    file_size_bytes: int = Field(..., description="File size in bytes")
    file_hash: str = Field(..., description="SHA-256 hash")
    status: str = Field(..., description="Processing status")
    storage_path: str = Field(..., description="Storage path/key")
    tenant_id: uuid.UUID = Field(..., description="Tenant ID")
    chunk_count: Optional[int] = Field(None, description="Number of chunks")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    retry_count: int = Field(0, description="Number of retries attempted")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class DocumentsListResponse(BaseModel):
    """Paginated list of documents"""
    
    documents: list[DocumentListItem] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents")
    skip: int = Field(..., description="Number of documents skipped")
    limit: int = Field(..., description="Number of documents returned")
    
    class Config:
        json_schema_extra = {
            "example": {
                "documents": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "filename": "contract.pdf",
                        "doc_type": "pdf",
                        "file_size": 1024000,
                        "status": "completed",
                        "created_at": "2025-12-15T08:00:00Z",
                        "updated_at": "2025-12-15T08:05:00Z"
                    }
                ],
                "total": 1,
                "skip": 0,
                "limit": 10
            }
        }
