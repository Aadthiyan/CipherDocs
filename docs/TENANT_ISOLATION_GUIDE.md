# Tenant Isolation Quick Reference

## Overview
Complete guide to using the tenant isolation system in CyborgDB.

---

## 1. Dependencies (Use in Endpoints)

### Get Current Tenant ID (Fast)
```python
from app.api.deps import get_current_tenant_id

@router.get("/documents")
async def list_documents(
    tenant_id: str = Depends(get_current_tenant_id)
):
    # tenant_id is extracted from JWT
    # No database query
    pass
```

### Get Current User (With DB Query)
```python
from app.api.deps import get_current_user

@router.get("/profile")
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    # Returns full User object from database
    # Validates user is active
    return current_user
```

### Get Current Tenant (With DB Query)
```python
from app.api.deps import get_current_tenant

@router.get("/tenant/info")
async def get_tenant_info(
    current_tenant: Tenant = Depends(get_current_tenant)
):
    # Returns full Tenant object from database
    # Validates tenant is active
    return current_tenant
```

---

## 2. Tenant-Scoped Database Queries

### Basic Usage
```python
from app.db.tenant_scoping import get_tenant_scoped_query
from app.db.database import get_db

@router.get("/documents")
async def list_documents(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    # Create tenant-scoped query helper
    tq = get_tenant_scoped_query(db)
    
    # Automatically filtered by current tenant
    documents = tq.query(Document).all()
    
    return documents
```

### Get Resource by ID
```python
@router.get("/documents/{doc_id}")
async def get_document(
    doc_id: uuid.UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    tq = get_tenant_scoped_query(db)
    
    # Returns None if not found OR belongs to different tenant
    document = tq.get_by_id(Document, doc_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document
```

### Create Resource
```python
@router.post("/documents")
async def create_document(
    request: DocumentCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    # Create document instance
    document = Document(
        filename=request.filename,
        doc_type=request.doc_type,
        # Don't set tenant_id manually!
    )
    
    tq = get_tenant_scoped_query(db)
    
    # tenant_id automatically assigned
    created_doc = tq.create(document)
    db.commit()
    db.refresh(created_doc)
    
    return created_doc
```

### Complex Queries
```python
@router.get("/documents/search")
async def search_documents(
    query: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    tq = get_tenant_scoped_query(db)
    
    # Build on top of tenant-scoped query
    documents = (
        tq.query(Document)
        .filter(Document.filename.contains(query))
        .filter(Document.status == "completed")
        .order_by(Document.created_at.desc())
        .limit(10)
        .all()
    )
    
    return documents
```

---

## 3. Manual Tenant Verification

### Verify Resource Access
```python
from app.api.deps import verify_tenant_access

@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: uuid.UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    # Get document (without tenant scoping for this example)
    document = db.query(Document).filter(Document.id == doc_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Verify current tenant owns this resource
    # Raises 403 if mismatch
    verify_tenant_access(document.tenant_id, tenant_id)
    
    # Safe to proceed
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted"}
```

---

## 4. Decorators

### Require Tenant Access
```python
from app.core.tenant_decorators import require_tenant_access

@router.get("/documents/{doc_id}")
@require_tenant_access("document")  # Parameter name containing resource
async def get_document(
    doc_id: uuid.UUID,
    document: Document = Depends(get_document_by_id),  # Must be named "document"
    tenant_id: str = Depends(get_current_tenant_id)
):
    # Decorator automatically verifies document.tenant_id matches JWT tenant_id
    # Raises 403 if mismatch
    return document
```

### Tenant Scoped Function
```python
from app.core.tenant_decorators import tenant_scoped

@tenant_scoped
async def process_document_background(doc_id: uuid.UUID, db: Session):
    """Background task that requires tenant context"""
    # This will fail if tenant context is not set
    tq = get_tenant_scoped_query(db)
    document = tq.get_by_id(Document, doc_id)
    
    # Process document...
```

---

## 5. Context Management (Advanced)

### Get Tenant Context
```python
from app.core.tenant_context import get_tenant_context, require_tenant_context

# Get tenant ID (returns None if not set)
tenant_id = get_tenant_context()

# Get tenant ID (raises error if not set)
tenant_id = require_tenant_context()
```

### Set Tenant Context (For Background Tasks)
```python
from app.core.tenant_context import set_tenant_context, clear_tenant_context

async def background_task(tenant_id: str, user_id: str):
    try:
        # Set context for this task
        set_tenant_context(tenant_id, user_id)
        
        # Now tenant-scoped queries will work
        tq = get_tenant_scoped_query(db)
        documents = tq.query(Document).all()
        
    finally:
        # Always clean up
        clear_tenant_context()
```

