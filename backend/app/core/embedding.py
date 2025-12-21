"""
Embedding service module for generating vector embeddings using sentence-transformers locally.
"""

import logging
import time
from typing import List, Optional
import os
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    # Fallback to HuggingFace API if sentence-transformers not available
    from huggingface_hub import InferenceClient

from app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Embedding service that uses local sentence-transformers model for fast, reliable embeddings.
    Falls back to HuggingFace API if local model is not available.
    """
    _instance = None
    _model = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Initialize only if model/client not created
        if self._model is None and self._client is None:
            self._initialize_model()

    def _initialize_model(self):
        """Initialize sentence-transformers model or HuggingFace API client"""
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                logger.info(f"Loading local sentence-transformers model: {settings.EMBEDDING_MODEL_NAME}")
                self._model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
                logger.info("Local sentence-transformers model loaded successfully")
                return
            except Exception as e:
                logger.error(f"Failed to load local model: {e}")
                logger.info("Falling back to HuggingFace API...")
        
        # Fallback to HuggingFace API
        try:
            api_key = settings.HUGGINGFACE_API_KEY
            if not api_key:
                raise ValueError("HUGGINGFACE_API_KEY environment variable not set")
            
            logger.info("Initializing HuggingFace Inference API client")
            self._client = InferenceClient(api_key=api_key)
            logger.info("HuggingFace Inference API client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize HuggingFace client: {e}")
            raise e

    def generate_embeddings(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using local model or HuggingFace API.
        
        Args:
            texts: List of strings to embed
            batch_size: Batch size for processing
            
        Returns:
            List of embedding vectors (lists of floats)
        """
        if not texts:
            return []
            
        try:
            start_time = time.time()
            
            if self._model is not None:
                # Use local sentence-transformers model
                logger.info(f"Processing {len(texts)} texts with local model")
                embeddings = self._model.encode(texts, batch_size=batch_size)
                
                # Convert to list of lists
                if isinstance(embeddings, np.ndarray):
                    embeddings = embeddings.tolist()
                
                duration = time.time() - start_time
                throughput = len(texts) / duration if duration > 0 else 0
                
                logger.info(
                    f"Generated {len(texts)} embeddings in {duration:.3f}s "
                    f"(Throughput: {throughput:.1f} texts/s) using local model"
                )
                
                return embeddings
                
            elif self._client is not None:
                # Use HuggingFace API as fallback
                return self._generate_embeddings_api(texts, batch_size)
            
            else:
                raise RuntimeError("Neither local model nor API client is available")
                
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise e

    def _generate_embeddings_api(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Generate embeddings using HuggingFace API (fallback method)"""
        model_name = settings.EMBEDDING_MODEL_NAME
        
        # Process in batches to handle API limits
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1} with {len(batch)} texts via API")
            
            try:
                # Use feature_extraction for HuggingFace Inference API
                batch_embeddings = self._client.feature_extraction(
                    text=batch if len(batch) > 1 else batch[0],
                    model=model_name
                )
                
                # Handle response: convert numpy arrays to lists
                if isinstance(batch_embeddings, np.ndarray):
                    embeddings.append(batch_embeddings.tolist())
                elif isinstance(batch_embeddings, list):
                    if batch_embeddings and isinstance(batch_embeddings[0], np.ndarray):
                        embeddings.extend([emb.tolist() for emb in batch_embeddings])
                    elif batch_embeddings and isinstance(batch_embeddings[0], (int, float)):
                        embeddings.append(batch_embeddings)
                    else:
                        embeddings.extend(batch_embeddings)
                else:
                    raise ValueError(f"Unexpected embedding response type: {type(batch_embeddings)}")
                    
            except Exception as e:
                logger.error(f"Error processing batch via API: {e}")
                raise e
        
        return embeddings

    @property
    def vector_dimension(self) -> int:
        """Return the dimension of the embeddings"""
        # all-MiniLM-L6-v2 produces 384 dimensional embeddings
        return settings.EMBEDDING_DIMENSION

# Global access
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()

