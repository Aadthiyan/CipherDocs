"""
Integration test utilities and fixtures for end-to-end testing.
Provides setup/teardown, multi-tenant helpers, and test orchestration.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.models.database import (
    Tenant, User, Document, DocumentChunk, SearchLog, EncryptionKey, Session as SessionModel
)
from app.core.security import hash_password, create_access_token, create_refresh_token
from app.core.encryption import KeyManager
from app.schemas.auth import Token


# ============================================================================
# Multi-Tenant Test Data Generators
# ============================================================================

class MultiTenantTestData:
    """Generate and manage multi-tenant test scenarios"""
    
    @staticmethod
    def create_tenants(db_session: Session, count: int = 3) -> List[Tenant]:
        """Create multiple test tenants"""
        tenants = []
        for i in range(count):
            tenant = Tenant(
                id=uuid.uuid4(),
                name=f"Integration Test Tenant {i}",
                plan="pro" if i % 2 == 0 else "starter"
            )
            db_session.add(tenant)
            tenants.append(tenant)
        db_session.commit()
        return tenants
    
    @staticmethod
    def create_users_for_tenants(
        db_session: Session,
        tenants: List[Tenant],
        users_per_tenant: int = 3
    ) -> Dict[uuid.UUID, List[User]]:
        """Create users for each tenant with different roles"""
        tenant_users = {}
        roles = ["admin", "user", "viewer"]
        
        for tenant in tenants:
            users = []
            for i in range(users_per_tenant):
                role = roles[i % len(roles)]
                user = User(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    email=f"{role}_user_{i}@tenant_{tenant.id.hex[:8]}.local",
                    password_hash=hash_password(f"Password{i}123!"),
                    is_active=True,
                    role=role
                )
                db_session.add(user)
                users.append(user)
            tenant_users[tenant.id] = users
        
        db_session.commit()
        return tenant_users
    
    @staticmethod
    def create_encryption_keys_for_tenants(
        db_session: Session,
        tenants: List[Tenant]
    ) -> Dict[uuid.UUID, EncryptionKey]:
        """Create encryption keys for each tenant"""
        tenant_keys = {}
        
        for tenant in tenants:
            fingerprint = "sha256_" + uuid.uuid4().hex[:32]
            key = EncryptionKey(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                encrypted_key="test_encrypted_key",
                key_fingerprint=fingerprint,
                is_active=True
            )
            db_session.add(key)
            tenant_keys[tenant.id] = key
        
        db_session.commit()
        return tenant_keys


class TestOrchestration:
    """Manage test setup, execution, and teardown"""
    
    @staticmethod
    def create_authenticated_session(
        db_session: Session,
        user: User,
        tenant: Tenant
    ) -> Tuple[Token, User, Tenant]:
        """Create authenticated session for a user"""
        access_token = create_access_token(
            subject=str(user.id),
            tenant_id=str(tenant.id),
            role=user.role,
            expires_delta=timedelta(hours=1)
        )
        refresh_token = create_refresh_token(
            subject=str(user.id),
            tenant_id=str(tenant.id),
            role=user.role,
            expires_delta=timedelta(days=7)
        )
        
        token = Token(
            access_token=access_token,
            token_type="bearer"
        )
        
        return token, user, tenant
    
    @staticmethod
    def cleanup_tenant_data(db_session: Session, tenant: Tenant):
        """Clean up all data for a tenant"""
        # Delete in order of dependencies
        db_session.query(DocumentChunk).filter_by(tenant_id=tenant.id).delete()
        db_session.query(SearchLog).filter_by(tenant_id=tenant.id).delete()
        db_session.query(Document).filter_by(tenant_id=tenant.id).delete()
        db_session.query(EncryptionKey).filter_by(tenant_id=tenant.id).delete()
        db_session.query(User).filter_by(tenant_id=tenant.id).delete()
        db_session.query(Tenant).filter_by(id=tenant.id).delete()
        db_session.commit()


class DocumentWorkflowHelper:
    """Helper methods for document workflow testing"""
    
    @staticmethod
    def create_test_document(
        db_session: Session,
        tenant: Tenant,
        filename: str = "test_document.pdf",
        doc_type: str = "pdf",
        content: str = "Test document content"
    ) -> Document:
        """Create a test document"""
        doc = Document(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            filename=filename,
            storage_path=f"documents/{tenant.id}/{filename}",
            doc_type=doc_type,
            file_size_bytes=len(content.encode()),
            file_hash="test_hash",
            chunk_count=0,
            status="uploaded"
        )
        db_session.add(doc)
        db_session.commit()
        return doc
    
    @staticmethod
    def simulate_document_extraction(
        db_session: Session,
        document: Document,
        text: str = "Extracted text from document"
    ) -> Document:
        """Simulate document text extraction step"""
        document.status = "extracting"
        db_session.commit()
        
        # Simulate extraction
        document.status = "chunking"
        db_session.commit()
        return document
    
    @staticmethod
    def simulate_chunking(
        db_session: Session,
        document: Document,
        num_chunks: int = 5
    ) -> List[DocumentChunk]:
        """Simulate document chunking"""
        document.status = "chunking"
        db_session.commit()
        
        chunks = []
        for i in range(num_chunks):
            chunk = DocumentChunk(
                id=uuid.uuid4(),
                tenant_id=document.tenant_id,
                doc_id=document.id,
                chunk_sequence=i,
                text=f"Chunk {i} content from {document.filename}",
                encrypted_embedding="mock_embedding",
                embedding_dimension=384,
                page_number=i // 5
            )
            db_session.add(chunk)
            chunks.append(chunk)
        
        document.chunk_count = num_chunks
        document.status = "embedding"
        db_session.commit()
        return chunks
    
    @staticmethod
    def simulate_embedding_and_encryption(
        db_session: Session,
        document: Document,
        chunks: List[DocumentChunk]
    ) -> Document:
        """Simulate embedding and encryption of chunks"""
        for i, chunk in enumerate(chunks):
            chunk.encrypted_embedding = f"encrypted_vector_{i}"
        
        document.status = "indexing"
        db_session.commit()
        
        document.status = "completed"
        db_session.commit()
        return document


class SearchWorkflowHelper:
    """Helper methods for search workflow testing"""
    
    @staticmethod
    def create_search_log(
        db_session: Session,
        tenant: Tenant,
        user: User,
        query: str = "test query",
        result_count: int = 5,
        latency_ms: int = 150
    ) -> SearchLog:
        """Create a search log entry"""
        log = SearchLog(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            user_id=user.id,
            query_text=query,
            result_count=result_count,
            query_latency_ms=latency_ms,
            top_k=10
        )
        db_session.add(log)
        db_session.commit()
        return log
    
    @staticmethod
    def simulate_search_results(
        num_results: int = 5,
        query: str = "test"
    ) -> List[Dict[str, Any]]:
        """Simulate search results from CyborgDB"""
        results = []
        for i in range(num_results):
            results.append({
                "doc_id": str(uuid.uuid4()),
                "chunk_id": str(uuid.uuid4()),
                "score": 1.0 - (i * 0.1),  # Descending relevance
                "text": f"Result {i} matching '{query}'",
                "page": i // 3
            })
        return results


# ============================================================================
# Fixtures for Integration Tests
# ============================================================================

@pytest.fixture
def multi_tenant_setup(db_session):
    """Setup multi-tenant environment with users and keys"""
    tenants = MultiTenantTestData.create_tenants(db_session, count=3)
    tenant_users = MultiTenantTestData.create_users_for_tenants(
        db_session, tenants, users_per_tenant=3
    )
    tenant_keys = MultiTenantTestData.create_encryption_keys_for_tenants(
        db_session, tenants
    )
    
    return {
        "tenants": tenants,
        "users": tenant_users,
        "keys": tenant_keys
    }


@pytest.fixture
def authenticated_client(client, db_session, multi_tenant_setup):
    """Create authenticated test client"""
    tenant = multi_tenant_setup["tenants"][0]
    user = multi_tenant_setup["users"][tenant.id][0]
    
    token, _, _ = TestOrchestration.create_authenticated_session(
        db_session, user, tenant
    )
    
    # Set auth header
    client.headers = {
        "Authorization": f"Bearer {token.access_token}"
    }
    
    return client, token, user, tenant


@pytest.fixture
def document_workflow_helper():
    """Provide document workflow helpers"""
    return DocumentWorkflowHelper()


@pytest.fixture
def search_workflow_helper():
    """Provide search workflow helpers"""
    return SearchWorkflowHelper()
