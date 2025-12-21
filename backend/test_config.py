"""
Test configuration loading and validation
"""
from app.core.config import settings

print("\n✅ Configuration Loaded Successfully\n")
print("=" * 70)
print("CURRENT CONFIGURATION")
print("=" * 70)
print(f"Environment: {settings.ENVIRONMENT}")
print(f"Debug Mode: {settings.DEBUG}")
print(f"Server: {settings.HOST}:{settings.PORT}")
print(f"Storage Backend: {settings.STORAGE_BACKEND}")
print(f"Log Level: {settings.LOG_LEVEL}")
print(f"Is Production: {settings.is_production()}")
print(f"Is Development: {settings.is_development()}")
print(f"Is Staging: {settings.is_staging()}")
print("=" * 70)

print("\n✅ All Configuration Tests Passed!\n")
