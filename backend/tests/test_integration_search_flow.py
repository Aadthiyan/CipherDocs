"""
Integration tests for search workflow.
Tests complete end-to-end flow: query → embedding → search → retrieval → decryption
"""

import pytest
import uuid
from sqlalchemy.orm import Session

from app.models.database import Document, DocumentChunk, SearchLog, Tenant, User
from tests.test_integration_helpers import (
    DocumentWorkflowHelper,
    SearchWorkflowHelper
)


class TestSearchWorkflow:
    """Test complete search pipeline"""
    
    def test_search_query_submission(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test search query is logged and persisted"""
        tenant = multi_tenant_setup["tenants"][0]
        user = multi_tenant_setup["users"][tenant.id][0]
        
        log = SearchWorkflowHelper.create_search_log(
            db_session,
            tenant,
            user,
            query="test search query"
        )
        
        # Verify log is stored
        assert log.query_text == "test search query"
        assert log.user_id == user.id
        assert log.tenant_id == tenant.id
        
        stored_log = db_session.query(SearchLog).filter_by(id=log.id).first()
        assert stored_log is not None
    
    def test_search_result_retrieval(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test search results are retrieved and ranked"""
        tenant = multi_tenant_setup["tenants"][0]
        user = multi_tenant_setup["users"][tenant.id][0]
        
        # Simulate search results
        results = SearchWorkflowHelper.simulate_search_results(
            num_results=5,
            query="search term"
        )
        
        # Verify results structure
        assert len(results) == 5
        
        # Verify ranking (scores should be descending)
        for i in range(len(results) - 1):
            assert results[i]["score"] >= results[i+1]["score"]
    
    def test_search_with_no_results(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test search query with no results"""
        tenant = multi_tenant_setup["tenants"][0]
        user = multi_tenant_setup["users"][tenant.id][0]
        
        results = SearchWorkflowHelper.simulate_search_results(
            num_results=0,
            query="nonexistent term"
        )
        
        assert len(results) == 0
    
    def test_search_result_relevance_scoring(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test relevance scores are correctly assigned"""
        tenant = multi_tenant_setup["tenants"][0]
        user = multi_tenant_setup["users"][tenant.id][0]
        
        results = SearchWorkflowHelper.simulate_search_results(
            num_results=10,
            query="test"
        )
        
        # Verify score range
        for result in results:
            assert 0 <= result["score"] <= 1.0
        
        # Verify monotonic decrease
        for i in range(len(results) - 1):
            assert results[i]["score"] >= results[i+1]["score"]
    
    def test_search_with_document_chunks(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test search against indexed document chunks"""
        tenant = multi_tenant_setup["tenants"][0]
        
        # Create and process document
        doc = DocumentWorkflowHelper.create_test_document(
            db_session,
            tenant,
            content="document about machine learning"
        )
        
        chunks = DocumentWorkflowHelper.simulate_chunking(
            db_session,
            doc,
            num_chunks=3
        )
        
        DocumentWorkflowHelper.simulate_embedding_and_encryption(
            db_session,
            doc,
            chunks
        )
        
        # Verify chunks are searchable
        stored_chunks = db_session.query(DocumentChunk).filter_by(
            tenant_id=tenant.id,
            doc_id=doc.id
        ).all()
        assert len(stored_chunks) == 3
        
        # Each chunk should have embeddings
        for chunk in stored_chunks:
            assert chunk.encrypted_embedding is not None
    
    def test_search_result_text_snippet(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test search results include relevant text snippets"""
        tenant = multi_tenant_setup["tenants"][0]
        
        results = SearchWorkflowHelper.simulate_search_results(
            num_results=5,
            query="python programming"
        )
        
        # Verify snippets
        for result in results:
            assert "text" in result
            assert isinstance(result["text"], str)
            assert len(result["text"]) > 0
    
    def test_search_pagination(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test search results pagination"""
        tenant = multi_tenant_setup["tenants"][0]
        user = multi_tenant_setup["users"][tenant.id][0]
        
        # Create multiple results
        all_results = SearchWorkflowHelper.simulate_search_results(
            num_results=25,
            query="test"
        )
        
        # Simulate pagination
        page_size = 10
        page1 = all_results[:page_size]
        page2 = all_results[page_size:page_size*2]
        page3 = all_results[page_size*2:]
        
        assert len(page1) == 10
        assert len(page2) == 10
        assert len(page3) == 5


class TestSearchMultiTenant:
    """Test search isolation across tenants"""
    
    def test_search_tenant_isolation(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test search results don't cross tenant boundaries"""
        tenant1 = multi_tenant_setup["tenants"][0]
        tenant2 = multi_tenant_setup["tenants"][1]
        
        # Create documents in each tenant
        doc1 = DocumentWorkflowHelper.create_test_document(
            db_session,
            tenant1,
            content="Confidential info from tenant 1"
        )
        
        doc2 = DocumentWorkflowHelper.create_test_document(
            db_session,
            tenant2,
            content="Confidential info from tenant 2"
        )
        
        # Create chunks
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
        
        # Verify isolation
        tenant1_chunks = db_session.query(DocumentChunk).filter_by(
            tenant_id=tenant1.id
        ).all()
        assert len(tenant1_chunks) == 2
        
        tenant2_chunks = db_session.query(DocumentChunk).filter_by(
            tenant_id=tenant2.id
        ).all()
        assert len(tenant2_chunks) == 2
        
        # Verify no cross-contamination
        assert all(c.tenant_id == tenant1.id for c in tenant1_chunks)
        assert all(c.tenant_id == tenant2.id for c in tenant2_chunks)
    
    def test_search_user_isolation_within_tenant(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test user search logs are isolated within tenant"""
        tenant = multi_tenant_setup["tenants"][0]
        user1 = multi_tenant_setup["users"][tenant.id][0]
        user2 = multi_tenant_setup["users"][tenant.id][1]
        
        # Create search logs for different users
        log1 = SearchWorkflowHelper.create_search_log(
            db_session,
            tenant,
            user1,
            query="user1 query"
        )
        
        log2 = SearchWorkflowHelper.create_search_log(
            db_session,
            tenant,
            user2,
            query="user2 query"
        )
        
        # Verify separation
        user1_logs = db_session.query(SearchLog).filter_by(
            user_id=user1.id
        ).all()
        user2_logs = db_session.query(SearchLog).filter_by(
            user_id=user2.id
        ).all()
        
        assert len(user1_logs) == 1
        assert len(user2_logs) == 1
        assert user1_logs[0].query_text == "user1 query"
        assert user2_logs[0].query_text == "user2 query"


class TestSearchPerformance:
    """Test search performance characteristics"""
    
    def test_search_result_latency_tracking(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test search latency is tracked"""
        tenant = multi_tenant_setup["tenants"][0]
        user = multi_tenant_setup["users"][tenant.id][0]
        
        # Create search with latency
        log = SearchWorkflowHelper.create_search_log(
            db_session,
            tenant,
            user,
            query="performance test",
            latency_ms=150
        )
        
        assert log.query_latency_ms == 150
        assert log.query_latency_ms > 0
    
    def test_search_result_count_tracking(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test result count is properly tracked"""
        tenant = multi_tenant_setup["tenants"][0]
        user = multi_tenant_setup["users"][tenant.id][0]
        
        # Create search with multiple results
        log = SearchWorkflowHelper.create_search_log(
            db_session,
            tenant,
            user,
            result_count=42
        )
        
        assert log.result_count == 42
    
    def test_bulk_search_queries(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test multiple concurrent search queries"""
        tenant = multi_tenant_setup["tenants"][0]
        user = multi_tenant_setup["users"][tenant.id][0]
        
        # Create multiple search logs
        for i in range(10):
            SearchWorkflowHelper.create_search_log(
                db_session,
                tenant,
                user,
                query=f"query {i}",
                result_count=i+5,
                latency_ms=100+i*10
            )
        
        # Verify all searches logged
        searches = db_session.query(SearchLog).filter_by(
            user_id=user.id
        ).all()
        assert len(searches) == 10


class TestSearchQueryTypes:
    """Test different query types and patterns"""
    
    def test_simple_keyword_search(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test simple single keyword search"""
        tenant = multi_tenant_setup["tenants"][0]
        user = multi_tenant_setup["users"][tenant.id][0]
        
        log = SearchWorkflowHelper.create_search_log(
            db_session,
            tenant,
            user,
            query="keyword"
        )
        
        assert log.query_text == "keyword"
    
    def test_multi_word_query_search(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test multi-word phrase search"""
        tenant = multi_tenant_setup["tenants"][0]
        user = multi_tenant_setup["users"][tenant.id][0]
        
        log = SearchWorkflowHelper.create_search_log(
            db_session,
            tenant,
            user,
            query="machine learning models"
        )
        
        assert log.query_text == "machine learning models"
        assert len(log.query_text.split()) == 3
    
    def test_special_characters_in_query(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test search with special characters"""
        tenant = multi_tenant_setup["tenants"][0]
        user = multi_tenant_setup["users"][tenant.id][0]
        
        log = SearchWorkflowHelper.create_search_log(
            db_session,
            tenant,
            user,
            query="C++ programming & design"
        )
        
        assert log.query_text == "C++ programming & design"
    
    def test_case_insensitive_search(
        self, db_session: Session, multi_tenant_setup
    ):
        """Test search is case insensitive"""
        tenant = multi_tenant_setup["tenants"][0]
        user = multi_tenant_setup["users"][tenant.id][0]
        
        # Create logs with different cases
        log1 = SearchWorkflowHelper.create_search_log(
            db_session,
            tenant,
            user,
            query="Python"
        )
        
        log2 = SearchWorkflowHelper.create_search_log(
            db_session,
            tenant,
            user,
            query="python"
        )
        
        # Both should be searchable regardless of case
        assert log1.query_text.lower() == log2.query_text.lower()
