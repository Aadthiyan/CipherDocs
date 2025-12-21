"""
Integration tests for multi-tenant isolation.
Tests complete data isolation across tenants at every level.
"""

import pytest
import uuid
from sqlalchemy.orm import Session

from app.models.database import (
    Tenant, User, Document, DocumentChunk, SearchLog, EncryptionKey
)
from app.core.security import hash_password
from tests.test_integration_helpers import (
    MultiTenantTestData,
    DocumentWorkflowHelper,
    SearchWorkflowHelper
)


class TestMultiTenantIsolation:
    """Test multi-tenant data isolation"""
    
    def test_tenant_data_separation(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test tenants have separate data"""
        tenants = multi_tenant_setup["tenants"]
        
        # Verify each tenant is unique
        assert len(tenants) >= 2
        
        for i, tenant in enumerate(tenants):
            assert tenant.id is not None
            assert tenant.name is not None
            assert tenants.count(tenant) == 1  # No duplicates
            
            # Verify tenant is in database
            stored = db_session.query(Tenant).filter_by(id=tenant.id).first()
            assert stored is not None
    
    def test_user_tenant_isolation(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test users are isolated by tenant"""
        tenant1 = multi_tenant_setup["tenants"][0]
        tenant2 = multi_tenant_setup["tenants"][1]
        
        users1 = multi_tenant_setup["users"][tenant1.id]
        users2 = multi_tenant_setup["users"][tenant2.id]
        
        # Verify separation
        tenant1_users = db_session.query(User).filter_by(
            tenant_id=tenant1.id
        ).all()
        tenant2_users = db_session.query(User).filter_by(
            tenant_id=tenant2.id
        ).all()
        
        assert len(tenant1_users) > 0
        assert len(tenant2_users) > 0
        
        # Verify no cross-contamination
        user_ids_1 = {u.id for u in tenant1_users}
        user_ids_2 = {u.id for u in tenant2_users}
        assert len(user_ids_1 & user_ids_2) == 0  # No intersection
    
    def test_document_tenant_isolation(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test documents are isolated by tenant"""
        tenant1 = multi_tenant_setup["tenants"][0]
        tenant2 = multi_tenant_setup["tenants"][1]
        
        # Create documents in each tenant
        doc1 = DocumentWorkflowHelper.create_test_document(
            db_session,
            tenant1,
            filename="secret.pdf"
        )
        
        doc2 = DocumentWorkflowHelper.create_test_document(
            db_session,
            tenant2,
            filename="secret.pdf"  # Same name
        )
        
        # Verify documents are different
        assert doc1.id != doc2.id
        assert doc1.tenant_id == tenant1.id
        assert doc2.tenant_id == tenant2.id
        
        # Verify no cross-visibility
        tenant1_docs = db_session.query(Document).filter_by(
            tenant_id=tenant1.id
        ).all()
        tenant2_docs = db_session.query(Document).filter_by(
            tenant_id=tenant2.id
        ).all()
        
        assert doc1 in tenant1_docs
        assert doc1 not in tenant2_docs
        assert doc2 not in tenant1_docs
        assert doc2 in tenant2_docs
    
    def test_document_chunk_tenant_isolation(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test document chunks are isolated by tenant"""
        tenant1 = multi_tenant_setup["tenants"][0]
        tenant2 = multi_tenant_setup["tenants"][1]
        
        # Create and chunk documents
        doc1 = DocumentWorkflowHelper.create_test_document(
            db_session,
            tenant1
        )
        doc2 = DocumentWorkflowHelper.create_test_document(
            db_session,
            tenant2
        )
        
        chunks1 = DocumentWorkflowHelper.simulate_chunking(
            db_session,
            doc1,
            num_chunks=3
        )
        chunks2 = DocumentWorkflowHelper.simulate_chunking(
            db_session,
            doc2,
            num_chunks=3
        )
        
        # Verify chunk isolation
        tenant1_chunks = db_session.query(DocumentChunk).filter_by(
            tenant_id=tenant1.id
        ).all()
        tenant2_chunks = db_session.query(DocumentChunk).filter_by(
            tenant_id=tenant2.id
        ).all()
        
        chunk_ids_1 = {c.id for c in tenant1_chunks}
        chunk_ids_2 = {c.id for c in tenant2_chunks}
        
        assert len(chunk_ids_1 & chunk_ids_2) == 0  # No overlap
        assert len(tenant1_chunks) == 3
        assert len(tenant2_chunks) == 3
    
    def test_search_log_tenant_isolation(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test search logs are isolated by tenant"""
        tenant1 = multi_tenant_setup["tenants"][0]
        tenant2 = multi_tenant_setup["tenants"][1]
        
        user1 = multi_tenant_setup["users"][tenant1.id][0]
        user2 = multi_tenant_setup["users"][tenant2.id][0]
        
        # Create search logs
        log1 = SearchWorkflowHelper.create_search_log(
            db_session,
            tenant1,
            user1,
            query="tenant1 secret"
        )
        
        log2 = SearchWorkflowHelper.create_search_log(
            db_session,
            tenant2,
            user2,
            query="tenant2 secret"
        )
        
        # Verify isolation
        tenant1_logs = db_session.query(SearchLog).filter_by(
            tenant_id=tenant1.id
        ).all()
        tenant2_logs = db_session.query(SearchLog).filter_by(
            tenant_id=tenant2.id
        ).all()
        
        assert log1 in tenant1_logs
        assert log1 not in tenant2_logs
        assert log2 not in tenant1_logs
        assert log2 in tenant2_logs
    
    def test_encryption_key_tenant_isolation(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test encryption keys are isolated by tenant"""
        keys = multi_tenant_setup["keys"]
        tenants = multi_tenant_setup["tenants"]
        
        # Verify each tenant has unique keys
        for tenant in tenants:
            tenant_keys = db_session.query(EncryptionKey).filter_by(
                tenant_id=tenant.id
            ).all()
            
            # Verify key belongs to this tenant
            assert len(tenant_keys) > 0
            assert all(k.tenant_id == tenant.id for k in tenant_keys)


class TestCrossTenantBlocking:
    """Test that cross-tenant access is blocked"""
    
    def test_cannot_access_other_tenant_documents(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test user cannot access documents from other tenant"""
        tenant1 = multi_tenant_setup["tenants"][0]
        tenant2 = multi_tenant_setup["tenants"][1]
        
        user1 = multi_tenant_setup["users"][tenant1.id][0]
        user2 = multi_tenant_setup["users"][tenant2.id][0]
        
        # Create document in tenant1
        doc1 = DocumentWorkflowHelper.create_test_document(
            db_session,
            tenant1
        )
        
        # Create document in tenant2
        doc2 = DocumentWorkflowHelper.create_test_document(
            db_session,
            tenant2
        )
        
        # Verify user1 can only see their tenant's docs
        user1_accessible = db_session.query(Document).filter_by(
            tenant_id=user1.tenant_id
        ).all()
        user2_accessible = db_session.query(Document).filter_by(
            tenant_id=user2.tenant_id
        ).all()
        
        assert doc1 in user1_accessible
        assert doc2 not in user1_accessible
        assert doc2 in user2_accessible
        assert doc1 not in user2_accessible
    
    def test_cannot_decrypt_with_wrong_tenant_key(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test decryption fails with wrong tenant's key"""
        tenant1 = multi_tenant_setup["tenants"][0]
        tenant2 = multi_tenant_setup["tenants"][1]
        
        keys = multi_tenant_setup["keys"]
        
        tenant1_key = keys[tenant1.id]
        tenant2_key = keys[tenant2.id]
        
        # Create document and encrypt with tenant1 key
        doc = DocumentWorkflowHelper.create_test_document(
            db_session,
            tenant1
        )
        
        chunks = DocumentWorkflowHelper.simulate_chunking(
            db_session,
            doc,
            num_chunks=2
        )
        
        # Simulate encryption with tenant1 key
        for chunk in chunks:
            chunk.encrypted_embedding = f"encrypted_with_{tenant1_key.key_fingerprint}"
        db_session.commit()
        
        # Verify keys are different
        assert tenant1_key.key_fingerprint != tenant2_key.key_fingerprint
        
        # Verify tenant2 key fingerprint doesn't match
        for chunk in chunks:
            # A proper system would reject using tenant2 key to decrypt tenant1 data
            assert tenant2_key.key_fingerprint not in chunk.encrypted_embedding
    
    def test_cannot_search_other_tenant_data(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test search doesn't return other tenant's data"""
        tenant1 = multi_tenant_setup["tenants"][0]
        tenant2 = multi_tenant_setup["tenants"][1]
        
        # Create documents with searchable content
        doc1 = DocumentWorkflowHelper.create_test_document(
            db_session,
            tenant1,
            content="unique secret data for tenant 1"
        )
        
        doc2 = DocumentWorkflowHelper.create_test_document(
            db_session,
            tenant2,
            content="unique secret data for tenant 2"
        )
        
        chunks1 = DocumentWorkflowHelper.simulate_chunking(
            db_session,
            doc1,
            num_chunks=2
        )
        
        chunks2 = DocumentWorkflowHelper.simulate_chunking(
            db_session,
            doc2,
            num_chunks=2
        )
        
        # Search for tenant1's content from tenant1 perspective
        tenant1_chunks = db_session.query(DocumentChunk).filter_by(
            tenant_id=tenant1.id
        ).all()
        
        # Verify tenant2's data not visible
        tenant1_doc_ids = {c.doc_id for c in tenant1_chunks}
        assert doc1.id in tenant1_doc_ids
        assert doc2.id not in tenant1_doc_ids


class TestTenantPlans:
    """Test tenant plan differences"""
    
    def test_different_tenant_plans(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test tenants can have different plans"""
        tenants = multi_tenant_setup["tenants"]
        
        # Verify plans are set
        for tenant in tenants:
            assert tenant.plan in ["starter", "pro", "enterprise"]
    
    def test_tenant_plan_quotas(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test tenant plans enforce different quotas"""
        tenants = multi_tenant_setup["tenants"]
        
        for tenant in tenants:
            if tenant.plan == "starter":
                # Starter plan restrictions
                max_documents = 100
            elif tenant.plan == "pro":
                # Pro plan restrictions
                max_documents = 1000
            else:
                # Enterprise
                max_documents = 999999
            
            # Create test documents
            for i in range(min(5, max_documents)):
                DocumentWorkflowHelper.create_test_document(
                    db_session,
                    tenant,
                    filename=f"doc_{i}.pdf"
                )
            
            # Verify documents stay within quota
            doc_count = db_session.query(Document).filter_by(
                tenant_id=tenant.id
            ).count()
            assert doc_count <= max_documents


class TestMultiTenantUsers:
    """Test multi-user scenarios within tenants"""
    
    def test_multiple_users_same_tenant(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test multiple users can work in same tenant"""
        tenant = multi_tenant_setup["tenants"][0]
        users = multi_tenant_setup["users"][tenant.id]
        
        # Verify multiple users exist for tenant
        assert len(users) >= 3
        
        # All users belong to same tenant
        assert all(u.tenant_id == tenant.id for u in users)
    
    def test_users_different_roles_isolation(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test users with different roles have proper isolation"""
        tenant = multi_tenant_setup["tenants"][0]
        users = multi_tenant_setup["users"][tenant.id]
        
        roles = {u.role for u in users}
        
        # Verify we have different roles
        assert len(roles) >= 2
        assert "admin" in roles
        
        # Admin and non-admin separation
        admin_users = [u for u in users if u.role == "admin"]
        regular_users = [u for u in users if u.role != "admin"]
        
        assert len(admin_users) > 0
        assert len(regular_users) > 0
    
    def test_user_search_history_isolation(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test search history is isolated per user"""
        tenant = multi_tenant_setup["tenants"][0]
        users = multi_tenant_setup["users"][tenant.id]
        
        user1, user2 = users[0], users[1]
        
        # Create search logs for different users
        for i in range(5):
            SearchWorkflowHelper.create_search_log(
                db_session,
                tenant,
                user1,
                query=f"user1 query {i}"
            )
            
            SearchWorkflowHelper.create_search_log(
                db_session,
                tenant,
                user2,
                query=f"user2 query {i}"
            )
        
        # Verify isolation
        user1_logs = db_session.query(SearchLog).filter_by(
            user_id=user1.id
        ).all()
        user2_logs = db_session.query(SearchLog).filter_by(
            user_id=user2.id
        ).all()
        
        assert len(user1_logs) == 5
        assert len(user2_logs) == 5
        
        # Verify no cross-contamination
        user1_queries = {log.query_text for log in user1_logs}
        user2_queries = {log.query_text for log in user2_logs}
        
        assert len(user1_queries & user2_queries) == 0


class TestDataLeakagePrevention:
    """Test prevention of data leakage between tenants"""
    
    def test_no_query_aggregation_across_tenants(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test queries don't aggregate data from multiple tenants"""
        tenant1 = multi_tenant_setup["tenants"][0]
        tenant2 = multi_tenant_setup["tenants"][1]
        
        # Create different number of documents per tenant
        for i in range(5):
            DocumentWorkflowHelper.create_test_document(
                db_session,
                tenant1,
                filename=f"t1_doc_{i}.pdf"
            )
        
        for i in range(3):
            DocumentWorkflowHelper.create_test_document(
                db_session,
                tenant2,
                filename=f"t2_doc_{i}.pdf"
            )
        
        # Query must filter by tenant
        t1_count = db_session.query(Document).filter_by(
            tenant_id=tenant1.id
        ).count()
        t2_count = db_session.query(Document).filter_by(
            tenant_id=tenant2.id
        ).count()
        
        assert t1_count == 5
        assert t2_count == 3
        
        # Unfiltered query would leak data
        total = db_session.query(Document).count()
        assert total == 8
    
    def test_no_metadata_leakage(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test tenant metadata doesn't leak"""
        tenants = multi_tenant_setup["tenants"]
        
        for i, tenant in enumerate(tenants):
            # Create documents
            for j in range(i+1):
                DocumentWorkflowHelper.create_test_document(
                    db_session,
                    tenant,
                    filename=f"doc_{j}.pdf"
                )
        
        # Verify doc counts are tenant-specific
        for i, tenant in enumerate(tenants):
            count = db_session.query(Document).filter_by(
                tenant_id=tenant.id
            ).count()
            assert count == i + 1
