"""
CyborgDB Database Models
SQLAlchemy ORM models for all database tables
"""

from sqlalchemy import (
    Column, String, Integer, BigInteger, Boolean, DateTime, Text, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.database import Base


class Tenant(Base):
    """
    Tenant model for multi-tenancy
    
    Each tenant represents an organization/company using the platform
    """
    __tablename__ = "tenants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    plan = Column(String(50), nullable=False, default="starter")  # starter, pro, enterprise
    key_fingerprint = Column(String(255), unique=True)
    cyborgdb_namespace = Column(String(255), unique=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="tenant", cascade="all, delete-orphan")
    document_chunks = relationship("DocumentChunk", back_populates="tenant", cascade="all, delete-orphan")
    search_logs = relationship("SearchLog", back_populates="tenant", cascade="all, delete-orphan")
    encryption_keys = relationship("EncryptionKey", back_populates="tenant", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('ix_tenants_name', 'name'),
        Index('ix_tenants_is_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<Tenant(id={self.id}, name={self.name}, plan={self.plan})>"


class User(Base):
    """
    User model for authentication and authorization
    
    Users belong to a tenant and have roles (admin, user, viewer)
    """
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="user")  # admin, user, viewer
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    search_logs = relationship("SearchLog", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('ix_users_email', 'email'),
        Index('ix_users_tenant_id', 'tenant_id'),
        Index('ix_users_tenant_email', 'tenant_id', 'email', unique=True),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"


class Document(Base):
    """
    Document model for uploaded files
    
    Stores metadata about uploaded documents
    """
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)
    doc_type = Column(String(50), nullable=False)  # pdf, docx, txt
    file_size_bytes = Column(BigInteger)
    file_hash = Column(String(64))  # SHA-256 hash for duplicate detection
    chunk_count = Column(Integer, default=0)
    status = Column(String(50), nullable=False, default="uploaded")  # uploaded, extracting, chunking, embedding, indexing, completed, failed
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('ix_documents_tenant_id', 'tenant_id'),
        Index('ix_documents_status', 'status'),
        Index('ix_documents_file_hash', 'file_hash'),
        Index('ix_documents_tenant_status', 'tenant_id', 'status'),
    )
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename}, status={self.status})>"


class DocumentChunk(Base):
    """
    Document chunk model for text segments
    
    Documents are split into chunks for embedding and search
    """
    __tablename__ = "document_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doc_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    chunk_sequence = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    encrypted_embedding = Column(Text) # Base64 encoded Fernet token
    embedding_dimension = Column(Integer, default=384)
    page_number = Column(Integer)
    section_heading = Column(String(500))
    indexed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    tenant = relationship("Tenant", back_populates="document_chunks")
    
    # Indexes
    __table_args__ = (
        Index('ix_document_chunks_doc_id', 'doc_id'),
        Index('ix_document_chunks_tenant_id', 'tenant_id'),
        Index('ix_document_chunks_doc_sequence', 'doc_id', 'chunk_sequence', unique=True),
    )
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, doc_id={self.doc_id}, sequence={self.chunk_sequence})>"


class SearchLog(Base):
    """
    Search log model for analytics
    
    Tracks all search queries for analytics and monitoring
    """
    __tablename__ = "search_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    query_text = Column(String(1000), nullable=False)
    query_latency_ms = Column(Integer)
    result_count = Column(Integer)
    top_k = Column(Integer, default=10)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="search_logs")
    user = relationship("User", back_populates="search_logs")
    
    # Indexes
    __table_args__ = (
        Index('ix_search_logs_tenant_id', 'tenant_id'),
        Index('ix_search_logs_created_at', 'created_at'),
        Index('ix_search_logs_tenant_created', 'tenant_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<SearchLog(id={self.id}, query={self.query_text[:50]})>"


class EncryptionKey(Base):
    """
    Encryption key model for tenant-specific keys
    
    Stores encrypted tenant keys for vector encryption
    """
    __tablename__ = "encryption_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    key_fingerprint = Column(String(255), unique=True, nullable=False)
    encrypted_key = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    rotated_at = Column(DateTime(timezone=True))
    
    # Relationships
    tenant = relationship("Tenant", back_populates="encryption_keys")
    
    # Indexes
    __table_args__ = (
        Index('ix_encryption_keys_tenant_id', 'tenant_id'),
        Index('ix_encryption_keys_tenant_active', 'tenant_id', 'is_active'),
    )
    
    def __repr__(self):
        return f"<EncryptionKey(id={self.id}, tenant_id={self.tenant_id}, active={self.is_active})>"


class Session(Base):
    """
    Session model for refresh tokens
    
    Tracks user sessions and refresh tokens
    """
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    refresh_token = Column(String(500), unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    # Indexes
    __table_args__ = (
        Index('ix_sessions_user_id', 'user_id'),
        Index('ix_sessions_refresh_token', 'refresh_token'),
        Index('ix_sessions_expires_at', 'expires_at'),
    )
    
    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id}, revoked={self.is_revoked})>"
