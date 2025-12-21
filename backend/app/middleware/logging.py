"""
CyborgDB Middleware
Request/response logging, correlation ID tracking, and error handling
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

from app.core.logging import set_correlation_id, get_correlation_id

logger = logging.getLogger(__name__)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add correlation ID to each request
    
    Correlation IDs help track requests across services and logs.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add correlation ID to request and response
        
        Args:
            request: Incoming request
            call_next: Next middleware/endpoint
            
        Returns:
            Response with correlation ID header
        """
        # Get correlation ID from header or generate new one
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        
        # Set correlation ID in context for logging
        set_correlation_id(correlation_id)
        
        # Add to request state for access in endpoints
        request.state.correlation_id = correlation_id
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all requests and responses
    
    Logs:
    - Request method, path, query params
    - Response status code
    - Request duration
    - Client IP
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log request and response details
        
        Args:
            request: Incoming request
            call_next: Next middleware/endpoint
            
        Returns:
            Response
        """
        # Start timer
        start_time = time.time()
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path} "
            f"from {client_ip}"
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"status={response.status_code} duration={duration:.3f}s"
            )
            
            # Add duration header
            response.headers["X-Process-Time"] = f"{duration:.3f}"
            
            return response
            
        except Exception as e:
            # Log error
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"error={str(e)} duration={duration:.3f}s",
                exc_info=True
            )
            raise


class TenantIsolationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract and validate tenant context from JWT tokens.
    
    This middleware:
    - Extracts JWT token from Authorization header
    - Validates and decodes the token
    - Extracts tenant_id and user_id from token claims
    - Sets tenant context for the request using contextvars
    - Logs all requests with tenant_id for audit trail
    - Skips authentication for public endpoints (health, docs, auth)
    """
    
    # Public endpoints that don't require authentication
    PUBLIC_PATHS = {
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/signup",
        "/api/v1/auth/login",
    }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Extract tenant ID from JWT token and set context.
        
        Args:
            request: Incoming request
            call_next: Next middleware/endpoint
            
        Returns:
            Response
        """
        from app.core import security
        from app.core.tenant_context import set_tenant_context, clear_tenant_context
        
        # Skip authentication for public endpoints
        if request.url.path in self.PUBLIC_PATHS or request.url.path.startswith("/static"):
            response = await call_next(request)
            return response
        
        # Extract Authorization header
        auth_header = request.headers.get("Authorization")
        
        # DEBUG: Log to file
        try:
            with open("middleware_debug.txt", "a") as f:
                f.write(f"Auth header present: {bool(auth_header)}\n")
        except:
            pass

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
            # Verify and decode token
            payload = security.verify_token(token)
            
            # DEBUG: Log payload
            try:
                with open("middleware_debug.txt", "a") as f:
                    f.write(f"Payload: {payload}\n")
            except:
                pass
            
            if payload:
                tenant_id = payload.get("tenant_id")
                user_id = payload.get("sub")
                
                if tenant_id:
                    # Set tenant context for this request
                    set_tenant_context(tenant_id, user_id)
                    
                    # Add to request state for easy access
                    request.state.tenant_id = tenant_id
                    request.state.user_id = user_id
                    
                    # Log request with tenant context
                    logger.info(
                        f"Tenant request: tenant_id={tenant_id} user_id={user_id} "
                        f"path={request.url.path} method={request.method}"
                    )
        
        try:
            # Process request
            response = await call_next(request)
            return response
        finally:
            # Clean up context after request
            clear_tenant_context()



class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to responses
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add security headers to response
        
        Args:
            request: Incoming request
            call_next: Next middleware/endpoint
            
        Returns:
            Response with security headers
        """
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
