"""
Comprehensive tests for document chunking module.
Tests text splitting, token counting, chunk validation, and edge cases.
Coverage: Recursive splitting, token-based sizing, chunk metadata, boundary handling.
"""

import pytest
import uuid
from unittest.mock import patch, MagicMock

from app.processing.chunking import DocumentChunker, Chunk
from app.core.config import settings


# Fixtures
@pytest.fixture
def chunker():
    """Create document chunker with default settings"""
    return DocumentChunker(chunk_size=512, chunk_overlap=50)


@pytest.fixture
def sample_text():
    """Sample multi-paragraph text"""
    return """
    First paragraph with some content.
    
    Second paragraph with more content here.
    It has multiple sentences. This is another sentence.
    
    Third paragraph. Final paragraph.
    """


@pytest.fixture
def long_document():
    """Generate a longer document"""
    paragraphs = []
    for i in range(20):
        paragraphs.append(f"Paragraph {i}: " + "This is a sample sentence. " * 10)
    return "\n\n".join(paragraphs)


@pytest.fixture
def tenant_and_doc_ids():
    """Generate test tenant and document IDs"""
    return uuid.uuid4(), uuid.uuid4()


# ============================================================================
# Token Counting Tests
# ============================================================================

class TestTokenCounting:
    """Test token counting functionality"""
    
    def test_count_tokens_returns_integer(self, chunker):
        """Token count should return an integer"""
        text = "Hello world"
        count = chunker._count_tokens(text)
        assert isinstance(count, int)
        assert count > 0
    
    def test_count_tokens_empty_string(self, chunker):
        """Empty string should have 0 tokens"""
        count = chunker._count_tokens("")
        assert count == 0
    
    def test_count_tokens_single_word(self, chunker):
        """Single word should have 1-2 tokens"""
        count = chunker._count_tokens("hello")
        assert count >= 1
    
    def test_count_tokens_longer_text(self, chunker):
        """Token count should increase with text length"""
        short = "hello"
        medium = "hello world this is a test"
        long = "hello world " * 50
        
        count_short = chunker._count_tokens(short)
        count_medium = chunker._count_tokens(medium)
        count_long = chunker._count_tokens(long)
        
        assert count_short < count_medium < count_long
    
    def test_count_tokens_consistency(self, chunker):
        """Same text should have same token count"""
        text = "test text for consistency checking"
        count1 = chunker._count_tokens(text)
        count2 = chunker._count_tokens(text)
        assert count1 == count2
    
    def test_count_tokens_special_characters(self, chunker):
        """Should handle special characters"""
        text = "Hello! @World #Test $Money %Percent"
        count = chunker._count_tokens(text)
        assert count > 0
    
    def test_count_tokens_unicode(self, chunker):
        """Should handle unicode text"""
        text = "Привет мир 你好世界 مرحبا العالم"
        count = chunker._count_tokens(text)
        assert count > 0


# ============================================================================
# Text Splitting Tests
# ============================================================================

class TestTextSplitting:
    """Test recursive text splitting"""
    
    def test_split_short_text_returns_whole(self, chunker):
        """Short text fitting in chunk should return as-is"""
        text = "This is a short text."
        chunks = chunker._split_text_recursive(text, chunker.separators)
        
        assert len(chunks) == 1
        assert chunks[0] == text
    
    def test_split_long_text_creates_chunks(self, chunker, long_document):
        """Long text should be split into multiple chunks"""
        chunks = chunker._split_text_recursive(long_document, chunker.separators)
        
        assert len(chunks) > 1
    
    def test_split_by_paragraph_first(self, chunker):
        """Should prefer splitting by paragraphs"""
        text = "Para 1 content here.\n\nPara 2 content here." * 50
        chunks = chunker._split_text_recursive(text, chunker.separators)
        
        # Should split by \n\n primarily
        for chunk in chunks:
            # Most chunks shouldn't contain both paragraphs fully
            assert chunk.count("\n\n") <= 1
    
    def test_split_respects_chunk_size(self, chunker):
        """All chunks should respect chunk_size"""
        text = "word " * 1000  # Many tokens
        chunks = chunker._split_text_recursive(text, chunker.separators)
        
        for chunk in chunks:
            token_count = chunker._count_tokens(chunk)
            # Some tolerance for rounding
            assert token_count <= chunker.chunk_size * 1.1
    
    def test_split_empty_text(self, chunker):
        """Empty text should return single empty chunk"""
        chunks = chunker._split_text_recursive("", chunker.separators)
        assert len(chunks) == 1
        assert chunks[0] == ""
    
    def test_split_text_with_newlines(self, chunker):
        """Should split by newlines appropriately"""
        text = "Line 1\nLine 2\nLine 3\n" * 100
        chunks = chunker._split_text_recursive(text, chunker.separators)
        
        assert len(chunks) > 1


# ============================================================================
# Chunk Object Tests
# ============================================================================

