"""
Comprehensive tests for database operations.
Tests CRUD operations, filtering, tenant scoping, and query performance.
"""

import pytest
import uuid
from datetime import datetime, timedelta

from app.models.database import User, Document, DocumentChunk, SearchLog, Tenant, EncryptionKey


# ============================================================================
# CREATE Operations Tests
# ============================================================================

class TestCreateOperations:
    """Test database create operations"""
    
    def test_create_user(self, db_session, sample_tenant):
        """Should create user successfully"""
        user = User(
            id=uuid.uuid4(),
            tenant_id=sample_tenant.id,
            email="newuser@example.com",
            password_hash="hashed_password",
            is_active=True,
            role="user"
        )
        
        db_session.add(user)
        db_session.commit()
        
        found = db_session.query(User).filter_by(email="newuser@example.com").first()
        assert found is not None
        assert found.role == "user"
    
    def test_create_document(self, db_session, sample_tenant):
        """Should create document successfully"""
        doc = Document(
            id=uuid.uuid4(),
            tenant_id=sample_tenant.id,
            filename="test.pdf",
            storage_path="documents/test.pdf",
            doc_type="pdf",
            file_size_bytes=1024,
            file_hash="test_hash",
            chunk_count=0,
            status="uploaded"
        )
        
        db_session.add(doc)
        db_session.commit()
        
        found = db_session.query(Document).filter_by(filename="test.pdf").first()
        assert found is not None
        assert found.doc_type == "pdf"
    
    def test_create_chunk(self, db_session, sample_document):
        """Should create document chunk successfully"""
        chunk = DocumentChunk(
            id=uuid.uuid4(),
            tenant_id=sample_document.tenant_id,
            doc_id=sample_document.id,
            chunk_sequence=0,
            text="Test chunk content",
            encrypted_embedding="mock_embedding",
            embedding_dimension=384
        )
        
        db_session.add(chunk)
        db_session.commit()
        
        found = db_session.query(DocumentChunk).filter_by(chunk_sequence=0).first()
        assert found is not None
        assert found.text == "Test chunk content"
    
    def test_create_bulk_users(self, db_session, sample_tenant):
        """Should create multiple users in bulk"""
        users = []
        for i in range(10):
            user = User(
                id=uuid.uuid4(),
                tenant_id=sample_tenant.id,
                email=f"bulk_user_{i}@example.com",
                password_hash=f"hash_{i}",
                is_active=True,
                role="user"
            )
            users.append(user)
        
        db_session.add_all(users)
        db_session.commit()
        
        count = db_session.query(User).filter(User.email.like("bulk_user_%")).count()
        assert count == 10


# ============================================================================
# READ Operations Tests
# ============================================================================

class TestReadOperations:
    """Test database read operations"""
    
    def test_read_user_by_id(self, db_session, sample_user):
        """Should read user by ID"""
        found = db_session.query(User).filter_by(id=sample_user.id).first()
        assert found is not None
        assert found.email == sample_user.email
    
    def test_read_user_by_email(self, db_session, sample_user):
        """Should read user by email"""
        found = db_session.query(User).filter_by(email=sample_user.email).first()
        assert found is not None
        assert found.id == sample_user.id
    
    def test_read_document_by_id(self, db_session, sample_document):
        """Should read document by ID"""
        found = db_session.query(Document).filter_by(id=sample_document.id).first()
        assert found is not None
        assert found.filename == sample_document.filename
    
    def test_read_multiple_documents(self, db_session, multiple_documents):
        """Should read multiple documents"""
        found = db_session.query(Document).all()
        assert len(found) >= 20
    
    def test_read_chunks_for_document(self, db_session, sample_chunks):
        """Should read all chunks for a document"""
        found = db_session.query(DocumentChunk).filter(
            DocumentChunk.doc_id == sample_chunks[0].doc_id
        ).all()
        assert len(found) == 10


# ============================================================================
# UPDATE Operations Tests
# ============================================================================

