"""
Database query helpers for automatic tenant scoping.
Ensures all queries are automatically filtered by tenant_id.
"""

from typing import Type, TypeVar, Optional
from sqlalchemy.orm import Session, Query
from sqlalchemy.ext.declarative import DeclarativeMeta
import uuid

from app.core.tenant_context import get_tenant_context, require_tenant_context
from app.models.database import Base

T = TypeVar('T', bound=Base)


class TenantScopedQuery:
    """
    Helper class for creating tenant-scoped database queries.
    Automatically filters all queries by the current tenant_id from context.
    """
    
    def __init__(self, db: Session):
        """
        Initialize with database session.
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def query(self, model: Type[T]) -> Query:
        """
        Create a query automatically scoped to current tenant.
        
        Args:
            model: SQLAlchemy model class
            
        Returns:
            Query object filtered by tenant_id
            
        Raises:
            RuntimeError: If tenant context is not set
            AttributeError: If model doesn't have tenant_id field
        """
        # Get current tenant ID from context
        tenant_id = require_tenant_context()
        
        # Check if model has tenant_id field
        if not hasattr(model, 'tenant_id'):
            raise AttributeError(
                f"Model {model.__name__} does not have a tenant_id field. "
                f"Cannot apply tenant scoping."
            )
        
        # Create query filtered by tenant_id
        tenant_uuid = uuid.UUID(tenant_id)
        return self.db.query(model).filter(model.tenant_id == tenant_uuid)
    
    def get_by_id(self, model: Type[T], resource_id: uuid.UUID) -> Optional[T]:
        """
        Get a single resource by ID, scoped to current tenant.
        
        Args:
            model: SQLAlchemy model class
            resource_id: The resource ID to fetch
            
        Returns:
            The resource if found and belongs to current tenant, None otherwise
        """
        return self.query(model).filter(model.id == resource_id).first()
    
    def create(self, instance: T) -> T:
        """
        Create a new resource with automatic tenant_id assignment.
        
        Args:
            instance: Model instance to create
            
        Returns:
            Created instance with tenant_id set
            
        Raises:
            RuntimeError: If tenant context is not set
        """
        tenant_id = require_tenant_context()
        
        # Set tenant_id if model has the field
        if hasattr(instance, 'tenant_id'):
            instance.tenant_id = uuid.UUID(tenant_id)
        
        self.db.add(instance)
        self.db.flush()
        return instance
    
    def verify_access(self, instance: T) -> bool:
        """
        Verify that the current tenant has access to a resource.
        
        Args:
            instance: Model instance to check
            
        Returns:
            True if current tenant owns the resource, False otherwise
        """
        if not hasattr(instance, 'tenant_id'):
            return True  # No tenant scoping for this model
        
        tenant_id = get_tenant_context()
        if not tenant_id:
            return False
        
        try:
            tenant_uuid = uuid.UUID(tenant_id)
            return instance.tenant_id == tenant_uuid
        except (ValueError, AttributeError):
            return False


def get_tenant_scoped_query(db: Session) -> TenantScopedQuery:
    """
    Factory function to create a tenant-scoped query helper.
    
    Args:
        db: SQLAlchemy database session
        
    Returns:
        TenantScopedQuery instance
        
    Example:
        ```python
        from app.db.tenant_scoping import get_tenant_scoped_query
        
        def get_documents(db: Session):
            tq = get_tenant_scoped_query(db)
            # Automatically filtered by current tenant
            documents = tq.query(Document).all()
            return documents
        ```
    """
    return TenantScopedQuery(db)
