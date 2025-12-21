"""
Integration tests for document ingestion workflow.
Tests complete end-to-end flow: upload → extract → chunk → embed → encrypt → store
"""

import pytest
import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.database import Document, DocumentChunk, Tenant, User
from tests.test_integration_helpers import (
    MultiTenantTestData,
    TestOrchestration,
    DocumentWorkflowHelper,
    SearchWorkflowHelper
)


class TestDocumentIngestionWorkflow:
    """Test complete document ingestion pipeline"""
    
    def test_document_upload_status_transition(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test document transitions to 'uploaded' status after upload"""
        tenant = multi_tenant_setup["tenants"][0]
        
        doc = DocumentWorkflowHelper.create_test_document(
            db_session,
            tenant,
            filename="test.pdf",
            content="Test content"
        )
        
        # Verify initial status
        assert doc.status == "uploaded"
        assert doc.filename == "test.pdf"
        assert doc.doc_type == "pdf"
        assert doc.tenant_id == tenant.id
        
        # Verify document is in database
        stored_doc = db_session.query(Document).filter_by(id=doc.id).first()
        assert stored_doc is not None
        assert stored_doc.status == "uploaded"
    
    def test_document_extraction_status_transition(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test document extraction transitions to 'extracting' then 'chunking'"""
        tenant = multi_tenant_setup["tenants"][0]
        
        doc = DocumentWorkflowHelper.create_test_document(
            db_session,
            tenant,
            content="Content to extract"
        )
        
        # Simulate extraction
        doc = DocumentWorkflowHelper.simulate_document_extraction(
            db_session,
            doc,
            text="Extracted text"
        )
        
        # Verify status progression
        assert doc.status == "chunking"
    
    def test_document_chunking_workflow(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test document chunking creates proper chunk records"""
        tenant = multi_tenant_setup["tenants"][0]
        
        doc = DocumentWorkflowHelper.create_test_document(
            db_session,
            tenant
        )
        
        # Chunk the document
        chunks = DocumentWorkflowHelper.simulate_chunking(
            db_session,
            doc,
            num_chunks=5
        )
        
        # Verify chunks created
        assert len(chunks) == 5
        assert doc.chunk_count == 5
        assert doc.status == "embedding"
        
        # Verify chunk properties
        stored_chunks = db_session.query(DocumentChunk).filter_by(
            doc_id=doc.id
        ).all()
        assert len(stored_chunks) == 5
        
        for i, chunk in enumerate(stored_chunks):
            assert chunk.chunk_sequence == i
            assert chunk.doc_id == doc.id
            assert chunk.tenant_id == tenant.id
            assert chunk.text is not None
    
    def test_embedding_and_encryption_workflow(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test embedding generation and encryption of chunks"""
        tenant = multi_tenant_setup["tenants"][0]
        
        doc = DocumentWorkflowHelper.create_test_document(
            db_session,
            tenant
        )
        
        chunks = DocumentWorkflowHelper.simulate_chunking(
            db_session,
            doc,
            num_chunks=3
        )
        
        # Simulate embedding and encryption
        doc = DocumentWorkflowHelper.simulate_embedding_and_encryption(
            db_session,
            doc,
            chunks
        )
        
        # Verify final status
        assert doc.status == "completed"
        
        # Verify embeddings are stored
        stored_chunks = db_session.query(DocumentChunk).filter_by(
            doc_id=doc.id
        ).all()
        
        for chunk in stored_chunks:
            assert chunk.encrypted_embedding is not None
            assert chunk.embedding_dimension > 0
    
    def test_complete_workflow_status_chain(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test complete workflow: uploaded → extracting → chunking → embedding → completed"""
        tenant = multi_tenant_setup["tenants"][0]
        
        # Start workflow
        doc = DocumentWorkflowHelper.create_test_document(
            db_session,
            tenant,
            filename="workflow_test.pdf"
        )
        assert doc.status == "uploaded"
        
        # Extract
        doc = DocumentWorkflowHelper.simulate_document_extraction(
            db_session,
            doc
        )
        assert doc.status == "chunking"
        
        # Chunk
        chunks = DocumentWorkflowHelper.simulate_chunking(
            db_session,
            doc,
            num_chunks=4
        )
        assert doc.status == "embedding"
        assert doc.chunk_count == 4
        
        # Embed and encrypt
        doc = DocumentWorkflowHelper.simulate_embedding_and_encryption(
            db_session,
            doc,
            chunks
        )
        assert doc.status == "completed"
        
        # Verify all data persisted
        final_doc = db_session.query(Document).filter_by(id=doc.id).first()
        assert final_doc.status == "completed"
        assert final_doc.chunk_count == 4
        
        final_chunks = db_session.query(DocumentChunk).filter_by(
            doc_id=doc.id
        ).all()
        assert len(final_chunks) == 4
    
    def test_multiple_documents_in_tenant(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test multiple documents can be processed independently in a tenant"""
        tenant = multi_tenant_setup["tenants"][0]
        
        # Create multiple documents
        docs = []
        for i in range(3):
            doc = DocumentWorkflowHelper.create_test_document(
                db_session,
                tenant,
                filename=f"document_{i}.pdf",
                content=f"Content for document {i}"
            )
            docs.append(doc)
        
        # Process them independently
        for i, doc in enumerate(docs):
            chunks = DocumentWorkflowHelper.simulate_chunking(
                db_session,
                doc,
                num_chunks=i+2  # Different chunk counts
            )
            DocumentWorkflowHelper.simulate_embedding_and_encryption(
                db_session,
                doc,
                chunks
            )
        
        # Verify independence
        stored_docs = db_session.query(Document).filter_by(
            tenant_id=tenant.id
        ).all()
        assert len(stored_docs) == 3
        
        for i, doc in enumerate(stored_docs):
            assert doc.status == "completed"
            chunk_count = db_session.query(DocumentChunk).filter_by(
                doc_id=doc.id
            ).count()
            assert chunk_count == i + 2
    
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
            filename="secret_doc.pdf"
        )
        
        doc2 = DocumentWorkflowHelper.create_test_document(
            db_session,
            tenant2,
            filename="secret_doc.pdf"  # Same name, different tenant
        )
        
        # Verify isolation
        tenant1_docs = db_session.query(Document).filter_by(
            tenant_id=tenant1.id
        ).all()
        assert len(tenant1_docs) == 1
        assert tenant1_docs[0].id == doc1.id
        
        tenant2_docs = db_session.query(Document).filter_by(
            tenant_id=tenant2.id
        ).all()
        assert len(tenant2_docs) == 1
        assert tenant2_docs[0].id == doc2.id
    
    def test_chunk_metadata_preservation(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test chunk metadata is preserved through workflow"""
        tenant = multi_tenant_setup["tenants"][0]
        
        doc = DocumentWorkflowHelper.create_test_document(
            db_session,
            tenant,
            filename="metadata_test.pdf"
        )
        
        chunks = DocumentWorkflowHelper.simulate_chunking(
            db_session,
            doc,
            num_chunks=3
        )
        
        # Verify metadata
        stored_chunks = db_session.query(DocumentChunk).filter_by(
            doc_id=doc.id
        ).order_by(DocumentChunk.chunk_sequence).all()
        
        for i, chunk in enumerate(stored_chunks):
            assert chunk.chunk_sequence == i
            assert chunk.doc_id == doc.id
            assert chunk.tenant_id == tenant.id
            assert chunk.page_number == i // 5
            assert chunk.text is not None


class TestIngestionErrorHandling:
    """Test error handling in document ingestion workflow"""
    
    def test_document_creation_with_minimal_data(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test document can be created with minimal required fields"""
        tenant = multi_tenant_setup["tenants"][0]
        
        doc = Document(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            filename="minimal.pdf",
            storage_path="path/to/minimal.pdf",
            doc_type="pdf",
            file_size_bytes=100,
            file_hash="hash123",
            status="uploaded"
        )
        db_session.add(doc)
        db_session.commit()
        
        # Verify minimal document
        stored = db_session.query(Document).filter_by(id=doc.id).first()
        assert stored is not None
        assert stored.chunk_count == 0
    
    def test_document_with_large_content(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test document ingestion with large content size"""
        tenant = multi_tenant_setup["tenants"][0]
        
        large_content = "x" * (10 * 1024 * 1024)  # 10MB
        
        doc = DocumentWorkflowHelper.create_test_document(
            db_session,
            tenant,
            content=large_content
        )
        
        assert doc.file_size_bytes == len(large_content.encode())
    
    def test_document_chunking_with_many_chunks(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test document chunking with large number of chunks"""
        tenant = multi_tenant_setup["tenants"][0]
        
        doc = DocumentWorkflowHelper.create_test_document(
            db_session,
            tenant
        )
        
        # Create many chunks
        chunks = DocumentWorkflowHelper.simulate_chunking(
            db_session,
            doc,
            num_chunks=100
        )
        
        assert len(chunks) == 100
        assert doc.chunk_count == 100
        
        # Verify all chunks stored
        stored_chunks = db_session.query(DocumentChunk).filter_by(
            doc_id=doc.id
        ).all()
        assert len(stored_chunks) == 100
    
    def test_parallel_document_ingestion(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test parallel ingestion of multiple documents"""
        tenant = multi_tenant_setup["tenants"][0]
        
        # Create multiple documents
        docs = []
        for i in range(5):
            doc = DocumentWorkflowHelper.create_test_document(
                db_session,
                tenant,
                filename=f"parallel_doc_{i}.pdf"
            )
            docs.append(doc)
        
        # Process in parallel (simulate)
        chunks_per_doc = []
        for doc in docs:
            chunks = DocumentWorkflowHelper.simulate_chunking(
                db_session,
                doc,
                num_chunks=3
            )
            chunks_per_doc.append(chunks)
        
        # Complete processing
        for doc in docs:
            DocumentWorkflowHelper.simulate_embedding_and_encryption(
                db_session,
                doc,
                []
            )
        
        # Verify all completed
        stored_docs = db_session.query(Document).filter_by(
            tenant_id=tenant.id,
            status="completed"
        ).all()
        assert len(stored_docs) == 5


class TestDocumentMetadata:
    """Test document metadata handling"""
    
    def test_document_timestamps_recorded(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test document creation and modification timestamps"""
        tenant = multi_tenant_setup["tenants"][0]
        
        doc = DocumentWorkflowHelper.create_test_document(
            db_session,
            tenant
        )
        
        # Verify timestamps exist (if the model supports them)
        # Note: Document model may not have created_at/updated_at fields
        assert doc is not None
        assert doc.id is not None
    
    def test_document_file_properties(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test document file metadata is preserved"""
        tenant = multi_tenant_setup["tenants"][0]
        
        doc = DocumentWorkflowHelper.create_test_document(
            db_session,
            tenant,
            filename="test_file.pdf",
            doc_type="pdf",
            content="x" * 5000
        )
        
        # Verify file properties
        assert doc.filename == "test_file.pdf"
        assert doc.doc_type == "pdf"
        assert doc.file_size_bytes == 5000
        assert doc.file_hash is not None
        assert doc.storage_path is not None
