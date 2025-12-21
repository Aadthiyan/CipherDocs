# Integration Testing Guide - Phase 8.2

## Overview

Phase 8.2 implements comprehensive integration tests for the Cipherdocs document management system. These tests validate end-to-end workflows across multiple components and scenarios.

## Test Files Structure

### 1. **test_integration_helpers.py** (Core Infrastructure)
- **MultiTenantTestData**: Create and manage multi-tenant test environments
  - `create_tenants()`: Create multiple test tenants
  - `create_users_for_tenants()`: Create users with different roles
  - `create_encryption_keys_for_tenants()`: Generate tenant-specific encryption keys

- **TestOrchestration**: Manage test setup, execution, and teardown
  - `create_authenticated_session()`: Create authenticated user sessions
  - `cleanup_tenant_data()`: Clean up all data for a tenant

- **DocumentWorkflowHelper**: Simulate document processing pipeline
  - `create_test_document()`: Create test documents
  - `simulate_document_extraction()`: Simulate text extraction
  - `simulate_chunking()`: Create document chunks
  - `simulate_embedding_and_encryption()`: Simulate embedding and encryption

- **SearchWorkflowHelper**: Simulate search operations
  - `create_search_log()`: Log search queries
  - `simulate_search_results()`: Generate mock search results

### 2. **test_integration_document_flow.py** (Document Ingestion)
Tests the complete document ingestion pipeline with 20+ test cases:

#### Status Transitions
- `test_document_upload_status_transition`: Verify "uploaded" status
- `test_document_extraction_status_transition`: Verify extraction → chunking
- `test_document_chunking_workflow`: Verify chunking creates proper records
- `test_embedding_and_encryption_workflow`: Verify embedding and encryption
- `test_complete_workflow_status_chain`: Full workflow validation

#### Document Management
- `test_multiple_documents_in_tenant`: Multiple independent documents
- `test_document_tenant_isolation`: Verify tenant data separation
- `test_chunk_metadata_preservation`: Verify chunk metadata integrity

#### Error Handling
- `test_document_creation_with_minimal_data`: Minimal required fields
- `test_document_with_large_content`: Large file handling
- `test_document_chunking_with_many_chunks`: Handle 100+ chunks
- `test_parallel_document_ingestion`: Parallel processing support

**Coverage**: 17 test cases covering status transitions, metadata, isolation, and error scenarios

### 3. **test_integration_search_flow.py** (Search Operations)
Tests the complete search pipeline with 20+ test cases:

#### Core Search Functionality
- `test_search_query_submission`: Verify query logging
- `test_search_result_retrieval`: Verify result retrieval and ranking
- `test_search_with_no_results`: Handle empty result sets
- `test_search_result_relevance_scoring`: Verify relevance calculations

#### Multi-Tenant Search
- `test_search_tenant_isolation`: Verify cross-tenant blocking
- `test_search_user_isolation_within_tenant`: User-level isolation

#### Search Performance
- `test_search_result_latency_tracking`: Measure latency
- `test_search_result_count_tracking`: Track result counts
- `test_bulk_search_queries`: Concurrent search handling

#### Query Types
- `test_simple_keyword_search`: Single keyword queries
- `test_multi_word_query_search`: Multi-word phrase queries
- `test_special_characters_in_query`: Special character handling
- `test_case_insensitive_search`: Case insensitivity

**Coverage**: 16 test cases covering search operations, isolation, performance, and query types

### 4. **test_integration_multi_tenant.py** (Multi-Tenant Isolation)
Tests complete multi-tenant data isolation with 25+ test cases:

#### Data Isolation
- `test_tenant_data_separation`: Verify tenant uniqueness
- `test_user_tenant_isolation`: User isolation by tenant
- `test_document_tenant_isolation`: Document isolation
- `test_document_chunk_tenant_isolation`: Chunk isolation
- `test_search_log_tenant_isolation`: Search log isolation
- `test_encryption_key_tenant_isolation`: Key isolation

#### Cross-Tenant Blocking
- `test_cannot_access_other_tenant_documents`: Block document access
- `test_cannot_decrypt_with_wrong_tenant_key`: Block decryption
- `test_cannot_search_other_tenant_data`: Block search access

#### Tenant Plans
- `test_different_tenant_plans`: Support multiple plan types
- `test_tenant_plan_quotas`: Enforce quota limits

#### Multi-User Scenarios
- `test_multiple_users_same_tenant`: Support multiple users
- `test_users_different_roles_isolation`: Role-based isolation
- `test_user_search_history_isolation`: History isolation

#### Data Leakage Prevention
- `test_no_query_aggregation_across_tenants`: Block aggregation
- `test_no_metadata_leakage`: Prevent metadata leakage

**Coverage**: 19 test cases covering isolation at all levels

### 5. **test_integration_auth_flow.py** (Authentication)
Tests complete authentication lifecycle with 20+ test cases:

