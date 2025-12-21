"""
Tests for document chunking logic.
"""

import pytest
import uuid
from unittest.mock import MagicMock, patch

from app.processing.chunking import DocumentChunker, Chunk

# Sample text for testing
SAMPLE_TEXT = """
CyborgDB is a high-performance database. 
It supports vector search and encryption.
Multi-tenancy is a core feature.

We divide documents into chunks. 
Chunks are embedded into vectors. 
Vectors are stored in the database.
""" * 10 # Make it long enough to split

@patch("app.processing.chunking.AutoTokenizer")
def test_chunking_logic(mock_tokenizer_cls):
    """Test chunking with mocked tokenizer"""
    # Setup mock tokenizer
    mock_tokenizer = MagicMock()
    # Mock encode to return a list of token IDs of length len(text)/4 (approx)
    # This simulates token counting
    mock_tokenizer.encode.side_effect = lambda text, **kwargs: [1] * (len(text) // 4)
    mock_tokenizer_cls.from_pretrained.return_value = mock_tokenizer
    
    # Initialize chunker
    chunker = DocumentChunker(chunk_size=50, chunk_overlap=10)
    
    doc_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    
    chunks = chunker.chunk_document(SAMPLE_TEXT, doc_id, tenant_id)
    
    # Verify chunks
    assert len(chunks) > 0
    assert isinstance(chunks[0], Chunk)
    assert chunks[0].doc_id == doc_id
    assert chunks[0].tenant_id == tenant_id
    assert chunks[0].sequence == 1
    assert chunks[1].sequence == 2
    
    # Verify text content
    assert len(chunks[0].text) > 0

@patch("app.processing.chunking.AutoTokenizer")
def test_chunking_fallback(mock_tokenizer_cls):
    """Test chunking fallback when tokenizer fails to load"""
    # Simulate failure
    mock_tokenizer_cls.from_pretrained.side_effect = Exception("Download failed")
    
    chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
    
    # Chunker should still work (using fallback char/4)
    assert chunker.tokenizer is None
    
    chunks = chunker.chunk_document(SAMPLE_TEXT, uuid.uuid4(), uuid.uuid4())
    assert len(chunks) > 0

def test_chunking_empty():
    """Test chunking empty text"""
    chunker = DocumentChunker()
    chunks = chunker.chunk_document("", uuid.uuid4(), uuid.uuid4())
    assert len(chunks) == 0

@patch("app.processing.chunking.AutoTokenizer")
def test_chunking_quality_control(mock_tokenizer_cls):
    """Test that very small chunks are rejected"""
    mock_tokenizer = MagicMock()
    mock_tokenizer.encode.side_effect = lambda text, **kwargs: [1] * (len(text) // 4)
    mock_tokenizer_cls.from_pretrained.return_value = mock_tokenizer
    
    chunker = DocumentChunker(chunk_size=100)
    
    # Input with some real text and some tiny noise
    # "Tiny" is 4 chars -> 1 token. Threshold is 10 tokens.
    text = "This is a substantial paragraph that should kept. " * 5 + "\n\nTiny"
    
    chunks = chunker.chunk_document(text, uuid.uuid4(), uuid.uuid4())
    
    # Should contain the big part, might exclude "Tiny" if it's split into its own chunk
    # Recursive splitter might modify this behavior, but let's check
    # If "Tiny" is own chunk, it has 1 token < 10, so rejected.
    
    # Just verify we have chunks and they are "valid"
    assert len(chunks) >= 1
    for chunk in chunks:
        assert chunk.token_count >= 10 or len(chunks) == 1