class TestUpdateOperations:
    """Test database update operations"""
    
    def test_update_user_role(self, db_session, sample_user):
        """Should update user role"""
        sample_user.role = "admin"
        db_session.commit()
        
        found = db_session.query(User).filter_by(id=sample_user.id).first()
        assert found.role == "admin"
    
    def test_update_user_is_active(self, db_session, sample_user):
        """Should update user active status"""
        sample_user.is_active = False
        db_session.commit()
        
        found = db_session.query(User).filter_by(id=sample_user.id).first()
        assert found.is_active is False
    
    def test_update_document_status(self, db_session, sample_document):
        """Should update document status"""
        sample_document.status = "completed"
        sample_document.chunk_count = 10
        db_session.commit()
        
        found = db_session.query(Document).filter_by(id=sample_document.id).first()
        assert found.status == "completed"
        assert found.chunk_count == 10
    
    def test_bulk_update_users(self, db_session, multiple_users):
        """Should update multiple users"""
        db_session.query(User).filter(User.email.like("user%")).update(
            {"role": "viewer"}
        )
        db_session.commit()
        
        count = db_session.query(User).filter(
            User.email.like("user%"),
            User.role == "viewer"
        ).count()
        assert count > 0


# ============================================================================
# DELETE Operations Tests
# ============================================================================

class TestDeleteOperations:
    """Test database delete operations"""
    
    def test_delete_user(self, db_session, sample_tenant):
        """Should delete user"""
        user = User(
            id=uuid.uuid4(),
            tenant_id=sample_tenant.id,
            email="delete_test@example.com",
            password_hash="hash",
            is_active=True,
            role="user"
        )
        db_session.add(user)
        db_session.commit()
        
        user_id = user.id
        db_session.delete(user)
        db_session.commit()
        
        found = db_session.query(User).filter_by(id=user_id).first()
        assert found is None
    
    def test_delete_document_cascade(self, db_session, sample_document, sample_chunks):
        """Should delete document and cascade delete chunks"""
        doc_id = sample_document.id
        
        db_session.delete(sample_document)
        db_session.commit()
        
        found_doc = db_session.query(Document).filter_by(id=doc_id).first()
        assert found_doc is None
        
        # Chunks should be deleted due to cascade
        chunks = db_session.query(DocumentChunk).filter_by(doc_id=doc_id).all()
        assert len(chunks) == 0


# ============================================================================
# FILTERING Tests
# ============================================================================

class TestFiltering:
    """Test database filtering operations"""
    
    def test_filter_users_by_role(self, db_session, sample_tenant):
        """Should filter users by role"""
        # Create users with different roles
        for role in ["admin", "user", "viewer"]:
            user = User(
                id=uuid.uuid4(),
                tenant_id=sample_tenant.id,
                email=f"{role}@example.com",
                password_hash="hash",
                is_active=True,
                role=role
            )
            db_session.add(user)
        db_session.commit()
        
        admins = db_session.query(User).filter_by(role="admin").count()
        assert admins >= 1
    
    def test_filter_documents_by_type(self, db_session, sample_tenant):
        """Should filter documents by type"""
        for doc_type in ["pdf", "docx", "txt"]:
            doc = Document(
                id=uuid.uuid4(),
                tenant_id=sample_tenant.id,
                filename=f"test.{doc_type}",
                storage_path=f"documents/test.{doc_type}",
                doc_type=doc_type,
                file_size_bytes=1024,
                file_hash=f"hash_{doc_type}",
                chunk_count=0,
                status="completed"
            )
            db_session.add(doc)
        db_session.commit()
        
        pdfs = db_session.query(Document).filter_by(doc_type="pdf").count()
        assert pdfs >= 1
    
    def test_filter_active_users(self, db_session, sample_tenant):
        """Should filter active users"""
        user = User(
            id=uuid.uuid4(),
            tenant_id=sample_tenant.id,
            email="inactive@example.com",
            password_hash="hash",
            is_active=False,
            role="user"
        )
        db_session.add(user)
        db_session.commit()
        
        inactive = db_session.query(User).filter_by(is_active=False).count()
        assert inactive >= 1
        
        active = db_session.query(User).filter_by(is_active=True).count()
        assert active >= 1


# ============================================================================
# TENANT SCOPING Tests
# ============================================================================

class TestTenantScoping:
    """Test tenant isolation"""
    
    def test_users_isolated_by_tenant(self, db_session, multiple_tenants):
        """Should isolate users by tenant"""
        # Create users in different tenants
        users = []
        for tenant in multiple_tenants[:2]:
            user = User(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                email=f"user@{tenant.id}",
                password_hash="hash",
                is_active=True,
                role="user"
            )
            db_session.add(user)
            users.append(user)
        db_session.commit()
        
        # Query users for first tenant
        tenant_users = db_session.query(User).filter_by(
            tenant_id=multiple_tenants[0].id
        ).all()
        
        assert len(tenant_users) >= 1
        for user in tenant_users:
            assert user.tenant_id == multiple_tenants[0].id
    
    def test_documents_isolated_by_tenant(self, db_session, multiple_tenants):
        """Should isolate documents by tenant"""
        for tenant in multiple_tenants[:2]:
            doc = Document(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                filename=f"doc_for_tenant_{tenant.id}",
                storage_path=f"documents/doc_{tenant.id}",
                doc_type="pdf",
                file_size_bytes=1024,
                file_hash=f"hash_{tenant.id}",
                chunk_count=0,
                status="completed"
            )
            db_session.add(doc)
        db_session.commit()
        
        tenant_docs = db_session.query(Document).filter_by(
            tenant_id=multiple_tenants[0].id
        ).all()
        
        for doc in tenant_docs:
            assert doc.tenant_id == multiple_tenants[0].id


