# Testing Guide for Cipherdocs

Comprehensive testing documentation for the Cipherdocs hackathon project including unit tests, fixtures, coverage targets, and execution instructions.

## Overview

This project implements comprehensive testing for Phase 8 (Testing, Benchmarking & Delivery) with:

- **Backend Tests**: Unit tests for all core modules (auth, encryption, chunking, embedding, database)
- **Coverage Target**: >70% overall, >90% for critical paths (auth, encryption, search)
- **Test Execution**: < 5 minutes for full suite
- **Framework**: pytest (Python), Jest + React Testing Library (Frontend - in progress)

---

## Backend Test Structure

### Test Files

#### Core Module Tests

1. **`test_auth_jwt_comprehensive.py`** (650+ lines)
   - Password hashing and verification
   - Access and refresh token creation
   - Token expiration and validation
   - JWT signature verification
   - Dependency injection (get_current_user, get_current_admin_user)
   - Integration tests for authentication flow
   - Edge cases (unicode, special characters, null bytes)
   - **Coverage**: 100% of security.py and deps.py

2. **`test_encryption_comprehensive.py`** (550+ lines)
   - Key generation and randomness
   - Master key encryption/decryption
   - Key fingerprinting (SHA256)
   - Database key creation and storage
   - Key retrieval and caching
   - Key rotation and multiple keys per tenant
   - Encryption/decryption roundtrips
   - Edge cases (empty keys, very long keys, unicode)
   - **Coverage**: 100% of encryption.py module

3. **`test_chunking_comprehensive.py`** (500+ lines)
   - Token counting accuracy
   - Recursive text splitting
   - Chunk object creation and metadata
   - Document chunking with overlap
   - Custom separator handling
   - Very long words and unicode text
   - Mixed whitespace and null bytes
   - Performance testing (large documents, many chunks)
   - **Coverage**: 90%+ of processing/chunking.py

4. **`test_embedding_comprehensive.py`** (450+ lines)
   - Singleton pattern verification
   - Model loading and initialization
   - Embedding generation for single and multiple texts
   - Batch processing with configurable batch sizes
   - Embedding dimension and normalization
   - Similarity calculations
   - Empty, very long, and unicode text handling
   - Large batch processing (10,000+ texts)
   - **Coverage**: 90%+ of core/embedding.py

5. **`test_database_ops.py`** (550+ lines)
   - CRUD operations (Create, Read, Update, Delete)
   - Filtering by multiple criteria
   - Tenant isolation and scoping
   - Pagination and sorting
   - Full-text search
   - Bulk operations
   - Database performance tests
   - **Coverage**: 85%+ of database operations

### Fixture Files

**`test_fixtures.py`** (700+ lines)

Provides reusable test data fixtures organized by category:

#### Tenant Fixtures
- `sample_tenant_id`: Single tenant ID
- `sample_tenant`: Created tenant in DB
- `multiple_tenants`: Array of 5 tenants
- `users_across_tenants`: Users distributed across tenants

#### User Fixtures
- `sample_user`: Regular user
- `admin_user`: Admin role user
- `viewer_user`: Viewer (read-only) user
- `multiple_users`: 10 users for same tenant
- `user_with_role`: Parametrized fixture for all roles
- `users_across_tenants`: Users across multiple tenants

#### Document Fixtures
- `sample_document`: Single document
- `multiple_documents`: 20 documents
- `documents_across_users`: Documents from multiple users
- `document_with_file_type`: Parametrized by file type (pdf, docx, txt, pptx)

#### Chunk Fixtures
- `sample_chunks`: 10 chunks for single document
- `chunks_from_multiple_documents`: Chunks across all documents

#### Other Fixtures
- `sample_search_queries`: Search query history
- `sample_audit_logs`: Audit log entries
- `sample_encryption_key`: Encryption key with decrypted version
- `multiple_encryption_keys`: Multiple keys for rotation
- `bulk_test_data`: Large dataset for stress testing
- `seeded_database`: Pre-populated database

#### Utility Functions
- `seed_test_database()`: Populate DB with configurable data

---

## Running Tests

### Prerequisites

```bash
cd backend
pip install -r requirements.txt
```

### Run All Tests

```bash
# Run with coverage report
pytest

# Verbose output
pytest -v

# Show test names only
pytest -q
```

