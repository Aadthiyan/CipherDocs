"""
CyborgDB Backend Configuration
Centralized configuration management using Pydantic Settings

This module handles all environment variable validation and configuration loading.
Secrets are never logged or exposed in error messages.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator, ValidationError
from typing import List, Optional
import secrets
import sys
import logging


# Get logger for configuration errors (before logging is configured)
config_logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    
    All settings are loaded from .env file or environment variables.
    Pydantic validates types and provides defaults.
    """
    
    # Application
    APP_NAME: str = "CyborgDB"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", description="Environment: development, staging, production")
    DEBUG: bool = Field(default=True, description="Debug mode")
    
    # Server
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    
    # Database
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
    DB_POOL_SIZE: int = Field(default=10, description="Database connection pool size")
    DB_MAX_OVERFLOW: int = Field(default=20, description="Max overflow connections")
    DB_POOL_TIMEOUT: int = Field(default=30, description="Pool timeout in seconds")
    DB_ECHO: bool = Field(default=False, description="Echo SQL queries")
    
    # Redis
    REDIS_URL: Optional[str] = Field(default=None, description="Redis connection string")
    REDIS_ENABLED: bool = Field(default=False, description="Enable Redis caching")
    
    # JWT Authentication
    JWT_SECRET: str = Field(..., description="JWT signing secret")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_EXPIRATION_HOURS: int = Field(default=24, description="JWT token expiration in hours")
    REFRESH_TOKEN_EXPIRATION_DAYS: int = Field(default=30, description="Refresh token expiration in days")
    
    # Encryption
    MASTER_ENCRYPTION_KEY: str = Field(..., description="Master encryption key for tenant keys")
    
    # CyborgDB Embedded (integrated directly in FastAPI backend)
    CYBORGDB_API_KEY: Optional[str] = Field(default=None, description="CyborgDB API key (from cyborgdb.co)")
    CYBORGDB_BACKING_STORE: str = Field(
        default="memory",
        description="CyborgDB backing store: 'memory' (fast, in-process) or 'redis' (persistent)"
    )
    
    # Embedding Service
    EMBEDDING_SERVICE_URL: str = Field(default="http://localhost:8001", description="Embedding service URL")
    EMBEDDING_MODEL_NAME: str = Field(default="sentence-transformers/all-mpnet-base-v2", description="HuggingFace model name")
    EMBEDDING_DIMENSION: int = Field(default=768, description="Embedding vector dimension")
    HUGGINGFACE_API_KEY: Optional[str] = Field(default=None, description="HuggingFace API key")
    
    # CORS
    CORS_ORIGINS: str = Field(default="http://localhost:3000", description="Comma-separated CORS origins")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(correlation_id)s - %(message)s",
        description="Log format"
    )
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    MAX_LOGIN_ATTEMPTS: int = Field(default=5, description="Max login attempts")
    RATE_LIMIT_WINDOW_SECONDS: int = Field(default=300, description="Rate limit window in seconds")
    
    # Document Processing
    MAX_FILE_SIZE_MB: int = Field(default=50, description="Max file size in MB")
    ALLOWED_FILE_TYPES: str = Field(default="pdf,docx,txt", description="Comma-separated file types")
    CHUNK_SIZE: int = Field(default=512, description="Document chunk size")
    CHUNK_OVERLAP: int = Field(default=50, description="Chunk overlap size")
    
    # Search
    DEFAULT_TOP_K: int = Field(default=10, description="Default number of search results")
    MAX_TOP_K: int = Field(default=100, description="Maximum number of search results")
    SEARCH_TIMEOUT_SECONDS: int = Field(default=30, description="Search timeout in seconds")
    
    # LLM Configuration (Groq)
    GROQ_API_KEY: Optional[str] = Field(default=None, description="Groq API key")
    GROQ_MODEL: str = Field(default="mixtral-8x7b-32768", description="Groq model to use")
    LLM_ANSWER_GENERATION_ENABLED: bool = Field(default=True, description="Enable LLM answer generation")
    LLM_MAX_TOKENS: int = Field(default=512, description="Max tokens for LLM response (reduced to stay within rate limits)")
    LLM_TEMPERATURE: float = Field(default=0.7, description="Temperature for LLM response generation")
    
    # Storage
    STORAGE_BACKEND: str = Field(default="local", description="Storage backend: local, s3, minio")
    LOCAL_STORAGE_PATH: str = Field(default="./storage/documents", description="Local storage path")
    
    @validator("CORS_ORIGINS")
    def parse_cors_origins(cls, v: str) -> List[str]:
        """Parse comma-separated CORS origins into list"""
        return [origin.strip() for origin in v.split(",")]
    
    @validator("ALLOWED_FILE_TYPES")
    def parse_file_types(cls, v: str) -> List[str]:
        """Parse comma-separated file types into list"""
        return [ft.strip() for ft in v.split(",")]
    
    @validator("JWT_SECRET")
    def validate_jwt_secret(cls, v: str) -> str:
        """Ensure JWT secret is strong enough"""
        if not v or len(v) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters long. Generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\"")
        return v
    
    @validator("MASTER_ENCRYPTION_KEY")
    def validate_master_encryption_key(cls, v: str) -> str:
        """Ensure master encryption key is strong enough"""
        if not v or len(v) < 32:
            raise ValueError("MASTER_ENCRYPTION_KEY must be at least 32 characters long. Generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\"")
        return v
    
    @validator("DATABASE_URL")
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format"""
        if not v or not v.startswith("postgresql://"):
            raise ValueError("DATABASE_URL must be a valid PostgreSQL connection string starting with 'postgresql://'")
        return v
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v: str) -> str:
        """Validate environment value"""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of: {', '.join(allowed)}")
        return v
    
    @validator("STORAGE_BACKEND")
    def validate_storage_backend(cls, v: str) -> str:
        """Validate storage backend"""
        allowed = ["local", "s3", "minio"]
        if v not in allowed:
            raise ValueError(f"STORAGE_BACKEND must be one of: {', '.join(allowed)}")
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of: {', '.join(allowed)}")
        return v.upper()
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"
        
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT == "production"
    
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT == "development"
    
    def is_staging(self) -> bool:
        """Check if running in staging"""
        return self.ENVIRONMENT == "staging"


def load_settings() -> Settings:
    """
    Load and validate settings from environment
    
    Raises:
        ValidationError: If required variables are missing or invalid
        SystemExit: If critical configuration is missing
    
    Returns:
        Settings instance with all validated configuration
    """
    try:
        settings = Settings()
        
        # Log configuration loaded (without secrets)
        config_logger.info("=" * 70)
        config_logger.info("🔧 Configuration Loaded Successfully")
        config_logger.info("=" * 70)
        config_logger.info(f"  Environment: {settings.ENVIRONMENT}")
        config_logger.info(f"  Debug Mode: {settings.DEBUG}")
        config_logger.info(f"  Server: {settings.HOST}:{settings.PORT}")
        config_logger.info(f"  Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'NEON'}")
        config_logger.info(f"  Storage Backend: {settings.STORAGE_BACKEND}")
        config_logger.info(f"  Log Level: {settings.LOG_LEVEL}")
        config_logger.info(f"  CORS Origins: {', '.join(settings.CORS_ORIGINS)}")
        config_logger.info("=" * 70)
        
        return settings
        
    except ValidationError as e:
        config_logger.error("=" * 70)
        config_logger.error("❌ Configuration Validation Failed")
        config_logger.error("=" * 70)
        
        for error in e.errors():
            field = error["loc"][0]
            msg = error["msg"]
            config_logger.error(f"  ❌ {field}: {msg}")
        
        config_logger.error("=" * 70)
        config_logger.error("See .env.example for configuration template")
        config_logger.error("=" * 70)
        
        sys.exit(1)
    
    except Exception as e:
        config_logger.error("=" * 70)
        config_logger.error("❌ Unexpected Configuration Error")
        config_logger.error("=" * 70)
        config_logger.error(f"  Error: {str(e)}")
        config_logger.error("=" * 70)
        sys.exit(1)


# Global settings instance - loaded and validated at startup
settings = load_settings()
