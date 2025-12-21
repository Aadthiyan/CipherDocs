"""
Test fixtures and test data for backend testing.
Provides reusable fixtures for users, tenants, documents, and other test data.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.db.database import Base, get_db
from app.models.database import (
    Tenant, User, Document, DocumentChunk, SearchLog, EncryptionKey, Session as SessionModel
)
from app.core.security import hash_password
from app.core.config import settings


# ============================================================================
# Tenant Fixtures
# ============================================================================

@pytest.fixture
def sample_tenant_id():
    """Generate a sample tenant ID"""
    return uuid.uuid4()


@pytest.fixture
def sample_tenant(db_session, sample_tenant_id):
    """Create a sample tenant in database"""
    tenant = Tenant(
        id=sample_tenant_id,
        name="Test Tenant",
        plan="starter"
    )
    db_session.add(tenant)
    db_session.commit()
    return tenant


@pytest.fixture
def multiple_tenants(db_session):
    """Create multiple sample tenants"""
    tenants = []
    for i in range(5):
        tenant = Tenant(
            id=uuid.uuid4(),
            name=f"Test Tenant {i}",
            plan="pro" if i % 2 == 0 else "starter"
        )
        db_session.add(tenant)
        tenants.append(tenant)
    db_session.commit()
    return tenants


# ============================================================================
# User Fixtures
# ============================================================================

@pytest.fixture
def sample_user(db_session, sample_tenant):
    """Create a sample user"""
    user = User(
        id=uuid.uuid4(),
        tenant_id=sample_tenant.id,
        email="testuser@example.com",
        password_hash=hash_password("SecurePassword123!"),
        is_active=True,
        role="user"
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def admin_user(db_session, sample_tenant):
    """Create an admin user"""
    user = User(
        id=uuid.uuid4(),
        tenant_id=sample_tenant.id,
        email="admin@example.com",
        password_hash=hash_password("AdminPassword123!"),
        is_active=True,
        role="admin"
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def viewer_user(db_session, sample_tenant):
    """Create a viewer (read-only) user"""
    user = User(
        id=uuid.uuid4(),
        tenant_id=sample_tenant.id,
        email="viewer@example.com",
        password_hash=hash_password("ViewerPassword123!"),
        is_active=True,
        role="viewer"
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def multiple_users(db_session, sample_tenant):
    """Create multiple users for same tenant"""
    users = []
    for i in range(10):
        user = User(
            id=uuid.uuid4(),
            tenant_id=sample_tenant.id,
            email=f"user{i}@example.com",
            password_hash=hash_password(f"Password{i}123!"),
            is_active=True,
            role="user" if i % 3 != 0 else "viewer"
        )
        db_session.add(user)
        users.append(user)
    db_session.commit()
    return users


@pytest.fixture
def users_across_tenants(db_session, multiple_tenants):
    """Create users across multiple tenants"""
    users = []
    for idx, tenant in enumerate(multiple_tenants):
        for i in range(3):
            user = User(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                email=f"user{idx}_{i}@test.example.com",
                password_hash=hash_password(f"Password{i}123!"),
                is_active=True,
                role="user"
            )
            db_session.add(user)
            users.append(user)
    db_session.commit()
    return users


# ============================================================================
# Document Fixtures
# ============================================================================

@pytest.fixture
def sample_document(db_session, sample_tenant):
    """Create a sample document"""
    doc = Document(
        id=uuid.uuid4(),
        tenant_id=sample_tenant.id,
        filename="sample.pdf",
        storage_path="documents/sample.pdf",
        doc_type="pdf",
        file_size_bytes=1024,
        file_hash="abc123def456",
        chunk_count=10,
        status="completed"
    )
    db_session.add(doc)
    db_session.commit()
    return doc


@pytest.fixture
def multiple_documents(db_session, sample_tenant):
    """Create multiple documents"""
    documents = []
    for i in range(20):
        doc = Document(
            id=uuid.uuid4(),
            tenant_id=sample_tenant.id,
            filename=f"document_{i}.pdf",
            storage_path=f"documents/document_{i}.pdf",
            doc_type="pdf" if i % 2 == 0 else "docx",
            file_size_bytes=1024 * (i + 1),
            file_hash=f"hash_{i}",
            chunk_count=10 + i,
            status="completed"
        )
        db_session.add(doc)
        documents.append(doc)
    db_session.commit()
    return documents


@pytest.fixture
def documents_from_multiple_users(db_session, sample_tenant, multiple_users):
    """Create documents from multiple users"""
    documents = []
    for user_idx, user in enumerate(multiple_users[:5]):  # Use first 5 users
        for i in range(3):
            doc = Document(
                id=uuid.uuid4(),
                tenant_id=sample_tenant.id,
                filename=f"doc_{user_idx}_{i}.pdf",
                storage_path=f"documents/doc_{user_idx}_{i}.pdf",
                doc_type="pdf",
                file_size_bytes=512 * (i + 1),
                file_hash=f"user_{user_idx}_doc_{i}",
                chunk_count=5,
                status="completed"
            )
            db_session.add(doc)
            documents.append(doc)
    db_session.commit()
    return documents


# ============================================================================
# Chunk Fixtures
# ============================================================================

@pytest.fixture
def sample_chunks(db_session, sample_tenant, sample_document):
    """Create sample chunks from a document"""
    chunks = []
    for i in range(10):
        chunk = DocumentChunk(
            id=uuid.uuid4(),
            tenant_id=sample_tenant.id,
            doc_id=sample_document.id,
            chunk_sequence=i,
            text=f"Chunk {i} content with vector data. " * 20,
            encrypted_embedding="mock_embedding_" + str(i),
            embedding_dimension=384,
            page_number=i // 5
        )
        db_session.add(chunk)
        chunks.append(chunk)
    db_session.commit()
    return chunks


@pytest.fixture
def chunks_from_multiple_documents(db_session, sample_tenant, multiple_documents):
    """Create chunks from multiple documents"""
    chunks = []
    for doc_idx, doc in enumerate(multiple_documents[:10]):  # Use first 10 docs
        for chunk_idx in range(5):
            chunk = DocumentChunk(
                id=uuid.uuid4(),
                tenant_id=sample_tenant.id,
                doc_id=doc.id,
                chunk_sequence=chunk_idx,
                text=f"Chunk {chunk_idx} from document {doc_idx}. " * 15,
                encrypted_embedding="mock_" + str(doc_idx) + "_" + str(chunk_idx),
                embedding_dimension=384,
                page_number=(doc_idx * 5) + chunk_idx
            )
            db_session.add(chunk)
            chunks.append(chunk)
    db_session.commit()
    return chunks


# ============================================================================
# Search Log Fixtures
# ============================================================================

@pytest.fixture
def sample_search_logs(db_session, sample_tenant, sample_user):
    """Create sample search logs"""
    logs = []
    search_terms = [
        "machine learning",
        "data science",
        "python programming",
        "natural language processing",
        "deep learning"
    ]
    
    for i, term in enumerate(search_terms):
        log = SearchLog(
            id=uuid.uuid4(),
            tenant_id=sample_tenant.id,
            user_id=sample_user.id,
            query_text=term,
            result_count=10 + i * 5,
            query_latency_ms=50 + i * 10,
            top_k=10
        )
        db_session.add(log)
        logs.append(log)
    db_session.commit()
    return logs


# ============================================================================
# Encryption Key Fixtures
# ============================================================================

@pytest.fixture
def sample_encryption_key(db_session, sample_tenant):
    """Create a sample encryption key"""
    fingerprint = "sha256_" + uuid.uuid4().hex[:32]
    
    db_key = EncryptionKey(
        id=uuid.uuid4(),
        tenant_id=sample_tenant.id,
        encrypted_key="encrypted_key_data",
        key_fingerprint=fingerprint,
        is_active=True
    )
    db_session.add(db_key)
    db_session.commit()
    return db_key


@pytest.fixture
def multiple_encryption_keys(db_session, sample_tenant):
    """Create multiple encryption keys for tenant"""
    keys = []
    for i in range(3):
        fingerprint = "sha256_" + uuid.uuid4().hex[:32]
        
        db_key = EncryptionKey(
            id=uuid.uuid4(),
            tenant_id=sample_tenant.id,
            encrypted_key=f"encrypted_key_data_{i}",
            key_fingerprint=fingerprint,
            is_active=(i == 0)  # Only first is active
        )
        db_session.add(db_key)
        keys.append(db_key)
    db_session.commit()
    return keys


# ============================================================================
# Bulk Data Fixtures
# ============================================================================

@pytest.fixture
def bulk_test_data(db_session, multiple_tenants):
    """Create bulk test data for stress testing"""
    all_data = {
        "tenants": multiple_tenants,
        "users": [],
        "documents": [],
        "chunks": []
    }
    
    # Create 10 users per tenant
    for tenant in multiple_tenants:
        for i in range(10):
            user = User(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                email=f"bulk_user{i}@{tenant.name.lower().replace(' ', '_')}.local",
                password_hash=hash_password(f"Password{i}123!"),
                is_active=True,
                role="user"
            )
            db_session.add(user)
            all_data["users"].append(user)
    
    db_session.flush()
    
    # Create 5 documents per user
    doc_counter = 0
    for user in all_data["users"]:
        for i in range(5):
            doc = Document(
                id=uuid.uuid4(),
                tenant_id=user.tenant_id,
                filename=f"bulk_doc_{doc_counter}.pdf",
                storage_path=f"documents/bulk_doc_{doc_counter}.pdf",
                doc_type="pdf",
                file_size_bytes=2048 * (i + 1),
                file_hash=f"bulk_hash_{doc_counter}",
                chunk_count=10,
                status="completed"
            )
            doc_counter += 1
            db_session.add(doc)
            all_data["documents"].append(doc)
    
    db_session.flush()
    
    # Create 10 chunks per document
    for doc in all_data["documents"]:
        for i in range(10):
            chunk = DocumentChunk(
                id=uuid.uuid4(),
                tenant_id=doc.tenant_id,
                doc_id=doc.id,
                chunk_sequence=i,
                text=f"Chunk {i} from bulk document. " * 30,
                encrypted_embedding="bulk_" + str(i),
                embedding_dimension=384,
                page_number=i // 5
            )
            db_session.add(chunk)
            all_data["chunks"].append(chunk)
    
    db_session.commit()
    return all_data


# ============================================================================
# Parametrized Fixtures
# ============================================================================

@pytest.fixture(params=["admin", "user", "viewer"])
def user_with_role(request, db_session, sample_tenant):
    """Parametrized fixture for users with different roles"""
    role = request.param
    user = User(
        id=uuid.uuid4(),
        tenant_id=sample_tenant.id,
        email=f"{role}@example.com",
        password_hash=hash_password(f"{role}Password123!"),
        is_active=True,
        role=role
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture(params=["pdf", "docx", "txt"])
def document_with_file_type(request, db_session, sample_tenant):
    """Parametrized fixture for documents with different file types"""
    file_type = request.param
    doc = Document(
        id=uuid.uuid4(),
        tenant_id=sample_tenant.id,
        filename=f"test.{file_type}",
        storage_path=f"documents/test.{file_type}",
        doc_type=file_type,
        file_size_bytes=1024,
        file_hash="test_hash",
        chunk_count=5,
        status="completed"
    )
    db_session.add(doc)
    db_session.commit()
    return doc


# ============================================================================
# Data Seeding Utilities
# ============================================================================

def seed_test_database(db_session: Session, num_tenants: int = 3, 
                       users_per_tenant: int = 5, 
                       docs_per_user: int = 3):
    """Seed database with test data"""
    tenants = []
    
    for t in range(num_tenants):
        tenant = Tenant(
            id=uuid.uuid4(),
            name=f"Seed Tenant {t}",
            plan="starter"
        )
        db_session.add(tenant)
        tenants.append(tenant)
    
    db_session.flush()
    
    for tenant in tenants:
        for u in range(users_per_tenant):
            user = User(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                email=f"seed_user{u}@test.local",
                password_hash=hash_password(f"SeedPassword{u}123!"),
                is_active=True,
                role="user" if u % 5 != 0 else "admin"
            )
            db_session.add(user)
            db_session.flush()
            
            for d in range(docs_per_user):
                doc = Document(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    filename=f"seeded_doc_{u}_{d}.pdf",
                    storage_path=f"documents/seeded_doc_{u}_{d}.pdf",
                    doc_type="pdf",
                    file_size_bytes=2048,
                    file_hash=f"seeded_hash_{u}_{d}",
                    chunk_count=10,
                    status="completed"
                )
                db_session.add(doc)
    
    db_session.commit()


@pytest.fixture
def seeded_database(db_session):
    """Seed database and provide clean session"""
    seed_test_database(db_session, num_tenants=3, users_per_tenant=5, docs_per_user=3)
    yield db_session
    # Cleanup handled by test_db fixture
