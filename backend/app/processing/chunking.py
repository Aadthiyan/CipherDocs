from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
import logging
import uuid

# from langchain.text_splitter import RecursiveCharacterTextSplitter # Removed dependency
from transformers import AutoTokenizer

from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class Chunk:
    """Represents a single text chunk with metadata"""
    text: str
    sequence: int
    doc_id: uuid.UUID
    tenant_id: uuid.UUID
    page_number: Optional[int] = None
    section_heading: Optional[str] = None
    token_count: int = 0

class DocumentChunker:
    """
    Intelligent document chunker.
    
    Implements recursive text splitting with token-based length function.
    Prioritizes splitting by:
    1. Paragraphs (\n\n)
    2. Newlines (\n)
    3. Sentences (. , ? !)
    4. Words ( )
    """
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
        except Exception:
            logger.warning("Could not load specific tokenizer, falling back to approximate token count (char/4)")
            self.tokenizer = None
            
        # Delimiters in order of priority
        self.separators = ["\n\n", "\n", ". ", "? ", "! ", " ", ""]

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if self.tokenizer:
            return len(self.tokenizer.encode(text, add_special_tokens=False))
        else:
            return len(text) // 4

    def _split_text_recursive(self, text: str, separators: List[str]) -> List[str]:
        """
        Recursively split text using separators until chunks fit in chunk_size.
        """
        final_chunks = []
        
        # Determine strict length function
        length = self._count_tokens(text)
        
        if length <= self.chunk_size:
            return [text]
            
        if not separators:
            # If no separators left, we must hard split (not implemented here for simplicity, 
            # usually just take first N chars. For robustness we return as is or truncate).
            return [text] 
            
        separator = separators[0]
        next_separators = separators[1:]
        
        # Split by current separator
        if separator == "":
            splits = list(text) # Split by char
        else:
            splits = text.split(separator)
            
        # Re-assemble splits into chunks that fit
        current_chunk = []
        current_length = 0
        
        for split in splits:
            split_len = self._count_tokens(split)
            
            # If single split is too big, recurse on it
            if split_len > self.chunk_size:
                if current_chunk:
                    # Flush current buffer
                    joined = separator.join(current_chunk)
                    final_chunks.append(joined)
                    current_chunk = []
                    current_length = 0
                
                # Recurse on the large split
                sub_chunks = self._split_text_recursive(split, next_separators)
                final_chunks.extend(sub_chunks)
                continue
            
            # If adding this split exceeds size, flush buffer
            # Note: We add len(separator) roughly to count? Ignored for simplicity
            if current_length + split_len > self.chunk_size:
                joined = separator.join(current_chunk)
                final_chunks.append(joined)
                
                # Start new chunk with overlaps could go here (sliding window)
                # For simple recursive, we usually just flush. 
                # Implementing overlap in recursive is tricky. 
                # LangChain does: merge splits until size limit, then verify overlap constraints.
                
                # Simplified overlap:
                # Keep last few items of current_chunk for next chunk
                # tailored logic needed.
                
                # Reset
                current_chunk = [split]
                current_length = split_len
            else:
                current_chunk.append(split)
                current_length += split_len
                
        if current_chunk:
            joined = separator.join(current_chunk)
            final_chunks.append(joined)
            
        return final_chunks

    def chunk_document(
        self, 
        text: str, 
        doc_id: uuid.UUID, 
        tenant_id: uuid.UUID,
        metadata: Dict[str, Any] = None
    ) -> List[Chunk]:
        """
        Split document text into chunks.
        """
        if not text:
            return []
            
        # Use our custom recursive splitter
        raw_chunks = self._split_text_recursive(text, self.separators)
        
        # TODO: Post-process for overlap if meaningful context lost. 
        # The simple recursive above has no overlap. 
        # Adding simple overlap:
        # We can create a sliding window over the raw chunks if they are small units? 
        # But raw_chunks are already max size.
        
        # Proper implementation of overlap requires accumulating small splits 
        # and maintaining a buffer. 
        # Let's trust the recursive split for now or improve `_split_text_recursive` later.
        
        chunks = []
        for i, chunk_text in enumerate(raw_chunks):
            chunk_text = chunk_text.strip()
            if not chunk_text:
                continue
                
            token_count = self._count_tokens(chunk_text)
            
            if token_count < 10 and len(raw_chunks) > 1:
                continue
                
            chunks.append(Chunk(
                text=chunk_text,
                sequence=i + 1,
                doc_id=doc_id,
                tenant_id=tenant_id,
                token_count=token_count
            ))
            
        return chunks
