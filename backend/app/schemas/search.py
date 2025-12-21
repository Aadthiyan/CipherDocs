from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=1000, description="Search query text")
    top_k: int = Field(5, ge=1, le=100, description="Number of results to return")

class AdvancedSearchRequest(SearchRequest):
    augment: bool = Field(False, description="Enable context augmentation (sliding window)")
    rerank: bool = Field(False, description="Enable result reranking")

class SearchResultItem(BaseModel):
    id: str = Field(..., description="Chunk ID")
    score: float = Field(..., description="Similarity score")
    text: Optional[str] = Field(None, description="Decrypted chunk text")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")

class SearchResponse(BaseModel):
    results: List[SearchResultItem]
    query_id: str
    latency_ms: float
    total_results: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # LLM Answer Generation (Optional)
    llm_answer: Optional[str] = Field(None, description="Synthesized answer from LLM")
    llm_sources: Optional[List[Dict[str, Any]]] = Field(None, description="Sources used by LLM")
    llm_confidence: Optional[float] = Field(None, description="Confidence score of LLM answer")
    llm_disclaimer: Optional[str] = Field(None, description="Warning if general knowledge might be used")
