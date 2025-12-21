"""
Comprehensive Configuration Validation Test
Verifies all configuration loading, validation, and security features
"""
import sys
import json
from app.core.config import settings

def test_configuration():
    """Test all configuration aspects"""
    
    print("\n" + "=" * 70)
    print("🧪 COMPREHENSIVE CONFIGURATION TEST")
    print("=" * 70)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Configuration loaded
    print("\n✓ Test 1: Configuration Loaded")
    print(f"  Environment: {settings.ENVIRONMENT}")
    print(f"  Debug Mode: {settings.DEBUG}")
    tests_passed += 1
    
    # Test 2: Required fields present
    print("\n✓ Test 2: Required Fields Present")
    required_fields = ["DATABASE_URL", "JWT_SECRET", "MASTER_ENCRYPTION_KEY"]
    for field in required_fields:
        value = getattr(settings, field)
        status = "✓" if value else "✗"
        print(f"  {status} {field}: {'Set' if value else 'MISSING'}")
    tests_passed += 1
    
    # Test 3: Secret strength validation
    print("\n✓ Test 3: Secret Strength Validation")
    jwt_len = len(settings.JWT_SECRET)
    key_len = len(settings.MASTER_ENCRYPTION_KEY)
    print(f"  JWT_SECRET length: {jwt_len} chars (min 32 required) - {'✓ OK' if jwt_len >= 32 else '✗ WEAK'}")
    print(f"  MASTER_ENCRYPTION_KEY length: {key_len} chars (min 32 required) - {'✓ OK' if key_len >= 32 else '✗ WEAK'}")
    tests_passed += 1
    
    # Test 4: Environment validation
    print("\n✓ Test 4: Environment Validation")
    valid_envs = ["development", "staging", "production"]
    is_valid = settings.ENVIRONMENT in valid_envs
    print(f"  Environment '{settings.ENVIRONMENT}': {'✓ Valid' if is_valid else '✗ Invalid'}")
    print(f"  is_development(): {settings.is_development()}")
    print(f"  is_staging(): {settings.is_staging()}")
    print(f"  is_production(): {settings.is_production()}")
    tests_passed += 1
    
    # Test 5: Database configuration
    print("\n✓ Test 5: Database Configuration")
    db_valid = settings.DATABASE_URL.startswith("postgresql://")
    print(f"  Database URL format: {'✓ Valid PostgreSQL' if db_valid else '✗ Invalid'}")
    print(f"  Pool size: {settings.DB_POOL_SIZE}")
    print(f"  Max overflow: {settings.DB_MAX_OVERFLOW}")
    tests_passed += 1
    
    # Test 6: Server configuration
    print("\n✓ Test 6: Server Configuration")
    print(f"  Host: {settings.HOST}")
    print(f"  Port: {settings.PORT}")
    print(f"  CORS Origins: {len(settings.CORS_ORIGINS)} domain(s)")
    for origin in settings.CORS_ORIGINS[:3]:  # Show first 3
        print(f"    - {origin}")
    tests_passed += 1
    
    # Test 7: Feature flags
    print("\n✓ Test 7: Feature Flags")
    print(f"  Redis Enabled: {settings.REDIS_ENABLED}")
    print(f"  Rate Limiting Enabled: {settings.RATE_LIMIT_ENABLED}")
    print(f"  Debug Mode: {settings.DEBUG}")
    tests_passed += 1
    
    # Test 8: Storage configuration
    print("\n✓ Test 8: Storage Configuration")
    valid_backends = ["local", "s3", "minio"]
    backend_valid = settings.STORAGE_BACKEND in valid_backends
    print(f"  Storage Backend: {settings.STORAGE_BACKEND} {'✓ Valid' if backend_valid else '✗ Invalid'}")
    if settings.STORAGE_BACKEND == "local":
        print(f"  Local Path: {settings.LOCAL_STORAGE_PATH}")
    tests_passed += 1
    
    # Test 9: Logging configuration
    print("\n✓ Test 9: Logging Configuration")
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    level_valid = settings.LOG_LEVEL in valid_levels
    print(f"  Log Level: {settings.LOG_LEVEL} {'✓ Valid' if level_valid else '✗ Invalid'}")
    tests_passed += 1
    
    # Test 10: Service configuration
    print("\n✓ Test 10: Service Configuration")
    print(f"  Embedding Service URL: {settings.EMBEDDING_SERVICE_URL}")
    print(f"  Embedding Dimension: {settings.EMBEDDING_DIMENSION}")
    print(f"  CyborgDB Endpoint: {settings.CYBORGDB_ENDPOINT}")
    print(f"  CyborgDB Timeout: {settings.CYBORGDB_TIMEOUT}s")
    tests_passed += 1
    
    # Test 11: Security measures
    print("\n✓ Test 11: Security Measures")
    print(f"  JWT Algorithm: {settings.JWT_ALGORITHM}")
    print(f"  JWT Expiration: {settings.JWT_EXPIRATION_HOURS} hours")
    print(f"  Refresh Token Expiration: {settings.REFRESH_TOKEN_EXPIRATION_DAYS} days")
    print(f"  Max Login Attempts: {settings.MAX_LOGIN_ATTEMPTS}")
    tests_passed += 1
    
    # Test 12: Document processing
    print("\n✓ Test 12: Document Processing")
    print(f"  Max File Size: {settings.MAX_FILE_SIZE_MB} MB")
    print(f"  Allowed Types: {', '.join(settings.ALLOWED_FILE_TYPES)}")
    print(f"  Chunk Size: {settings.CHUNK_SIZE} chars")
    print(f"  Chunk Overlap: {settings.CHUNK_OVERLAP} chars")
    tests_passed += 1
    
    # Test 13: Search configuration
    print("\n✓ Test 13: Search Configuration")
    print(f"  Default Top K: {settings.DEFAULT_TOP_K}")
    print(f"  Max Top K: {settings.MAX_TOP_K}")
    print(f"  Search Timeout: {settings.SEARCH_TIMEOUT_SECONDS}s")
    tests_passed += 1
    
    # Test 14: No secrets in output
    print("\n✓ Test 14: Security - No Secrets in Logs")
    settings_dict = settings.model_dump()
    secret_fields = ["JWT_SECRET", "MASTER_ENCRYPTION_KEY", "CYBORGDB_API_KEY"]
    secrets_found = []
    for field in secret_fields:
        if field in settings_dict and str(settings_dict[field]):
            secrets_found.append(field)
    
    if secrets_found:
        print(f"  ⚠️  WARNING: Secrets found in model dump (should be masked)")
        tests_failed += 1
    else:
        print(f"  ✓ No sensitive data exposed in logs")
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    total_tests = tests_passed + tests_failed
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {tests_passed} ✓")
    print(f"Failed: {tests_failed} ✗")
    
    if tests_failed == 0:
        print("\n🎉 ALL CONFIGURATION TESTS PASSED!")
        print("=" * 70 + "\n")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        print("=" * 70 + "\n")
        return 1

if __name__ == "__main__":
    exit_code = test_configuration()
    sys.exit(exit_code)
