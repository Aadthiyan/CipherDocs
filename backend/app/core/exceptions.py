"""
CyborgDB Exception Handlers
Centralized error handling and response formatting
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import logging

from app.core.logging import get_correlation_id

logger = logging.getLogger(__name__)


class CyborgDBException(Exception):
    """Base exception for CyborgDB application"""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(CyborgDBException):
    """Authentication failed"""
    
    def __init__(self, message: str = "Authentication failed", details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class AuthorizationError(CyborgDBException):
    """Authorization failed"""
    
    def __init__(self, message: str = "Access denied", details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


class NotFoundError(CyborgDBException):
    """Resource not found"""
    
    def __init__(self, message: str = "Resource not found", details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )


class ValidationError(CyborgDBException):
    """Validation failed"""
    
    def __init__(self, message: str = "Validation failed", details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class ConflictError(CyborgDBException):
    """Resource conflict"""
    
    def __init__(self, message: str = "Resource conflict", details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )


def create_error_response(
    status_code: int,
    message: str,
    details: dict = None,
    correlation_id: str = None
) -> dict:
    """
    Create standardized error response
    
    Args:
        status_code: HTTP status code
        message: Error message
        details: Additional error details
        correlation_id: Request correlation ID
        
    Returns:
        Error response dictionary
    """
    return {
        "error": True,
        "status_code": status_code,
        "message": message,
        "details": details or {},
        "correlation_id": correlation_id or get_correlation_id(),
        "timestamp": datetime.utcnow().isoformat()
    }


async def cyborgdb_exception_handler(request: Request, exc: CyborgDBException) -> JSONResponse:
    """
    Handle CyborgDB custom exceptions
    
    Args:
        request: Request object
        exc: CyborgDB exception
        
    Returns:
        JSON error response
    """
    logger.error(
        f"CyborgDB exception: {exc.message}",
        extra={"details": exc.details}
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            status_code=exc.status_code,
            message=exc.message,
            details=exc.details,
            correlation_id=get_correlation_id()
        )
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions
    
    Args:
        request: Request object
        exc: HTTP exception
        
    Returns:
        JSON error response
    """
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            status_code=exc.status_code,
            message=exc.detail,
            correlation_id=get_correlation_id()
        )
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle request validation errors
    
    Args:
        request: Request object
        exc: Validation error
        
    Returns:
        JSON error response with validation details
    """
    logger.warning(f"Validation error: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Request validation failed",
            details={"validation_errors": exc.errors()},
            correlation_id=get_correlation_id()
        )
    )


async def database_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Handle database errors
    
    Args:
        request: Request object
        exc: SQLAlchemy error
        
    Returns:
        JSON error response
    """
    logger.error(f"Database error: {str(exc)}", exc_info=True)
    
    # Don't expose internal database errors to clients
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Database error occurred",
            details={"type": "database_error"},
            correlation_id=get_correlation_id()
        )
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle all other exceptions
    
    Args:
        request: Request object
        exc: Exception
        
    Returns:
        JSON error response
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    # Don't expose internal errors to clients in production
    from app.core.config import settings
    
    if settings.is_development():
        details = {
            "type": type(exc).__name__,
            "message": str(exc)
        }
    else:
        details = {"type": "internal_error"}
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An unexpected error occurred",
            details=details,
            correlation_id=get_correlation_id()
        )
    )
