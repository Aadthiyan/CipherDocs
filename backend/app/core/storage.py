"""
Storage abstraction layer for document storage.
Supports local filesystem, S3, and Minio backends.
"""

from abc import ABC, abstractmethod
from typing import BinaryIO, Optional
from pathlib import Path
import os
import hashlib
import uuid
from datetime import datetime

from app.core.config import settings


class StorageBackend(ABC):
    """Abstract base class for storage backends"""
    
    @abstractmethod
    async def save_file(
        self,
        file_data: BinaryIO,
        tenant_id: str,
        document_id: str,
        filename: str
    ) -> str:
        """
        Save a file to storage.
        
        Args:
            file_data: File binary data
            tenant_id: Tenant identifier
            document_id: Document identifier
            filename: Original filename
            
        Returns:
            Storage path/key where file was saved
        """
        pass
    
    @abstractmethod
    async def get_file(self, storage_path: str) -> bytes:
        """
        Retrieve a file from storage.
        
        Args:
            storage_path: Path/key where file is stored
            
        Returns:
            File binary data
        """
        pass
    
    @abstractmethod
    async def delete_file(self, storage_path: str) -> bool:
        """
        Delete a file from storage.
        
        Args:
            storage_path: Path/key where file is stored
            
        Returns:
            True if deleted successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def file_exists(self, storage_path: str) -> bool:
        """
        Check if a file exists in storage.
        
        Args:
            storage_path: Path/key to check
            
        Returns:
            True if file exists, False otherwise
        """
        pass


class LocalFileSystemStorage(StorageBackend):
    """Local filesystem storage backend"""
    
    def __init__(self, base_path: str = "./storage"):
        """
        Initialize local filesystem storage.
        
        Args:
            base_path: Base directory for file storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_file_path(self, tenant_id: str, document_id: str, filename: str) -> Path:
        """
        Generate file path with tenant isolation.
        
        Format: {base_path}/{tenant_id}/{document_id}/{filename}
        """
        tenant_dir = self.base_path / tenant_id / document_id
        tenant_dir.mkdir(parents=True, exist_ok=True)
        return tenant_dir / filename
    
    async def save_file(
        self,
        file_data: BinaryIO,
        tenant_id: str,
        document_id: str,
        filename: str
    ) -> str:
        """Save file to local filesystem"""
        file_path = self._get_file_path(tenant_id, document_id, filename)
        
        # Write file in chunks to handle large files
        with open(file_path, 'wb') as f:
            while chunk := file_data.read(8192):  # 8KB chunks
                f.write(chunk)
        
        # Return relative path from base
        return str(file_path.relative_to(self.base_path))
    
    async def get_file(self, storage_path: str) -> bytes:
        """Retrieve file from local filesystem"""
        file_path = self.base_path / storage_path
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {storage_path}")
        
        with open(file_path, 'rb') as f:
            return f.read()
    
    async def delete_file(self, storage_path: str) -> bool:
        """Delete file from local filesystem"""
        file_path = self.base_path / storage_path
        
        if file_path.exists():
            file_path.unlink()
            
            # Clean up empty directories
            try:
                file_path.parent.rmdir()
                file_path.parent.parent.rmdir()
            except OSError:
                pass  # Directory not empty
            
            return True
        
        return False
    
    async def file_exists(self, storage_path: str) -> bool:
        """Check if file exists in local filesystem"""
        file_path = self.base_path / storage_path
        return file_path.exists()


class S3Storage(StorageBackend):
    """AWS S3 storage backend"""
    
    def __init__(
        self,
        bucket_name: str,
        aws_access_key: Optional[str] = None,
        aws_secret_key: Optional[str] = None,
        region: str = "us-east-1"
    ):
        """
        Initialize S3 storage.
        
        Args:
            bucket_name: S3 bucket name
            aws_access_key: AWS access key (optional, uses env if not provided)
            aws_secret_key: AWS secret key (optional, uses env if not provided)
            region: AWS region
        """
        try:
            import boto3
            from botocore.exceptions import ClientError
        except ImportError:
            raise ImportError("boto3 is required for S3 storage. Install with: pip install boto3")
        
        self.bucket_name = bucket_name
        self.client_error = ClientError
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )
    
    def _get_s3_key(self, tenant_id: str, document_id: str, filename: str) -> str:
        """
        Generate S3 key with tenant isolation.
        
        Format: {tenant_id}/{document_id}/{filename}
        """
        return f"{tenant_id}/{document_id}/{filename}"
    
    async def save_file(
        self,
        file_data: BinaryIO,
        tenant_id: str,
        document_id: str,
        filename: str
    ) -> str:
        """Upload file to S3"""
        s3_key = self._get_s3_key(tenant_id, document_id, filename)
        
        try:
            self.s3_client.upload_fileobj(
                file_data,
                self.bucket_name,
                s3_key,
                ExtraArgs={'ServerSideEncryption': 'AES256'}
            )
            return s3_key
        except self.client_error as e:
            raise Exception(f"Failed to upload to S3: {str(e)}")
    
    async def get_file(self, storage_path: str) -> bytes:
        """Download file from S3"""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=storage_path
            )
            return response['Body'].read()
        except self.client_error as e:
            raise FileNotFoundError(f"File not found in S3: {storage_path}")
    
    async def delete_file(self, storage_path: str) -> bool:
        """Delete file from S3"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=storage_path
            )
            return True
        except self.client_error:
            return False
    
    async def file_exists(self, storage_path: str) -> bool:
        """Check if file exists in S3"""
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=storage_path
            )
            return True
        except self.client_error:
            return False


def get_storage_backend() -> StorageBackend:
    """
    Factory function to get the configured storage backend.
    
    Returns:
        Configured storage backend instance
    """
    storage_type = getattr(settings, 'STORAGE_BACKEND', 'local').lower()
    
    if storage_type == 'local':
        storage_path = getattr(settings, 'LOCAL_STORAGE_PATH', './storage')
        return LocalFileSystemStorage(base_path=storage_path)
    
    elif storage_type == 's3':
        bucket_name = getattr(settings, 'S3_BUCKET_NAME', None)
        if not bucket_name:
            raise ValueError("S3_BUCKET_NAME must be set for S3 storage")
        
        return S3Storage(
            bucket_name=bucket_name,
            aws_access_key=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
            aws_secret_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
            region=getattr(settings, 'AWS_REGION', 'us-east-1')
        )
    
    else:
        raise ValueError(f"Unsupported storage backend: {storage_type}")


def calculate_file_hash(file_data: BinaryIO) -> str:
    """
    Calculate SHA-256 hash of file for duplicate detection.
    
    Args:
        file_data: File binary data
        
    Returns:
        Hexadecimal hash string
    """
    sha256_hash = hashlib.sha256()
    
    # Reset file pointer to beginning
    file_data.seek(0)
    
    # Read file in chunks
    while chunk := file_data.read(8192):
        sha256_hash.update(chunk)
    
    # Reset file pointer again for subsequent reads
    file_data.seek(0)
    
    return sha256_hash.hexdigest()