# ============================================================================
# PAGINATION Tests
# ============================================================================

class TestPagination:
    """Test pagination"""
    
    def test_limit_offset(self, db_session, multiple_documents):
        """Should apply limit and offset"""
        # Get first 5 documents
        page1 = db_session.query(Document).offset(0).limit(5).all()
        assert len(page1) == 5
        
        # Get next 5 documents
        page2 = db_session.query(Document).offset(5).limit(5).all()
        assert len(page2) == 5
        
        # Verify they're different
        assert page1[0].id != page2[0].id
    
    def test_order_by_ascending(self, db_session, multiple_documents):
        """Should order by filename ascending"""
        docs = db_session.query(Document).order_by(Document.filename).all()
        
        for i in range(len(docs) - 1):
            assert docs[i].filename <= docs[i + 1].filename
    
    def test_order_by_descending(self, db_session, multiple_documents):
        """Should order by filename descending"""
        docs = db_session.query(Document).order_by(Document.filename.desc()).all()
        
        for i in range(len(docs) - 1):
            assert docs[i].filename >= docs[i + 1].filename


# ============================================================================
# SEARCH Tests
# ============================================================================

class TestSearch:
    """Test search functionality"""
    
    def test_search_documents_by_filename(self, db_session, sample_document):
        """Should search documents by filename"""
        found = db_session.query(Document).filter(
            Document.filename.ilike(f"%{sample_document.filename}%")
        ).all()
        
        assert len(found) >= 1
        assert any(d.id == sample_document.id for d in found)
    
    def test_search_chunks_by_text(self, db_session, sample_chunks):
        """Should search chunks by text"""
        search_term = "Chunk 0"
        found = db_session.query(DocumentChunk).filter(
            DocumentChunk.text.ilike(f"%{search_term}%")
        ).all()
        
        assert len(found) >= 1


# ============================================================================
# RELATIONSHIP Tests
# ============================================================================

class TestRelationships:
    """Test model relationships"""
    
    def test_tenant_has_users(self, db_session, sample_tenant, sample_user):
        """Should navigate tenant to users"""
        assert sample_user.tenant_id == sample_tenant.id
    
    def test_document_has_chunks(self, db_session, sample_document, sample_chunks):
        """Should navigate document to chunks"""
        assert sample_chunks[0].doc_id == sample_document.id
    
    def test_user_has_search_logs(self, db_session, sample_user, sample_search_logs):
        """Should navigate user to search logs"""
        logs = db_session.query(SearchLog).filter_by(user_id=sample_user.id).all()
        assert len(logs) >= 1


# ============================================================================
# PERFORMANCE Tests
# ============================================================================

class TestPerformance:
    """Test query performance with large datasets"""
    
    def test_bulk_create_performance(self, db_session, sample_tenant):
        """Should handle bulk creation efficiently"""
        users = []
        for i in range(100):
            user = User(
                id=uuid.uuid4(),
                tenant_id=sample_tenant.id,
                email=f"perf_test_{i}@example.com",
                password_hash="hash",
                is_active=True,
                role="user"
            )
            users.append(user)
        
        db_session.add_all(users)
        db_session.commit()
        
        count = db_session.query(User).filter(
            User.email.like("perf_test_%")
        ).count()
        assert count == 100
    
    def test_large_dataset_query(self, db_session, bulk_test_data):
        """Should query large dataset efficiently"""
        # Query all documents across all tenants
        count = db_session.query(Document).count()
        assert count > 50  # From bulk_test_data fixture
    
    def test_indexed_query_performance(self, db_session, multiple_documents):
        """Should use index for tenant filtering"""
        # This should be fast due to tenant_id index
        tenant_id = multiple_documents[0].tenant_id
        docs = db_session.query(Document).filter_by(
            tenant_id=tenant_id
        ).all()
        
        assert len(docs) >= 1
        for doc in docs:
            assert doc.tenant_id == tenant_id
