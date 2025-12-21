"""
Role-based access control (RBAC) system.
Defines roles, permissions, and access control decorators.
"""

from enum import Enum
from typing import List, Callable, Any
from functools import wraps
from fastapi import HTTPException, status, Depends

from app.api.deps import get_current_user
from app.models.database import User


class UserRole(str, Enum):
    """
    User roles with hierarchical permissions.
    
    - ADMIN: Full access to tenant data, manage users, view analytics
    - USER: Upload documents, search, view own uploads
    - VIEWER: Search only, no upload capability
    """
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class Permission(str, Enum):
    """
    Granular permissions for different operations.
    """
    # User management
    MANAGE_USERS = "manage_users"
    VIEW_USERS = "view_users"
    
    # Document operations
    UPLOAD_DOCUMENTS = "upload_documents"
    VIEW_DOCUMENTS = "view_documents"
    DELETE_DOCUMENTS = "delete_documents"
    
    # Search operations
    SEARCH_DOCUMENTS = "search_documents"
    
    # Analytics
    VIEW_ANALYTICS = "view_analytics"
    
    # Tenant settings
    MANAGE_TENANT = "manage_tenant"


# Role to permissions mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        Permission.MANAGE_USERS,
        Permission.VIEW_USERS,
        Permission.UPLOAD_DOCUMENTS,
        Permission.VIEW_DOCUMENTS,
        Permission.DELETE_DOCUMENTS,
        Permission.SEARCH_DOCUMENTS,
        Permission.VIEW_ANALYTICS,
        Permission.MANAGE_TENANT,
    ],
    UserRole.USER: [
        Permission.UPLOAD_DOCUMENTS,
        Permission.VIEW_DOCUMENTS,
        Permission.DELETE_DOCUMENTS,
        Permission.SEARCH_DOCUMENTS,
    ],
    UserRole.VIEWER: [
        Permission.VIEW_DOCUMENTS,
        Permission.SEARCH_DOCUMENTS,
    ],
}


def has_permission(user_role: str, permission: Permission) -> bool:
    """
    Check if a role has a specific permission.
    
    Args:
        user_role: The user's role
        permission: The permission to check
        
    Returns:
        True if role has permission, False otherwise
    """
    try:
        role = UserRole(user_role)
        return permission in ROLE_PERMISSIONS.get(role, [])
    except ValueError:
        return False


def require_role(*allowed_roles: UserRole):
    """
    Decorator to restrict endpoint access to specific roles.
    
    Args:
        *allowed_roles: One or more roles that are allowed to access the endpoint
        
    Example:
        ```python
        @router.post("/users")
        @require_role(UserRole.ADMIN)
        async def create_user(...):
            pass
        ```
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Get current user from kwargs (injected by dependency)
            current_user = kwargs.get('current_user')
            
            if not current_user:
                # Try to get from Depends if not in kwargs
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authentication dependency not found. Add 'current_user: User = Depends(get_current_user)' to endpoint."
                )
            
            # Check if user's role is in allowed roles
            try:
                user_role = UserRole(current_user.role)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Invalid user role: {current_user.role}"
                )
            
            if user_role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required role(s): {', '.join([r.value for r in allowed_roles])}"
                )
            
            # Role check passed, execute function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_permission(*required_permissions: Permission):
    """
    Decorator to restrict endpoint access based on permissions.
    
    Args:
        *required_permissions: One or more permissions required to access the endpoint
        
    Example:
        ```python
        @router.delete("/documents/{doc_id}")
        @require_permission(Permission.DELETE_DOCUMENTS)
        async def delete_document(...):
            pass
        ```
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Get current user from kwargs
            current_user = kwargs.get('current_user')
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authentication dependency not found"
                )
            
            # Check if user has all required permissions
            user_role = current_user.role
            
            for permission in required_permissions:
                if not has_permission(user_role, permission):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Access denied. Missing permission: {permission.value}"
                    )
            
            # Permission check passed, execute function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def check_role_hierarchy(current_user_role: str, target_user_role: str) -> bool:
    """
    Check if current user can modify a target user based on role hierarchy.
    
    Rules:
    - Admins can modify any role
    - Users cannot modify anyone
    - Viewers cannot modify anyone
    
    Args:
        current_user_role: The role of the user performing the action
        target_user_role: The role of the user being modified
        
    Returns:
        True if modification is allowed, False otherwise
    """
    try:
        current_role = UserRole(current_user_role)
        target_role = UserRole(target_user_role)
    except ValueError:
        return False
    
    # Only admins can modify users
    if current_role != UserRole.ADMIN:
        return False
    
    # Admins can modify any role
    return True


def get_role_description(role: UserRole) -> str:
    """
    Get human-readable description of a role.
    
    Args:
        role: The user role
        
    Returns:
        Description string
    """
    descriptions = {
        UserRole.ADMIN: "Full access to tenant data, manage users, view analytics",
        UserRole.USER: "Upload documents, search, view own uploads",
        UserRole.VIEWER: "Search only, no upload capability",
    }
    return descriptions.get(role, "Unknown role")
