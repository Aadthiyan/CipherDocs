"""
CyborgDB Health Check API
System health and status endpoints
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import logging
import httpx

from app.schemas.common import HealthCheckResponse
from app.db.database import get_db, get_db_info
from app.core.config import settings
from app.core.cyborg import CyborgDBManager

router = APIRouter(tags=["System"])
logger = logging.getLogger(__name__)


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check the health status of the service and its dependencies"
)
async def health_check(db: Session = Depends(get_db)) -> HealthCheckResponse:
    """
    Health check endpoint for monitoring and load balancers
    
    Returns:
        HealthCheckResponse with service status and component checks
    """
    
    # Check database connection
    db_status = "unknown"
    db_info = None
    try:
        # Simple query to test connection - using text() for SQLAlchemy
        db.execute(text("SELECT 1"))
        db_status = "connected"
        db_info = get_db_info()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"
    
    # Check embedding service
    embedding_status = "pending"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.EMBEDDING_SERVICE_URL}/health")
            embedding_status = "reachable" if response.status_code == 200 else "unreachable"
    except Exception as e:
        logger.debug(f"Embedding service health check failed: {e}")
        embedding_status = "unreachable"
    
    # Check CyborgDB
    cyborgdb_status = "pending"
    if settings.CYBORGDB_API_KEY:
        if CyborgDBManager.check_health():
            cyborgdb_status = "connected"
        else:
            cyborgdb_status = "unreachable"
    else:
        cyborgdb_status = "not_configured"
    
    return HealthCheckResponse(
        status="healthy" if db_status == "connected" else "degraded",
        service="cyborgdb-backend",
        version=settings.APP_VERSION,
        timestamp=datetime.utcnow(),
        environment=settings.ENVIRONMENT,
        checks={
            "database": db_status,
            "embedding_service": embedding_status,
            "cyborgdb": cyborgdb_status
        },
        database=db_info
    )


@router.get(
    "/health/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness Check",
    description="Check if the service is ready to accept requests"
)
async def readiness_check(db: Session = Depends(get_db)) -> dict:
    """
    Readiness check for Kubernetes/orchestration
    
    Returns:
        Simple ready status
    """
    try:
        # Check critical dependencies
        db.execute(text("SELECT 1"))
        return {"ready": True}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"ready": False, "error": str(e)}


@router.get(
    "/health/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness Check",
    description="Check if the service is alive"
)
async def liveness_check() -> dict:
    """
    Liveness check for Kubernetes/orchestration
    
    Returns:
        Simple alive status
    """
    return {"alive": True}