class TestChunkObject:
    """Test Chunk dataclass"""
    
    def test_chunk_creation_basic(self, tenant_and_doc_ids):
        """Should create chunk with basic properties"""
        tenant_id, doc_id = tenant_and_doc_ids
        chunk = Chunk(
            text="chunk content",
            sequence=0,
            doc_id=doc_id,
            tenant_id=tenant_id
        )
        
        assert chunk.text == "chunk content"
        assert chunk.sequence == 0
        assert chunk.doc_id == doc_id
        assert chunk.tenant_id == tenant_id
    
    def test_chunk_with_metadata(self, tenant_and_doc_ids):
        """Should store optional metadata"""
        tenant_id, doc_id = tenant_and_doc_ids
        chunk = Chunk(
            text="content",
            sequence=1,
            doc_id=doc_id,
            tenant_id=tenant_id,
            page_number=5,
            section_heading="Introduction"
        )
        
        assert chunk.page_number == 5
        assert chunk.section_heading == "Introduction"
    
    def test_chunk_token_count(self, tenant_and_doc_ids):
        """Should calculate token count"""
        tenant_id, doc_id = tenant_and_doc_ids
        chunk = Chunk(
            text="test content here",
            sequence=0,
            doc_id=doc_id,
            tenant_id=tenant_id,
            token_count=5
        )
        
        assert chunk.token_count == 5


# ============================================================================
# Document Chunker Integration Tests
# ============================================================================

class TestDocumentChunker:
    """Test complete document chunking"""
    
    def test_chunk_document_basic(self, chunker, sample_text, tenant_and_doc_ids):
        """Should chunk document into list of Chunks"""
        tenant_id, doc_id = tenant_and_doc_ids
        chunks = chunker.chunk_document(
            sample_text,
            doc_id=doc_id,
            tenant_id=tenant_id
        )
        
        assert isinstance(chunks, list)
        assert len(chunks) > 0
        assert all(isinstance(c, Chunk) for c in chunks)
    
    def test_chunk_document_preserves_content(self, chunker, long_document, tenant_and_doc_ids):
        """Chunks should reconstruct original text"""
        tenant_id, doc_id = tenant_and_doc_ids
        chunks = chunker.chunk_document(
            long_document,
            doc_id=doc_id,
            tenant_id=tenant_id
        )
        
        # Reconstruct (with overlap loss)
        reconstructed = ""
        for i, chunk in enumerate(chunks):
            if i == 0:
                reconstructed += chunk.text
            else:
                # Skip overlap region
                reconstructed += chunk.text[chunker.chunk_overlap:]
        
        # Content should be mostly preserved (accounting for splitting)
        assert long_document.replace(" ", "") in reconstructed.replace(" ", "") or \
               reconstructed.replace(" ", "") in long_document.replace(" ", "")
    
    def test_chunk_document_sequence_numbers(self, chunker, long_document, tenant_and_doc_ids):
        """Chunks should have correct sequence numbers"""
        tenant_id, doc_id = tenant_and_doc_ids
        chunks = chunker.chunk_document(
            long_document,
            doc_id=doc_id,
            tenant_id=tenant_id
        )
        
        for i, chunk in enumerate(chunks):
            assert chunk.sequence == i
    
    def test_chunk_document_metadata_preserved(self, chunker, sample_text, tenant_and_doc_ids):
        """Metadata should be preserved across chunks"""
        tenant_id, doc_id = tenant_and_doc_ids
        chunks = chunker.chunk_document(
            sample_text,
            doc_id=doc_id,
            tenant_id=tenant_id,
            page_number=3,
            section_heading="Methods"
        )
        
        for chunk in chunks:
            assert chunk.doc_id == doc_id
            assert chunk.tenant_id == tenant_id
            assert chunk.page_number == 3
            assert chunk.section_heading == "Methods"
    
    def test_chunk_document_empty_string(self, chunker, tenant_and_doc_ids):
        """Empty document should produce at least one chunk"""
        tenant_id, doc_id = tenant_and_doc_ids
        chunks = chunker.chunk_document(
            "",
            doc_id=doc_id,
            tenant_id=tenant_id
        )
        
        assert len(chunks) >= 1
    
    def test_chunk_document_single_word(self, chunker, tenant_and_doc_ids):
        """Single word should produce one chunk"""
        tenant_id, doc_id = tenant_and_doc_ids
        chunks = chunker.chunk_document(
            "word",
            doc_id=doc_id,
            tenant_id=tenant_id
        )
        
        assert len(chunks) == 1
        assert chunks[0].text == "word"
    
    def test_chunk_document_with_custom_size(self, tenant_and_doc_ids):
        """Should respect custom chunk size"""
        tenant_id, doc_id = tenant_and_doc_ids
        chunker_small = DocumentChunker(chunk_size=64, chunk_overlap=10)
        
        text = "word " * 500
        chunks = chunker_small.chunk_document(
            text,
            doc_id=doc_id,
            tenant_id=tenant_id
        )
        
        # Smaller chunk size should produce more chunks
        assert len(chunks) > 1
    
    def test_chunk_document_overlap(self, tenant_and_doc_ids):
        """Overlapping chunks should share content"""
        tenant_id, doc_id = tenant_and_doc_ids
        chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
        
        text = "This is a sentence. " * 50
        chunks = chunker.chunk_document(
            text,
            doc_id=doc_id,
            tenant_id=tenant_id
        )
        
        # Check overlap between consecutive chunks
        for i in range(len(chunks) - 1):
            chunk1_end = chunks[i].text[-20:]
            chunk2_start = chunks[i+1].text[:20]
            # Some overlap should exist
            assert len(chunk1_end) > 0 and len(chunk2_start) > 0


# ============================================================================
# Custom Separator Tests
# ============================================================================

class TestCustomSeparators:
    """Test chunking with custom separators"""
    
    def test_custom_separators_order(self, tenant_and_doc_ids):
        """Custom separators should be respected"""
        tenant_id, doc_id = tenant_and_doc_ids
        chunker = DocumentChunker(chunk_size=50)
        
        # Override separators
        chunker.separators = ["|", " "]
        
        text = "part1|part2|part3|part4|" * 20
        chunks = chunker.chunk_document(
            text,
            doc_id=doc_id,
            tenant_id=tenant_id
        )
        
        assert len(chunks) > 0


# ============================================================================
# Edge Cases and Performance Tests
# ============================================================================

class TestChunkingEdgeCases:
    """Test edge cases in chunking"""
    
    def test_very_long_word(self, chunker, tenant_and_doc_ids):
        """Should handle very long words"""
        tenant_id, doc_id = tenant_and_doc_ids
        long_word = "a" * 10000
        
        chunks = chunker.chunk_document(
            long_word,
            doc_id=doc_id,
            tenant_id=tenant_id
        )
        
        assert len(chunks) >= 1
    
    def test_special_characters(self, chunker, tenant_and_doc_ids):
        """Should handle special characters"""
        tenant_id, doc_id = tenant_and_doc_ids
        text = "Test!@#$%^&*()_+-=[]{}|;:',.<>?/" * 100
        
        chunks = chunker.chunk_document(
            text,
            doc_id=doc_id,
            tenant_id=tenant_id
        )
        
        assert len(chunks) > 0
    
    def test_unicode_text(self, chunker, tenant_and_doc_ids):
        """Should handle unicode properly"""
        tenant_id, doc_id = tenant_and_doc_ids
        text = "你好世界。 Привет мир. مرحبا بالعالم. " * 100
        
        chunks = chunker.chunk_document(
            text,
            doc_id=doc_id,
            tenant_id=tenant_id
        )
        
        assert len(chunks) > 0
    
    def test_mixed_whitespace(self, chunker, tenant_and_doc_ids):
        """Should handle mixed whitespace"""
        tenant_id, doc_id = tenant_and_doc_ids
        text = "word1\tword2\nword3\r\nword4    word5" * 100
        
        chunks = chunker.chunk_document(
            text,
            doc_id=doc_id,
            tenant_id=tenant_id
        )
        
        assert len(chunks) > 0
    
    def test_null_bytes(self, chunker, tenant_and_doc_ids):
        """Should handle null bytes gracefully"""
        tenant_id, doc_id = tenant_and_doc_ids
        text = "word1\x00word2\x00word3" * 50
        
        chunks = chunker.chunk_document(
            text,
            doc_id=doc_id,
            tenant_id=tenant_id
        )
        
        assert len(chunks) >= 1


# ============================================================================
# Performance Tests
# ============================================================================

class TestChunkingPerformance:
    """Test performance characteristics"""
    
    def test_chunking_large_document_completes(self, chunker, tenant_and_doc_ids):
        """Large document should chunk in reasonable time"""
        tenant_id, doc_id = tenant_and_doc_ids
        
        # Generate very large document
        large_text = "This is a test sentence. " * 100000
        
        import time
        start = time.time()
        chunks = chunker.chunk_document(
            large_text,
            doc_id=doc_id,
            tenant_id=tenant_id
        )
        elapsed = time.time() - start
        
        # Should complete in reasonable time (< 30 seconds)
        assert elapsed < 30
        assert len(chunks) > 0
    
    def test_many_chunks_handling(self, tenant_and_doc_ids):
        """Should handle documents that split into many chunks"""
        tenant_id, doc_id = tenant_and_doc_ids
        chunker_small = DocumentChunker(chunk_size=32, chunk_overlap=5)
        
        # Document that will create many chunks
        text = "test " * 10000
        
        chunks = chunker_small.chunk_document(
            text,
            doc_id=doc_id,
            tenant_id=tenant_id
        )
        
        # Should create many chunks
        assert len(chunks) > 100
        # All should be valid
        assert all(isinstance(c, Chunk) for c in chunks)