### Run Specific Test Files

```bash
# Auth module tests only
pytest tests/test_auth_jwt_comprehensive.py -v

# Encryption tests
pytest tests/test_encryption_comprehensive.py -v

# All comprehensive tests
pytest tests/test_*_comprehensive.py -v
```

### Run Specific Test Classes

```bash
# Password hashing tests
pytest tests/test_auth_jwt_comprehensive.py::TestPasswordHashing -v

# Key generation tests
pytest tests/test_encryption_comprehensive.py::TestKeyGeneration -v

# CRUD operations
pytest tests/test_database_ops.py::TestCreateOperations -v
```

### Run Specific Tests

```bash
# Single test
pytest tests/test_auth_jwt_comprehensive.py::TestPasswordHashing::test_hash_password_generates_valid_hash -v

# Tests matching pattern
pytest -k "encryption" -v
pytest -k "token" -v
```

### Run with Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html

# Terminal coverage with missing lines
pytest --cov=app --cov-report=term-missing

# Both formats
pytest --cov=app --cov-report=html --cov-report=term-missing

# With branch coverage
pytest --cov=app --cov-branch --cov-report=html
```

### Run Subset of Tests

```bash
# Skip slow tests
pytest -m "not slow"

# Run only fast tests
pytest -m "fast"

# Run integration tests only
pytest -m "integration"
```

### Performance Testing

```bash
# Show slowest 10 tests
pytest --durations=10

# Run specific performance tests
pytest tests/test_*_comprehensive.py::*Performance -v
```

---

## Coverage Targets

### Overall Target
- **Minimum**: 70% code coverage
- **Target**: 80%+ coverage

### Critical Paths (Target: 90%+)
- **Authentication**: Password hashing, token generation, token validation
- **Encryption**: Key generation, encryption/decryption, key management
- **Search**: Query execution, result filtering
- **Tenant Isolation**: Scoping, data filtering by tenant

### Coverage Configuration

Located in `pytest.ini`:
```ini
--cov=app
--cov-report=html:htmlcov
--cov-report=term-missing
--cov-report=xml
--cov-fail-under=70
--cov-branch
```

### Viewing Coverage Reports

After running tests with coverage:

```bash
# HTML report
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
xdg-open htmlcov/index.html  # Linux

# Terminal output shows:
# - Line coverage percentage
# - Missing lines by file
# - Branch coverage statistics
```

---

## Test Organization

### Naming Conventions
- **Test files**: `test_<module>_comprehensive.py`
- **Test classes**: `Test<Functionality>`
- **Test methods**: `test_<specific_case>`

### Class Organization

Tests are organized into logical classes:

```python
# Example from test_auth_jwt_comprehensive.py
class TestPasswordHashing:
    def test_hash_password_generates_valid_hash(self): ...
    def test_verify_password_success(self): ...
    def test_different_passwords_generate_different_hashes(self): ...

class TestJWTTokenCreation:
    def test_create_access_token_basic(self): ...
    def test_create_refresh_token_includes_required_claims(self): ...

class TestJWTTokenVerification:
    def test_verify_valid_access_token(self): ...
    def test_verify_expired_token_returns_none(self): ...
```

---

## Using Fixtures in Tests

### Basic Usage

```python
def test_example(db_session, sample_user, sample_tenant):
    """Test using fixtures"""
    assert sample_user.tenant_id == sample_tenant.id
    assert sample_user.email == "testuser@example.com"
```

### Parametrized Fixtures

```python
def test_with_role(user_with_role):
    """Automatically runs with admin, user, and viewer"""
    assert user_with_role.role in ["admin", "user", "viewer"]
```

### Bulk Data

```python
def test_with_large_dataset(bulk_test_data):
    """Access pre-created test data"""
    tenants = bulk_test_data["tenants"]
    users = bulk_test_data["users"]
    documents = bulk_test_data["documents"]
    assert len(users) >= 50
```

### Seeded Database

```python
def test_with_seeded_data(seeded_database):
    """Use pre-populated database"""
    users = seeded_database.query(User).all()
    assert len(users) > 0