---

## 6. Common Patterns

### Pattern 1: List Resources
```python
@router.get("/documents")
async def list_documents(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    tq = get_tenant_scoped_query(db)
    
    documents = (
        tq.query(Document)
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return documents
```

### Pattern 2: Get Single Resource
```python
@router.get("/documents/{doc_id}")
async def get_document(
    doc_id: uuid.UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    tq = get_tenant_scoped_query(db)
    document = tq.get_by_id(Document, doc_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document
```

### Pattern 3: Create Resource
```python
@router.post("/documents")
async def create_document(
    request: DocumentCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    document = Document(**request.dict())
    
    tq = get_tenant_scoped_query(db)
    created_doc = tq.create(document)
    db.commit()
    db.refresh(created_doc)
    
    return created_doc
```

### Pattern 4: Update Resource
```python
@router.put("/documents/{doc_id}")
async def update_document(
    doc_id: uuid.UUID,
    request: DocumentUpdate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    tq = get_tenant_scoped_query(db)
    document = tq.get_by_id(Document, doc_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Update fields
    for key, value in request.dict(exclude_unset=True).items():
        setattr(document, key, value)
    
    db.commit()
    db.refresh(document)
    
    return document
```

### Pattern 5: Delete Resource
```python
@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: uuid.UUID,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    tq = get_tenant_scoped_query(db)
    document = tq.get_by_id(Document, doc_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}
```

---

## 7. Security Best Practices

### ✅ DO:
- Always use `get_tenant_scoped_query()` for database queries
- Use `get_current_tenant_id()` dependency in all protected endpoints
- Verify tenant access when accessing resources by ID
- Log tenant_id with all operations
- Test cross-tenant access scenarios

### ❌ DON'T:
- Query database without tenant filtering
- Trust client-provided tenant_id
- Expose tenant information in error messages
- Skip tenant verification for "admin" users
- Use global tenant state
- Manually set tenant_id from request parameters

---

## 8. Error Handling

### Status Codes
- `401 Unauthorized` - Missing or invalid JWT token
- `403 Forbidden` - Valid token, but wrong tenant
- `404 Not Found` - Resource doesn't exist (for current tenant)

### Error Messages
```python
# ✅ Good - Doesn't leak information
raise HTTPException(status_code=404, detail="Document not found")

# ❌ Bad - Reveals resource exists for another tenant
raise HTTPException(status_code=403, detail="Document belongs to tenant XYZ")
```

---

## 9. Testing

### Test Tenant Isolation
```python
def test_cross_tenant_access_blocked(client, user1, user2, tenant1, tenant2):
    # Create resource for tenant 2
    doc = create_document(tenant2)
    
    # Login as user1 (tenant 1)
    token = get_token(user1)
    
    # Try to access tenant 2's document
    response = client.get(
        f"/api/v1/documents/{doc.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Should return 404 (not 403, to avoid info leakage)
    assert response.status_code == 404
```

---

## 10. Troubleshooting

### Issue: "Tenant context not set"
**Cause:** Trying to use tenant-scoped queries outside request context  
**Solution:** Ensure middleware is running or manually set context

### Issue: "Resource not found" but it exists
**Cause:** Resource belongs to different tenant  
**Solution:** Verify JWT token has correct tenant_id

### Issue: Cross-tenant access not blocked
**Cause:** Not using tenant-scoped queries  
**Solution:** Use `get_tenant_scoped_query()` instead of direct queries

---

## 11. Performance Tips

### Use get_current_tenant_id() for Performance
```python
# ✅ Fast - No database query
tenant_id: str = Depends(get_current_tenant_id)

# ❌ Slower - Queries database
tenant: Tenant = Depends(get_current_tenant)
```

### Cache Tenant Data
```python
# If you need tenant info frequently, cache it
@lru_cache(maxsize=100)
def get_tenant_info(tenant_id: str):
    # Cache tenant information
    pass
```

---

## Summary

**Key Components:**
1. **Middleware** - Extracts tenant_id from JWT
2. **Dependencies** - Provides tenant context to endpoints
3. **Scoped Queries** - Automatic tenant filtering
4. **Decorators** - Declarative access control
5. **Context Variables** - Request-scoped isolation

**Security Layers:**
- Layer 1: Middleware (JWT validation)
- Layer 2: Dependencies (Tenant extraction)
- Layer 3: Scoped Queries (Automatic filtering)
- Layer 4: Decorators (Access verification)

**Always remember:** Every database query should be tenant-scoped! 🔒