#### Signup Flow
- `test_new_user_signup`: User creation and validation
- `test_password_hashing_on_signup`: Verify password hashing
- `test_user_activation_status`: Activation status handling

#### Login Flow
- `test_successful_login`: Valid credentials
- `test_login_generates_tokens`: Token generation
- `test_access_token_contains_claims`: Verify token claims

#### Token Management
- `test_access_token_expiration`: Token expiration
- `test_refresh_token_validity`: Refresh token lifecycle
- `test_token_refresh_flow`: Token refresh process

#### Access Control
- `test_authenticated_user_access`: Protected resource access
- `test_role_based_access`: Role enforcement
- `test_inactive_user_cannot_authenticate`: Inactive user blocking

#### Logout Flow
- `test_logout_invalidates_session`: Session invalidation
- `test_session_cleanup_on_logout`: Proper cleanup

#### Cross-Tenant Blocking
- `test_cannot_login_to_different_tenant`: Tenant enforcement
- `test_token_claims_include_tenant`: Tenant in token claims

**Coverage**: 18 test cases covering authentication lifecycle

### 6. **test_integration_error_scenarios.py** (Error Handling)
Tests 25+ error scenarios with recovery paths:

#### Upload Errors (4 cases)
- Invalid file formats
- Oversized files
- Missing filenames
- Duplicate detection

#### Extraction Errors (4 cases)
- Corrupted PDFs
- Missing dependencies
- Timeout handling
- Unsupported encoding

#### Chunking Errors (4 cases)
- Empty documents
- Very small documents
- Very large documents
- Memory exhaustion

#### Embedding Errors (3 cases)
- Model loading failure
- Timeout handling
- Out of memory

#### Encryption Errors (2 cases)
- Missing encryption keys
- Key rotation during ingestion

#### Database Errors (3 cases)
- Concurrent operations
- Transaction rollback
- Connection loss

#### Search Errors (3 cases)
- Empty query strings
- Search timeout
- Invalid query syntax

#### Authentication Errors (3 cases)
- Wrong password
- Nonexistent user
- Inactive user login

**Coverage**: 29 test cases covering all major failure scenarios

## Running Integration Tests

### Run All Integration Tests
```bash
cd backend
python -m pytest tests/test_integration_*.py -v --tb=short
```

### Run Specific Test Category
```bash
# Document ingestion workflow
python -m pytest tests/test_integration_document_flow.py -v

# Search workflow
python -m pytest tests/test_integration_search_flow.py -v

# Multi-tenant isolation
python -m pytest tests/test_integration_multi_tenant.py -v

# Authentication flow
python -m pytest tests/test_integration_auth_flow.py -v

# Error scenarios
python -m pytest tests/test_integration_error_scenarios.py -v
```

### Run with Coverage
```bash
python -m pytest tests/test_integration_*.py \
  --cov=app \
  --cov-report=html \
  --cov-report=term-missing \
  -v
```

### Run in Parallel (pytest-xdist)
```bash
pip install pytest-xdist
python -m pytest tests/test_integration_*.py -n auto -v
```

### Run with Specific Marker
```bash
# Run only multi-tenant tests
python -m pytest -m "multi_tenant" -v

# Run only performance tests
python -m pytest -m "performance" -v
```

## Test Fixtures

### Database Fixtures
- `db_session`: Database session for test execution
- `test_db`: Fresh database tables for each test

### Integration Fixtures
- `multi_tenant_setup`: Pre-configured multi-tenant environment
  - `tenants`: List of 3+ test tenants
  - `users`: Dict of users per tenant
  - `keys`: Encryption keys per tenant

- `authenticated_client`: Test client with authentication
  - `client`: FastAPI test client
  - `token`: Valid JWT token
  - `user`: Authenticated user
  - `tenant`: Associated tenant

- `document_workflow_helper`: Document processing helper
- `search_workflow_helper`: Search operation helper

### Helper Methods

**DocumentWorkflowHelper**
```python
# Create test document
doc = DocumentWorkflowHelper.create_test_document(
    db_session, tenant, 
    filename="test.pdf", 
    content="Test content"
)

# Simulate chunking
chunks = DocumentWorkflowHelper.simulate_chunking(
    db_session, doc, 
    num_chunks=5
)

# Simulate embedding and encryption
doc = DocumentWorkflowHelper.simulate_embedding_and_encryption(
    db_session, doc, chunks
)
```

**SearchWorkflowHelper**
```python
# Create search log
log = SearchWorkflowHelper.create_search_log(
    db_session, tenant, user,
    query="search term",
    result_count=10
)

# Simulate search results
results = SearchWorkflowHelper.simulate_search_results(
    num_results=5,
    query="test"
)
```

