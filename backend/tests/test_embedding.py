"""
Tests for embedding service.
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from app.core.embedding import EmbeddingService, get_embedding_service

@patch("app.core.embedding.SentenceTransformer")
def test_embedding_service_init(mock_cls):
    """Test service initialization and model loading"""
    # Reset singleton
    EmbeddingService._instance = None
    EmbeddingService._model = None
    
    service = get_embedding_service()
    
    mock_cls.assert_called_once()
    assert service._model is not None

@patch("app.core.embedding.SentenceTransformer")
def test_generate_embeddings(mock_cls):
    """Test embedding generation logic"""
    # Reset singleton
    EmbeddingService._instance = None
    EmbeddingService._model = None
    
    # Setup mock model
    mock_model = MagicMock()
    # Mock encode to return a numpy array of shape (N, 384)
    def side_effect(texts, **kwargs):
        return np.random.rand(len(texts), 384)
        
    mock_model.encode.side_effect = side_effect
    mock_model.get_sentence_embedding_dimension.return_value = 384
    
    mock_cls.return_value = mock_model
    
    service = get_embedding_service()
    
    texts = ["Hello world", "Another sentence"]
    embeddings = service.generate_embeddings(texts)
    
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 384
    mock_model.encode.assert_called_with(
        texts, 
        batch_size=32, 
        show_progress_bar=False, 
        convert_to_numpy=True,
        normalize_embeddings=True
    )

@patch("app.core.embedding.SentenceTransformer")
def test_empty_input(mock_cls):
    """Test empty input handling"""
    EmbeddingService._instance = None
    EmbeddingService._model = None
    
    service = get_embedding_service()
    embeddings = service.generate_embeddings([])
    assert embeddings == []
