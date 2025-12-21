"""
Celery worker configuration and tasks for async document processing.
"""

import os
from celery import Celery
from sqlalchemy.orm import Session
import uuid
import logging
import asyncio
from typing import Dict, Any

from app.core.config import settings
from app.db.database import SessionLocal
from app.models.database import Document, DocumentChunk
from app.core.storage import get_storage_backend
from app.processing.text_extraction import TextExtractor
from app.processing.text_cleaning import TextCleaner
from app.processing.chunking import DocumentChunker
from app.core.embedding import get_embedding_service
from app.core.encryption import KeyManager
from app.core.vector_encryption import VectorEncryptor
from app.core.cyborg import CyborgDBManager

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Celery
# Use Redis as broker and backend
celery_app = Celery(
    "cyborgdb_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

def get_db_session():
    """Helper to get DB session in tasks"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def process_document_task(self, document_id: str):
    """
    Background task to process an uploaded document.
    
    1. Fetch document metadata from DB
    2. Download file from storage
    3. Extract text
    4. Clean/Preprocess text
    5. Chunk text
    6. Save chunks to DB
    7. Update status
    """
    logger.info(f"Starting processing for document {document_id}")
    
    db = SessionLocal()
    try:
        doc_uuid = uuid.UUID(document_id)
        document = db.query(Document).filter(Document.id == doc_uuid).first()
        
        if not document:
            logger.error(f"Document {document_id} not found")
            return {"status": "failed", "error": "Document not found"}
            
        # Update status to processing (extracting)
        if document.status == "uploaded": 
            document.status = "extracting"
            db.commit()
        
        # 1. Get file from storage
        storage = get_storage_backend()
        
        try:
            import io
            # Run async storage call synchronously
            file_data_bytes = asyncio.run(storage.get_file(document.storage_path))
            file_stream = io.BytesIO(file_data_bytes)
            
        except Exception as e:
            logger.error(f"Failed to retrieve file from storage: {e}")
            document.status = "failed"
            document.error_message = f"Storage retrieval error: {str(e)}"
            db.commit()
            raise self.retry(exc=e)

        # 2. Extract Text
        content = TextExtractor.extract(file_stream, document.doc_type)
        
        if content.error:
            logger.error(f"Extraction failed: {content.error}")
            document.status = "failed"
            document.error_message = f"Extraction error: {content.error}"
            db.commit()
            return {"status": "failed", "error": content.error}
            
        # 3. Clean Text
        cleaned_text = TextCleaner.clean(content.text)
        
        if not cleaned_text:
             logger.warning(f"No text extracted/cleaned for document {document_id}")
             document.status = "failed"
             document.error_message = "No text extracted from document"
             db.commit()
             return {"status": "failed", "error": "Empty text"}

        # 4. Chunk Text
        document.status = "chunking"
        db.commit()
        
        chunker = DocumentChunker(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )
        
        chunks = chunker.chunk_document(
            text=cleaned_text,
            doc_id=document.id,
            tenant_id=document.tenant_id
            # metadata=content.metadata # Not passing full metadata yet as chunker signature assumes simple
        )
        
        if not chunks:
            logger.warning(f"No chunks created for document {document_id}")
            document.status = "failed"
            document.error_message = "Text could not be split into valid chunks"
            db.commit()
            return {"status": "failed", "error": "No chunks"}
            
        # 5. Generate Embeddings & Encrypt
        document.status = "embedding"
        db.commit()
        
        embedding_service = get_embedding_service()
        
        # Get tenant key for encryption
        # We need a fresh session or reuse existing. Reusing 'db' session is fine.
        try:
            tenant_key = KeyManager.get_tenant_key(db, document.tenant_id)
        except ValueError:
            # If key doesn't exist, create one? 
            # It should have been created at signup. But for robustness/legacy support:
            logger.warning(f"No key found for tenant {document.tenant_id}, creating new one.")
            KeyManager.create_tenant_key(db, document.tenant_id)
            tenant_key = KeyManager.get_tenant_key(db, document.tenant_id)

        # Batch processing
        BATCH_SIZE = 32
        db_chunks = []
        
        total_chunks = len(chunks)
        
        for i in range(0, total_chunks, BATCH_SIZE):
            batch = chunks[i : i + BATCH_SIZE]
            batch_texts = [c.text for c in batch]
            
            # Generate Embeddings
            embeddings = embedding_service.generate_embeddings(batch_texts)
            
            # Encrypt Embeddings
            encrypted_tokens = VectorEncryptor.batch_encrypt(embeddings, tenant_key)
            
            # Create DB objects
            # Create DB objects and CyborgDB batch
            cyborg_batch = []
            
            for j, chunk in enumerate(batch):
                # Use deterministic ID for idempotency (doc_id + sequence)
                chunk_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"{document.id}_{chunk.sequence}")
                
                db_chunk = DocumentChunk(
                    id=chunk_uuid,
                    doc_id=chunk.doc_id,
                    tenant_id=chunk.tenant_id,
                    chunk_sequence=chunk.sequence,
                    text=chunk.text,
                    page_number=chunk.page_number,
                    section_heading=chunk.section_heading,
                    encrypted_embedding=encrypted_tokens[j],
                    embedding_dimension=embedding_service.vector_dimension
                )
                db_chunks.append(db_chunk)
                
                # Prepare CyborgDB record (encrypted)
                cyborg_record = {
                    "id": str(chunk_uuid),
                    "values": encrypted_tokens[j],
                    "metadata": {
                        "doc_id": str(chunk.doc_id),
                        "tenant_id": str(chunk.tenant_id),
                        "chunk_sequence": chunk.sequence,
                        "page_number": chunk.page_number
                    }
                }
                cyborg_batch.append(cyborg_record)
                
            # Upsert batch to CyborgDB
            # We fail the task if this fails, ensuring consistency with DB (rollback)
            try:
                # Determine tenant index via Tenant ID (assuming convention)
                # Note: CyborgDBManager resolves index name as "tenant_{id}"
                if settings.CYBORGDB_API_KEY:
                     import base64
                     index_key = base64.urlsafe_b64decode(tenant_key)
                     CyborgDBManager.upsert_vectors(str(document.tenant_id), cyborg_batch, index_key=index_key)
            except Exception as e:
                logger.error(f"CyborgDB upsert failed for batch: {e}")
                raise e
        
        # Bulk insert chunks
        db.add_all(db_chunks)
        
        # Update document stats
        document.chunk_count = len(db_chunks)
        document.status = "completed"
        
        db.commit()
        
        
        logger.info(f"Successfully processed document {document_id}: {len(db_chunks)} chunks created")
        return {
            "status": "success", 
            "document_id": document_id, 
            "chunk_count": len(db_chunks),
            "text_length": len(cleaned_text)
        }
        
    except Exception as e:
        logger.exception(f"Error processing document {document_id}")
        
        # Calculate backoff: 1s, 4s, 16s
        # retry_number starts at 0 for first retry attempt
        retry_number = self.request.retries
        backoff = 4 ** retry_number
        
        try:
            # Refresh session to ensure clean state
            db.rollback()
            document = db.query(Document).filter(Document.id == doc_uuid).first()
            if document:
                document.retry_count = retry_number + 1
                document.error_message = str(e)
                
                # Check if this is the last retry
                if retry_number >= self.max_retries:
                    document.status = "failed"
                    logger.error(f"Max retries exceeded for document {document_id}. Marking as failed.")
                else:
                    # Keep current status or append info?
                    # We'll rely on the existing status (extracting/chunking) 
                    # but maybe update error message to indicate retry
                    logger.info(f"Retrying document {document_id} in {backoff}s (Attempt {retry_number + 1})")
                    pass
                
                db.commit()
        except Exception as db_e:
            logger.error(f"Database error during error handling: {db_e}")
            
        # Re-raise as Celery retry
        raise self.retry(countdown=backoff, exc=e)
        
    finally:
        db.close()