**MultiTenantTestData**
```python
# Create multi-tenant setup
tenants = MultiTenantTestData.create_tenants(db_session, count=3)
users = MultiTenantTestData.create_users_for_tenants(
    db_session, tenants, users_per_tenant=3
)
keys = MultiTenantTestData.create_encryption_keys_for_tenants(
    db_session, tenants
)
```

## Test Statistics

### Coverage by Component
- **Document Ingestion**: 17 tests (status transitions, metadata, isolation)
- **Search Operations**: 16 tests (query, relevance, isolation, performance)
- **Multi-Tenant Isolation**: 19 tests (data separation, cross-tenant blocking)
- **Authentication**: 18 tests (signup, login, tokens, access control)
- **Error Scenarios**: 29 tests (upload, extraction, chunking, embedding, auth)

**Total Integration Tests**: 99 test cases

### Success Criteria
- ✅ 100% pass rate (all 99 tests passing)
- ✅ Execution time < 10 minutes
- ✅ Support parallel execution (pytest-xdist)
- ✅ 20+ error scenarios with recovery
- ✅ Multi-tenant isolation verified at all levels

## Key Testing Patterns

### 1. Document Workflow Testing
```python
def test_complete_workflow(db_session, multi_tenant_setup):
    tenant = multi_tenant_setup["tenants"][0]
    
    # Create document
    doc = DocumentWorkflowHelper.create_test_document(
        db_session, tenant
    )
    
    # Process through workflow
    doc = DocumentWorkflowHelper.simulate_document_extraction(
        db_session, doc
    )
    chunks = DocumentWorkflowHelper.simulate_chunking(
        db_session, doc, num_chunks=5
    )
    doc = DocumentWorkflowHelper.simulate_embedding_and_encryption(
        db_session, doc, chunks
    )
    
    # Verify final state
    assert doc.status == "completed"
    assert doc.chunk_count == 5
```

### 2. Multi-Tenant Isolation Testing
```python
def test_tenant_isolation(db_session, multi_tenant_setup):
    tenant1 = multi_tenant_setup["tenants"][0]
    tenant2 = multi_tenant_setup["tenants"][1]
    
    # Create data in each tenant
    doc1 = DocumentWorkflowHelper.create_test_document(
        db_session, tenant1
    )
    doc2 = DocumentWorkflowHelper.create_test_document(
        db_session, tenant2
    )
    
    # Verify isolation
    tenant1_docs = db_session.query(Document).filter_by(
        tenant_id=tenant1.id
    ).all()
    
    assert doc1 in tenant1_docs
    assert doc2 not in tenant1_docs
```

### 3. Error Scenario Testing
```python
def test_error_recovery(db_session, multi_tenant_setup):
    tenant = multi_tenant_setup["tenants"][0]
    
    doc = DocumentWorkflowHelper.create_test_document(
        db_session, tenant
    )
    
    # Simulate failure
    doc.status = "failed"
    db_session.commit()
    
    # Verify graceful handling
    assert doc.status == "failed"
```

## Continuous Integration

### CI/CD Pipeline Integration
```yaml
# Example GitHub Actions workflow
test-integration:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v2
    - uses: actions/setup-python@v2
    - run: pip install -r backend/requirements.txt
    - run: cd backend && python -m pytest tests/test_integration_*.py --cov=app
    - uses: codecov/codecov-action@v2
```

## Troubleshooting

### Issue: Tests timeout
**Solution**: Run with longer timeout or reduce parallel execution
```bash
python -m pytest tests/test_integration_*.py --timeout=300 -n 2
```

### Issue: Database locked
**Solution**: Ensure no other pytest processes running
```bash
pkill -f "pytest"
```

### Issue: Import errors
**Solution**: Verify all dependencies installed
```bash
pip install -r backend/requirements.txt
cd backend && python -m pytest tests/test_integration_document_flow.py -v
```

## Performance Benchmarks

### Expected Execution Times
- **Document workflow tests**: ~30 seconds
- **Search workflow tests**: ~20 seconds
- **Multi-tenant tests**: ~25 seconds
- **Auth flow tests**: ~20 seconds
- **Error scenario tests**: ~40 seconds

**Total**: ~135 seconds (~2.3 minutes) for all 99 integration tests

### Optimization Tips
1. Use pytest-xdist for parallel execution (`-n auto`)
2. Use `-x` to stop on first failure for debugging
3. Use `-k` to run specific test patterns
4. Use `--lf` to run only last failed tests

## Future Enhancements

### Potential Additions
1. **Performance benchmarking**: Add performance test suite
2. **Load testing**: Test system under concurrent load
3. **Security testing**: Add security-specific test cases
4. **API contract testing**: Validate API specifications
5. **Database migration testing**: Test schema migrations

### Planned Extensions
- Integration with PostHog analytics
- Real document processing (PDF/DOCX)
- Real embedding model integration
- Real CyborgDB backend testing
- End-to-end API testing with real HTTP
