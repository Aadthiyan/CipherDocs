"""
Document upload and management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
import uuid
import logging
from typing import Optional

from app.db.database import get_db
from app.models.database import Document, User
from app.schemas.documents import (
    DocumentUploadResponse, DocumentListItem, DocumentDetail,
    DocumentsListResponse
)
from app.api.deps import get_current_user, get_current_tenant_id
from app.core.storage import get_storage_backend, calculate_file_hash
from app.core.rbac import UserRole, Permission, require_permission
from app.db.tenant_scoping import get_tenant_scoped_query

router = APIRouter(prefix="/documents", tags=["Documents"])
logger = logging.getLogger(__name__)

# Supported file types
ALLOWED_EXTENSIONS = {
    'pdf': 'application/pdf',
    'txt': 'text/plain',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'doc': 'application/msword',
}

# Maximum file size (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes


def validate_file_type(filename: str, content_type: str) -> str:
    """
    Validate file type based on extension and content type.
    
    Returns:
        File extension if valid
        
    Raises:
        HTTPException: If file type is not supported
    """
    # Get file extension
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {ext}. Allowed types: {', '.join(ALLOWED_EXTENSIONS.keys())}"
        )
    
    return ext


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload document",
    description="Upload a document for processing. Supports PDF, DOCX, TXT files up to 50MB."
)
@require_permission(Permission.UPLOAD_DOCUMENTS)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload"),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    """
    Upload a document for processing.
    
    - **file**: Document file (PDF, DOCX, TXT, max 50MB)
    
    Returns document metadata and processing status.
    
    **File Validation:**
    - Type: PDF, DOCX, DOC, TXT
    - Size: Maximum 50MB
    - Duplicate detection via SHA-256 hash
    
    **Processing Flow:**
    1. Validate file type and size
    2. Calculate file hash for duplicate detection
    3. Store file in secure storage
    4. Create database record
    5. Return document metadata
    """
    
    # Validate file type
    doc_type = validate_file_type(file.filename, file.content_type)
    
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    
    # Validate file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large: {file_size} bytes. Maximum size: {MAX_FILE_SIZE} bytes (50MB)"
        )
    
    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file uploaded"
        )
    
    # Calculate file hash for duplicate detection
    from io import BytesIO
    file_stream = BytesIO(file_content)
    file_hash = calculate_file_hash(file_stream)
    file_stream.seek(0)
    
    # Check for duplicate
    tq = get_tenant_scoped_query(db)
    existing_doc = tq.query(Document).filter(Document.file_hash == file_hash).first()
    
    if existing_doc:
        logger.info(
            f"Duplicate document detected: hash={file_hash} "
            f"existing_id={existing_doc.id} tenant_id={tenant_id}"
        )
        return DocumentUploadResponse(
            id=existing_doc.id,
            filename=existing_doc.filename,
            doc_type=existing_doc.doc_type,
            file_size_bytes=existing_doc.file_size_bytes,
            file_hash=existing_doc.file_hash,
            status=existing_doc.status,
            storage_path=existing_doc.storage_path,
            tenant_id=existing_doc.tenant_id,
            uploaded_at=existing_doc.uploaded_at,
            message="Document already exists (duplicate detected)"
        )
    
    # Generate document ID
    document_id = uuid.uuid4()
    
    try:
        # Save file to storage
        storage = get_storage_backend()
        storage_path = await storage.save_file(
            file_data=file_stream,
            tenant_id=tenant_id,
            document_id=str(document_id),
            filename=file.filename
        )
        
        # Create document record
        document = Document(
            id=document_id,
            tenant_id=uuid.UUID(tenant_id),
            filename=file.filename,
            doc_type=doc_type,
            file_size_bytes=file_size,
            file_hash=file_hash,
            storage_path=storage_path,
            status="uploaded"
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Process document (synchronous by default, Celery disabled for free tier)
        processing_result = None
        try:
            # Use synchronous processing (no Celery/Redis required)
            # This works perfectly fine for hackathon use cases
            logger.info(f"Starting synchronous processing for document {document.id}")
            from app.processing.sync_processor import process_document_sync
            processing_result = await process_document_sync(document.id, db)
            logger.info(f"Synchronous processing completed: {processing_result}")
        except Exception as sync_error:
            logger.error(f"Synchronous processing failed: {sync_error}", exc_info=True)
            # Document remains in 'uploaded' status for manual retry
        
        logger.info(
            f"Document uploaded: id={document.id} filename={file.filename} "
            f"size={file_size} tenant_id={tenant_id} user_id={current_user.id}"
        )
        
        # Refresh document to get updated status
        db.refresh(document)
        
        return DocumentUploadResponse(
            id=document.id,
            filename=document.filename,
            doc_type=document.doc_type,
            file_size_bytes=document.file_size_bytes,
            file_hash=document.file_hash,
            status=document.status,
            storage_path=document.storage_path,
            tenant_id=document.tenant_id,
            uploaded_at=document.uploaded_at,
            message=f"Document uploaded and {processing_result['status'] if processing_result else 'queued for processing'}"
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to upload document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.get(
    "",
    response_model=DocumentsListResponse,
    summary="List documents",
    description="Get a list of all documents for the current tenant."
)
@require_permission(Permission.VIEW_DOCUMENTS)
async def list_documents(
    skip: int = 0,
    limit: int = 10,
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    """
    List all documents for the current tenant.
    
    - **skip**: Number of documents to skip (pagination)
    - **limit**: Maximum number of documents to return
    - **status_filter**: Optional status filter (uploaded, processing, completed, failed)
    
    Returns paginated list of documents.
    """
    
    tq = get_tenant_scoped_query(db)
    query = tq.query(Document)
    
    # Apply status filter if provided
    if status_filter:
        query = query.filter(Document.status == status_filter)
    
    # Get total count
    total = query.count()
    
    # Get paginated documents
    documents = (
        query
        .order_by(Document.uploaded_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return DocumentsListResponse(
        documents=[DocumentListItem.model_validate(doc) for doc in documents],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get(
    "/{document_id}",
    response_model=DocumentDetail,
    summary="Get document details",
    description="Get detailed information about a specific document."
)
@require_permission(Permission.VIEW_DOCUMENTS)
async def get_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific document.
    
    - **document_id**: The document's UUID
    
    Returns document details if found and belongs to current tenant.
    """
    
    tq = get_tenant_scoped_query(db)
    document = tq.get_by_id(Document, document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return DocumentDetail.model_validate(document)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete document",
    description="Delete a document and its associated data."
)
@require_permission(Permission.DELETE_DOCUMENTS)
async def delete_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    """
    Delete a document.
    
    - **document_id**: The document's UUID
    
    Returns success message.
    """
    
    tq = get_tenant_scoped_query(db)
    document = tq.get_by_id(Document, document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    try:
        # Delete file from storage
        storage = get_storage_backend()
        await storage.delete_file(document.storage_path)
        
        # Delete database record
        db.delete(document)
        db.commit()
        
        logger.info(
            f"Document deleted: id={document_id} filename={document.filename} "
            f"tenant_id={tenant_id} user_id={current_user.id}"
        )
        
        return {
            "message": "Document deleted successfully",
            "document_id": str(document_id),
            "filename": document.filename
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.post(
    "/{document_id}/retry",
    status_code=status.HTTP_200_OK,
    summary="Retry document processing",
    description="Retry processing for a failed or stuck document."
)
@require_permission(Permission.UPLOAD_DOCUMENTS)
async def retry_processing(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    """
    Retry processing for a document.
    
    - **document_id**: The document's UUID
    
    Returns success message if retry triggered.
    """
    
    tq = get_tenant_scoped_query(db)
    document = tq.get_by_id(Document, document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Trigger background task
    try:
        from app.worker import process_document_task
        process_document_task.delay(str(document.id))
        
        # Reset retry status in DB
        document.retry_count = 0
        document.status = "uploaded" # Reset status so worker picks it up as fresh
        document.error_message = None
        db.commit()
        
        return {"message": "Processing retry triggered successfully", "document_id": str(document_id)}
    except Exception as e:
        logger.error(f"Failed to trigger retry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger processing retry"
        )
