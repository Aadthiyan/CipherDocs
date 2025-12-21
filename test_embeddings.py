"""Test HuggingFace embedding service"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables from backend/.env
load_dotenv('backend/.env')

# Set minimal required env vars for testing (if not in .env)
if not os.getenv('DATABASE_URL'):
    os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost/test'
if not os.getenv('JWT_SECRET'):
    os.environ['JWT_SECRET'] = 'test_jwt_secret_key_for_testing_only'
if not os.getenv('MASTER_ENCRYPTION_KEY'):
    os.environ['MASTER_ENCRYPTION_KEY'] = 'test_master_key_for_testing_only'

sys.path.insert(0, 'backend')

from app.core.embedding import EmbeddingService
from app.core.config import settings

def test_embedding_service():
    print("=" * 60)
    print("Testing HuggingFace Embedding Service")
    print("=" * 60)
    
    # Check API key
    if not settings.HUGGINGFACE_API_KEY:
        print("❌ HUGGINGFACE_API_KEY not set!")
        return
    
    print(f"✅ API Key: {settings.HUGGINGFACE_API_KEY[:20]}...")
    print(f"✅ Model: {settings.EMBEDDING_MODEL_NAME}")
    print()
    
    # Initialize service
    service = EmbeddingService()
    print("✅ Embedding service initialized")
    print()
    
    # Test with sample texts
    test_texts = [
        "This is a test document about machine learning.",
        "Python is a great programming language.",
        "Vector embeddings are useful for semantic search."
    ]
    
    print(f"Generating embeddings for {len(test_texts)} texts...")
    try:
        embeddings = service.generate_embeddings(test_texts)
        
        print(f"✅ Generated {len(embeddings)} embeddings")
        print(f"✅ Dimension: {len(embeddings[0]) if embeddings else 'N/A'}")
        print(f"✅ Expected dimension: {settings.EMBEDDING_DIMENSION}")
        
        if len(embeddings[0]) == settings.EMBEDDING_DIMENSION:
            print("✅ Dimension matches configuration!")
        else:
            print(f"⚠️ Dimension mismatch: got {len(embeddings[0])}, expected {settings.EMBEDDING_DIMENSION}")
        
        print()
        print("Sample embedding (first 10 values):")
        print(embeddings[0][:10])
        print()
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_embedding_service()
