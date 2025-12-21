#!/usr/bin/env python3
"""
Test script for Groq LLM integration
Tests Groq API connectivity and answer generation
"""

import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from app.core.config import settings
from app.core.llm import GroqAnswerGenerator, LLMAnswerService


def test_groq_connectivity():
    """Test connection to Groq API"""
    print("\n" + "="*80)
    print("TEST 1: Groq API Connectivity")
    print("="*80)
    
    try:
        generator = GroqAnswerGenerator(settings)
        print("✅ Groq client initialized successfully")
        print(f"   Model: {generator.model}")
        print(f"   Max Tokens: {generator.max_tokens}")
        print(f"   Temperature: {generator.temperature}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize Groq client: {e}")
        return False


def test_answer_generation():
    """Test answer generation from mock chunks"""
    print("\n" + "="*80)
    print("TEST 2: Answer Generation from Chunks")
    print("="*80)
    
    try:
        generator = GroqAnswerGenerator(settings)
        
        # Mock search results
        mock_chunks = [
            {
                "text": "Python is a high-level, interpreted programming language known for its simplicity and readability. It was created by Guido van Rossum in 1991.",
                "source": "python_basics.pdf",
                "similarity_score": 0.95,
                "chunk_id": "chunk_1"
            },
            {
                "text": "Python supports multiple programming paradigms including object-oriented, procedural, and functional programming. It has a large standard library.",
                "source": "python_features.pdf",
                "similarity_score": 0.87,
                "chunk_id": "chunk_2"
            },
            {
                "text": "Python is widely used in data science, machine learning, web development, and automation due to its versatility and rich ecosystem.",
                "source": "python_applications.pdf",
                "similarity_score": 0.82,
                "chunk_id": "chunk_3"
            }
        ]
        
        query = "What is Python and what is it used for?"
        
        print(f"\nQuery: {query}")
        print(f"\nRetrieved {len(mock_chunks)} chunks:")
        for i, chunk in enumerate(mock_chunks, 1):
            print(f"  {i}. {chunk['source']} (score: {chunk['similarity_score']})")
            print(f"     {chunk['text'][:80]}...")
        
        print("\nGenerating answer...")
        result = generator.generate_answer(query, mock_chunks)
        
        if result["success"]:
            print("\n✅ Answer generated successfully!")
            print(f"\n{'Answer:':20}")
            print("-" * 80)
            print(result["answer"])
            print("-" * 80)
            print(f"\nTokens used: {result['tokens_used']}")
            print(f"Confidence: {result['confidence']}")
            print(f"Sources used:")
            for source in result['sources']:
                print(f"  - {source['source']} (Relevance: {source['relevance']:.2f})")
            return True
        else:
            print(f"❌ Failed to generate answer: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error during answer generation: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_llm_service():
    """Test LLM service wrapper"""
    print("\n" + "="*80)
    print("TEST 3: LLM Service Wrapper")
    print("="*80)
    
    try:
        service = LLMAnswerService(settings)
        
        print(f"LLM Service enabled: {service.enabled}")
        
        if not service.enabled:
            print("⚠️  LLM answer generation is disabled")
            return True
        
        # Mock search results in service format
        mock_results = [
            {
                "text": "FastAPI is a modern, fast web framework for building APIs with Python.",
                "metadata": {"source": "fastapi_intro.pdf"},
                "similarity_score": 0.93,
                "id": "chunk_1"
            },
            {
                "text": "FastAPI is built on top of Starlette and uses async/await for performance.",
                "metadata": {"source": "fastapi_features.pdf"},
                "similarity_score": 0.85,
                "id": "chunk_2"
            }
        ]
        
        query = "What is FastAPI?"
        
        print(f"\nQuery: {query}")
        print(f"Search results: {len(mock_results)}")
        
        result = service.generate_answer_from_search(
            query=query,
            search_results=mock_results,
            tenant_id="test_tenant"
        )
        
        if result.get("success"):
            print("\n✅ Service generated answer successfully!")
            print(f"\nAnswer: {result['answer'][:200]}...")
            return True
        else:
            print(f"❌ Service failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing LLM service: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_configuration():
    """Print current Groq configuration"""
    print("\n" + "="*80)
    print("GROQ CONFIGURATION")
    print("="*80)
    
    print(f"GROQ_API_KEY: {'***' + settings.GROQ_API_KEY[-10:] if settings.GROQ_API_KEY else 'NOT SET'}")
    print(f"GROQ_MODEL: {settings.GROQ_MODEL}")
    print(f"LLM_ANSWER_GENERATION_ENABLED: {settings.LLM_ANSWER_GENERATION_ENABLED}")
    print(f"LLM_MAX_TOKENS: {settings.LLM_MAX_TOKENS}")
    print(f"LLM_TEMPERATURE: {settings.LLM_TEMPERATURE}")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("GROQ LLM INTEGRATION TEST SUITE")
    print("="*80)
    
    # Print configuration
    print_configuration()
    
    # Check if API key is set
    if not settings.GROQ_API_KEY:
        print("\n❌ ERROR: GROQ_API_KEY is not set in .env file")
        print("   Please add your API key:")
        print("   GROQ_API_KEY=gsk_YOUR_API_KEY_HERE")
        sys.exit(1)
    
    # Run tests
    tests = [
        ("API Connectivity", test_groq_connectivity),
        ("Answer Generation", test_answer_generation),
        ("LLM Service", test_llm_service)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ Unexpected error in {test_name}: {e}")
            results[test_name] = False
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:30} {status}")
    
    all_passed = all(results.values())
    print("="*80)
    
    if all_passed:
        print("\n✅ All tests passed! Groq LLM integration is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please review the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
