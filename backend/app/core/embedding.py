"""
Embedding service module for generating vector embeddings using HuggingFace Inference API.
Optimized for production deployment with minimal memory footprint.
"""

import logging
import time
from typing import List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Embedding service using HuggingFace Inference API for zero-memory overhead.
    Perfect for serverless and low-memory deployments.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Initialize HuggingFace InferenceClient
        try:
            from huggingface_hub import InferenceClient
            self.client = InferenceClient(api_key=settings.HUGGINGFACE_API_KEY)
        except ImportError:
            raise ImportError("huggingface_hub is required. Install with: pip install huggingface_hub")
        
        self.model_name = settings.EMBEDDING_MODEL_NAME
        self.api_key = settings.HUGGINGFACE_API_KEY
        
        if not self.api_key:
            logger.warning("HUGGINGFACE_API_KEY not set - embeddings may fail")
        else:
            logger.info(f"HuggingFace Inference API configured with model: {self.model_name}")

    def generate_embeddings(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings using HuggingFace Inference API.
        
        Args:
            texts: List of strings to embed
            batch_size: Batch size for API requests
            
        Returns:
            List of embedding vectors (lists of floats)
        """
        if not texts:
            return []
        
        if not self.api_key:
            raise ValueError("HUGGINGFACE_API_KEY is required for embedding generation")
            
        try:
            start_time = time.time()
            
            # Use InferenceClient for feature extraction (embeddings)
            logger.info(f"Generating embeddings for {len(texts)} texts using HuggingFace API")
            embeddings = self.client.feature_extraction(
                texts,
                model=self.model_name
            )
            
            # Convert response to list of lists
            import numpy as np
            if isinstance(embeddings, np.ndarray):
                # numpy array returned, convert to list
                if len(embeddings.shape) == 1:
                    # Single embedding, reshape to 2D
                    embeddings = [embeddings.tolist()]
                else:
                    # Multiple embeddings
                    embeddings = embeddings.tolist()
            elif isinstance(embeddings, list):
                if len(embeddings) > 0 and not isinstance(embeddings[0], list):
                    # Single embedding returned as list, wrap in list
                    embeddings = [embeddings]
            else:
                raise ValueError(f"Unexpected API response format: {type(embeddings)}")
            
            duration = time.time() - start_time
            throughput = len(texts) / duration if duration > 0 else 0
            
            logger.info(
                f"Generated {len(embeddings)} embeddings in {duration:.3f}s "
                f"(Throughput: {throughput:.1f} texts/s) using HuggingFace API"
            )
            
            return embeddings
                
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise e

    @property
    def vector_dimension(self) -> int:
        """Return the dimension of the embeddings"""
        # all-MiniLM-L6-v2 produces 384 dimensional embeddings
        return settings.EMBEDDING_DIMENSION

# Global access
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()

