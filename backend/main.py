"""
CyborgDB Backend - FastAPI Application
Production-grade encrypted multi-tenant SaaS platform
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
from contextlib import asynccontextmanager
import logging

# Import core components
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import (
    CyborgDBException,
    cyborgdb_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    database_exception_handler,
    general_exception_handler
)

# Import middleware
from app.middleware.logging import (
    CorrelationIdMiddleware,
    RequestLoggingMiddleware,
    TenantIsolationMiddleware,
    SecurityHeadersMiddleware
)

# Import database
from app.db.database import init_db, close_db

# Import API routers
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.documents import router as documents_router
from app.api.search import router as search_router
from app.api.analytics import router as analytics_router

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    
    Handles startup and shutdown events
    """
    # Startup
    logger.info("=" * 60)
    logger.info("🚀 CyborgDB Backend Starting Up")
    logger.info("=" * 60)
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Version: {settings.APP_VERSION}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    logger.info(f"CORS Origins: {settings.CORS_ORIGINS}")
    
    # Initialize database
    try:
        await init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        if not settings.is_development():
            raise
    
    # Validate critical configuration
    if not settings.CYBORGDB_API_KEY:
        logger.warning("⚠️  CyborgDB API key not configured")
    
    logger.info("✅ Application startup complete")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("=" * 60)
    logger.info("👋 CyborgDB Backend Shutting Down")
    logger.info("=" * 60)
    
    # Close database connections
    await close_db()
    
    logger.info("✅ Shutdown complete")
    logger.info("=" * 60)


# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Encrypted Multi-Tenant SaaS Document Search Platform",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    debug=settings.DEBUG
)

# ============================================================================
# MIDDLEWARE CONFIGURATION
# ============================================================================

# CORS Middleware (must be first)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Correlation-ID", "X-Process-Time"]
)

# Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# Correlation ID Middleware
app.add_middleware(CorrelationIdMiddleware)

# Request Logging Middleware
app.add_middleware(RequestLoggingMiddleware)

# Tenant Isolation Middleware (will be fully implemented in Phase 2)
app.add_middleware(TenantIsolationMiddleware)

# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

app.add_exception_handler(CyborgDBException, cyborgdb_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, database_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# ============================================================================
# API ROUTERS
# ============================================================================

# Include health check router
app.include_router(health_router)

# Include authentication router
app.include_router(auth_router, prefix="/api/v1")

# Include user management router
app.include_router(users_router, prefix="/api/v1")

# Include documents router
app.include_router(documents_router, prefix="/api/v1")

# Include search router
app.include_router(search_router, prefix="/api/v1/search", tags=["Search"])

# Include analytics router
app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["Analytics"])

# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """
    Root endpoint with API information
    
    Returns:
        API information and links
    """
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "health": "/health",
        "description": "Encrypted multi-tenant document search with CyborgDB"
    }


# API version endpoint
@app.get("/api/v1", tags=["System"])
async def api_version():
    """
    API version information
    
    Returns:
        API version and available endpoints
    """
    return {
        "api_version": "v1",
        "status": "active",
        "endpoints": {
            "health": "/health",
            "auth": "/api/v1/auth (Phase 2)",
            "documents": "/api/v1/documents (Phase 3)",
            "search": "/api/v1/search (Phase 6)",
            "users": "/api/v1/users (Phase 2)",
            "analytics": "/api/v1/analytics (Phase 6)"
        }
    }


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.is_development(),
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )
