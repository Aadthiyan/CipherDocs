"""
Decorators for tenant access control and resource verification.
"""

from functools import wraps
from typing import Callable, Any
from fastapi import HTTPException, status
import uuid

from app.core.tenant_context import get_tenant_context


def require_tenant_access(resource_param: str = "resource"):
    """
    Decorator to verify tenant access to a resource.
    
    Checks that the resource's tenant_id matches the current tenant from JWT.
    Raises 403 Forbidden if there's a mismatch.
    
    Args:
        resource_param: Name of the parameter containing the resource object
        
    Example:
        ```python
        @router.get("/documents/{doc_id}")
        @require_tenant_access("document")
        async def get_document(
            doc_id: uuid.UUID,
            document: Document = Depends(get_document_by_id),
            current_tenant: str = Depends(get_current_tenant_id)
        ):
            return document
        ```
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Get the resource from kwargs
            resource = kwargs.get(resource_param)
            
            if resource is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Resource parameter '{resource_param}' not found"
                )
            
            # Check if resource has tenant_id
            if not hasattr(resource, 'tenant_id'):
                # No tenant scoping for this resource, allow access
                return await func(*args, **kwargs)
            
            # Get current tenant from context
            current_tenant_id = get_tenant_context()
            
            if not current_tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Tenant context not set"
                )
            
            # Verify tenant access
            try:
                current_tenant_uuid = uuid.UUID(current_tenant_id)
                resource_tenant_id = resource.tenant_id
                
                if resource_tenant_id != current_tenant_uuid:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied: resource belongs to different tenant"
                    )
                
            except (ValueError, AttributeError) as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Invalid tenant ID: {str(e)}"
                )
            
            # Access granted, proceed with function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def tenant_scoped(func: Callable) -> Callable:
    """
    Decorator to ensure a function runs with tenant context.
    
    Verifies that tenant context is set before executing the function.
    Useful for background tasks or async operations.
    
    Example:
        ```python
        @tenant_scoped
        async def process_document(doc_id: uuid.UUID):
            # This will fail if tenant context is not set
            tq = get_tenant_scoped_query(db)
            doc = tq.get_by_id(Document, doc_id)
            # Process document...
        ```
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        tenant_id = get_tenant_context()
        
        if not tenant_id:
            raise RuntimeError(
                f"Function '{func.__name__}' requires tenant context but none is set. "
                f"Ensure this function is called within a request context or "
                f"manually set tenant context before calling."
            )
        
        return await func(*args, **kwargs)
    
    return wrapper
