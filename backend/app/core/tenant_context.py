"""
Tenant context management using contextvars for request-scoped tenant isolation.
"""

from contextvars import ContextVar
from typing import Optional
import uuid

# Context variable to store current tenant ID for the request
_current_tenant_id: ContextVar[Optional[str]] = ContextVar('current_tenant_id', default=None)
_current_user_id: ContextVar[Optional[str]] = ContextVar('current_user_id', default=None)


def set_tenant_context(tenant_id: str, user_id: Optional[str] = None) -> None:
    """
    Set the tenant context for the current request.
    
    Args:
        tenant_id: The tenant ID to set
        user_id: Optional user ID to set
    """
    _current_tenant_id.set(tenant_id)
    if user_id:
        _current_user_id.set(user_id)


def get_tenant_context() -> Optional[str]:
    """
    Get the current tenant ID from context.
    
    Returns:
        The current tenant ID or None if not set
    """
    return _current_tenant_id.get()


def get_user_context() -> Optional[str]:
    """
    Get the current user ID from context.
    
    Returns:
        The current user ID or None if not set
    """
    return _current_user_id.get()


def clear_tenant_context() -> None:
    """Clear the tenant context (useful for cleanup)."""
    _current_tenant_id.set(None)
    _current_user_id.set(None)


def require_tenant_context() -> str:
    """
    Get the tenant ID from context, raising an error if not set.
    
    Returns:
        The current tenant ID
        
    Raises:
        RuntimeError: If tenant context is not set
    """
    tenant_id = _current_tenant_id.get()
    if not tenant_id:
        raise RuntimeError("Tenant context not set. Ensure middleware is properly configured.")
    return tenant_id