```

---

## Expected Test Results

### Execution Time
- **Full suite**: 2-5 minutes
- **Unit tests only**: < 3 minutes
- **Fast tests (-m "not slow")**: < 1 minute

### Pass Rate
- **Target**: 100% pass rate
- **Current**: All tests should pass
- **Regression**: Failed tests indicate code issues

### Coverage Metrics (Target)
- **Overall**: 70%+
- **Core modules**: 90%+
- **Critical paths**: 95%+
- **HTML report**: Generated in `htmlcov/index.html`

---

## Test Categories

### Unit Tests
- Individual function/method testing
- Isolated from external dependencies
- Use mocks for external services

### Integration Tests
- Test interactions between components
- Use real database (in-memory SQLite)
- Test full workflows

### Parametrized Tests
- Same test logic with different inputs
- Reduce code duplication
- Cover multiple scenarios

### Performance Tests
- Large dataset handling
- Batch processing efficiency
- Query performance

---

## Common Test Patterns

### Testing Database Operations

```python
def test_create_user(db_session, sample_tenant):
    user = User(
        id=uuid.uuid4(),
        tenant_id=sample_tenant.id,
        email="new@example.com",
        ...
    )
    db_session.add(user)
    db_session.commit()
    
    found = db_session.query(User).filter_by(email="new@example.com").first()
    assert found is not None
```

### Testing Async Functions

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

### Testing Exceptions

```python
def test_invalid_token_raises():
    with pytest.raises(HTTPException) as exc_info:
        # Code that should raise
    assert exc_info.value.status_code == 401
```

---

## Troubleshooting

### Tests Fail with "Database is locked"
- Increase SQLite timeout in `conftest.py`
- Use `-n 1` to run single-threaded

### Import Errors
- Ensure `pythonpath = .` in `pytest.ini`
- Install package in development mode: `pip install -e .`

### Fixtures Not Found
- Verify fixture is in `conftest.py` or imported
- Check fixture scope (function, module, session)

### Slow Tests
- Use `pytest --durations=10` to identify slow tests
- Consider marking slow tests with `@pytest.mark.slow`
- Run subset: `pytest -m "not slow"`

---

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.10
      - run: pip install -r backend/requirements.txt
      - run: cd backend && pytest --cov=app --cov-report=xml
      - uses: codecov/codecov-action@v2
```

---

## Best Practices

### Writing Tests
1. ✅ One assertion per test when possible
2. ✅ Descriptive test names (what it tests and expected result)
3. ✅ Use fixtures for common setup
4. ✅ Test both happy path and edge cases
5. ✅ Mock external dependencies
6. ✅ Use parametrized tests for multiple scenarios

### Naming
- ✅ Use snake_case for test functions
- ✅ Use PascalCase for test classes
- ✅ Prefix test items with `test_`
- ✅ Include the scenario and expected result in name

### Organization
- ✅ Group related tests in classes
- ✅ Order tests logically (create, read, update, delete)
- ✅ Keep fixtures in `conftest.py` or `test_fixtures.py`
- ✅ Use markers for categorization (`@pytest.mark.slow`, `@pytest.mark.integration`)

---

## Next Steps

### Phase 8 Completion
1. ✅ Unit tests for auth, encryption, chunking, embedding, database
2. ⏳ Frontend component tests (Jest + React Testing Library)
3. ⏳ Integration tests across modules
4. ⏳ Performance benchmarking
5. ⏳ Load testing

### Coverage Improvement
- Run coverage reports regularly
- Target 90%+ for critical paths
- Document untested code (pragma: no cover)
- Refactor for testability

---

## Quick Reference Commands

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app

# Verbose output
pytest -v

# Specific test file
pytest tests/test_auth_jwt_comprehensive.py

# Specific test class
pytest tests/test_auth_jwt_comprehensive.py::TestPasswordHashing

# Specific test
pytest tests/test_auth_jwt_comprehensive.py::TestPasswordHashing::test_hash_password_generates_valid_hash

# Show slowest tests
pytest --durations=10

# Generate HTML coverage report
pytest --cov=app --cov-report=html

# Run without slow tests
pytest -m "not slow"

# Watch mode (requires pytest-watch)
ptw

# Run in parallel (requires pytest-xdist)
pytest -n auto
```

---

**Last Updated**: December 15, 2025
**Cipherdocs Phase 8**: Testing, Benchmarking & Delivery
