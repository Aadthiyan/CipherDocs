"""
Unit tests for text extraction and cleaning.
"""

import pytest
import io
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from app.processing.text_extraction import TextExtractor
from app.processing.text_cleaning import TextCleaner

# ============================================================================
# TEXT CLEANING TESTS
# ============================================================================

def test_clean_text_normalization():
    """Test whitespace normalization"""
    input_text = "This   is  a   test.\n\n\nNew paragraph."
    expected = "This is a test.\n\nNew paragraph."
    assert TextCleaner.clean(input_text) == expected

def test_clean_utf8_artifacts():
    """Test cleaning of common UTF-8 artifacts"""
    input_text = "Smart quotes \u201cshould\u201d be normal."
    expected = 'Smart quotes "should" be normal.'
    assert TextCleaner.clean(input_text) == expected

def test_clean_empty():
    assert TextCleaner.clean(None) == ""
    assert TextCleaner.clean("") == ""
    assert TextCleaner.clean("   ") == ""

# ============================================================================
# TEXT EXTRACTION TESTS
# ============================================================================

def test_extract_txt():
    """Test TXT extraction"""
    content = b"Hello world"
    file_stream = io.BytesIO(content)
    
    result = TextExtractor.extract(file_stream, "txt")
    assert result.text == "Hello world"
    assert not result.error

def test_extract_txt_encoding():
    """Test TXT extraction with utf-8"""
    content = "Hello 🌎".encode("utf-8")
    file_stream = io.BytesIO(content)
    
    result = TextExtractor.extract(file_stream, "txt")
    assert result.text == "Hello 🌎"

def test_extract_unsupported():
    """Test unsupported file type"""
    file_stream = io.BytesIO(b"content")
    result = TextExtractor.extract(file_stream, "exe")
    assert result.error
    assert "Unsupported" in result.error

@patch("app.processing.text_extraction.pypdf.PdfReader")
def test_extract_pdf_mock(mock_reader):
    """Test PDF extraction with mock"""
    # Setup mock
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Page 1 content"
    
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.metadata = {"/Title": "Test PDF"}
    
    mock_reader.return_value = mock_pdf
    
    file_stream = io.BytesIO(b"%PDF mock")
    result = TextExtractor.extract(file_stream, "pdf")
    
    assert "Page 1 content" in result.text
    assert result.metadata["Title"] == "Test PDF"
    assert result.page_count == 1

@patch("app.processing.text_extraction.docx.Document")
def test_extract_docx_mock(mock_document):
    """Test DOCX extraction with mock"""
    # Setup mock
    mock_doc = MagicMock()
    
    para1 = MagicMock()
    para1.text = "Paragraph 1"
    
    para2 = MagicMock()
    para2.text = "" # Empty
    
    mock_doc.paragraphs = [para1, para2]
    mock_doc.tables = []
    mock_doc.core_properties = MagicMock(author="Tester", title="Doc Title")
    
    mock_document.return_value = mock_doc
    
    file_stream = io.BytesIO(b"PK mock")
    result = TextExtractor.extract(file_stream, "docx")
    
    assert "Paragraph 1" in result.text
    assert result.metadata["author"] == "Tester"

# ============================================================================
# INTEGRATION TESTING (MOCKED CELERY)
# ============================================================================
# We verify that uploading triggers the task

from main import app
from app.core import security
from app.models.database import User, Tenant
from app.api.deps import get_current_user, get_current_tenant_id
import uuid

@patch("app.worker.process_document_task.delay")
def test_upload_triggers_processing(mock_delay):
    """Test that upload endpoint triggers celery task"""
    
    # Setup FastAPI TestClient with overrides
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    
    mock_user = MagicMock(spec=User)
    mock_user.id = user_id
    mock_user.role = "user"
    mock_user.tenant_id = tenant_id
    mock_user.is_active = True
    
    # Basic DB mock
    mock_db = MagicMock()
    
    # We'll use the real app but override dependencies
    app.dependency_overrides[get_current_user] = lambda: mock_user
    # Fix the context issue from previous task
    from app.core.tenant_context import set_tenant_context
    def mock_get_tenant_id():
        set_tenant_context(str(tenant_id), str(user_id))
        return str(tenant_id)
        
    app.dependency_overrides[get_current_tenant_id] = mock_get_tenant_id
    
    # We also need to mock storage to avoid file IO errors
    with patch("app.api.documents.get_storage_backend") as mock_storage_factory:
        mock_storage = MagicMock()
        mock_storage.save_file.return_value = "saved/path.pdf" # Async mock needs await? 
        # save_file is async def in the abstract and implementation
        # unittest.mock.AsyncMock is better for async methods if python 3.8+
        
        async def async_save(*args, **kwargs):
            return "saved/path.pdf"
        mock_storage.save_file = async_save
        
        mock_storage_factory.return_value = mock_storage
        
        # We need a real DB session behavior or use the real test DB. 
        # Since this is an integration test of the API, adhering to the previous 
        # test style with an in-memory DB is best.
        
        # Let's import the client fixture from test_document_upload.py logic or recreate it
        # Recreating simplified version here:
        
        from app.db.database import get_db, Base
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        TestingSessionLocal = sessionmaker(bind=engine)
        
        def override_get_db():
            db = TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()
                
        app.dependency_overrides[get_db] = override_get_db
        
        client = TestClient(app)
        
        # Create user/tenant in the test DB
        db = TestingSessionLocal()
        t = Tenant(id=tenant_id, name="Test", plan="basic")
        u = User(id=user_id, email="test@test.com", password_hash="hash", tenant_id=tenant_id, role="user")
        db.add(t)
        db.add(u)
        db.commit()
        db.close()
        
        # Act
        files = {"file": ("test.pdf", b"%PDF content", "application/pdf")}
        token = security.create_access_token(str(user_id), str(tenant_id), "user")
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.post("/api/v1/documents/upload", files=files, headers=headers)
        
        # Assert
        assert response.status_code == 201
        
        # Verify Celery task was called
        mock_delay.assert_called_once()
        args, _ = mock_delay.call_args
        # args[0] should be the document ID
        assert uuid.UUID(args[0]) # Should be valid UUID
