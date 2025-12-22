"""
Synchronous document processing for development/testing without Celery.
"""

import logging
import uuid
import io
from sqlalchemy.orm import Session

from app.models.database import Document, DocumentChunk
from app.core.storage import get_storage_backend
from app.processing.text_extraction import TextExtractor
from app.processing.text_cleaning import TextCleaner
from app.processing.chunking import DocumentChunker
from app.core.embedding import get_embedding_service
from app.core.encryption import KeyManager
from app.core.vector_encryption import VectorEncryptor
from app.core.cyborg import CyborgDBManager
from app.core.config import settings

logger = logging.getLogger(__name__)


async def process_document_sync(document_id: uuid.UUID, db: Session) -> dict:
    """
    Process a document synchronously (without Celery).
    
    This is used when Redis/Celery is not available.
    """
    logger.info(f"Starting synchronous processing for document {document_id}")
    
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            logger.error(f"Document {document_id} not found")
            return {"status": "failed", "error": "Document not found"}
        
        # Update status to processing
        document.status = "extracting"
        db.commit()
        
        # 1. Get file from storage
        storage = get_storage_backend()
        
        try:
            file_data_bytes = await storage.get_file(document.storage_path)
            file_stream = io.BytesIO(file_data_bytes)
        except Exception as e:
            logger.error(f"Failed to retrieve file from storage: {e}")
            document.status = "failed"
            document.error_message = f"Storage retrieval error: {str(e)}"
            db.commit()
            return {"status": "failed", "error": str(e)}
        
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
        try:
            tenant_key = KeyManager.get_tenant_key(db, document.tenant_id)
        except ValueError:
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
            
            # Create DB objects and CyborgDB batch
            cyborg_batch = []
            
            for j, chunk in enumerate(batch):
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
                
                # Prepare CyborgDB record
                # CyborgDB's encrypted index uses its own encryption with index_key
                # So we send the raw (unencrypted) embedding vector, not the Fernet token
                cyborg_record = {
                    "id": str(chunk_uuid),
                    "vector": embeddings[j],  # Send raw vector, CyborgDB will encrypt it
                    "metadata": {
                        "doc_id": str(chunk.doc_id),
                        "tenant_id": str(chunk.tenant_id),
                        "chunk_sequence": chunk.sequence,
                        "page_number": chunk.page_number
                    }
                }
                cyborg_batch.append(cyborg_record)
            
            # Upsert batch to CyborgDB
            try:
                # Convert tenant_key (base64 string) to list of bytes for CyborgDB index_key
                import base64
                index_key_bytes = base64.urlsafe_b64decode(tenant_key)
                index_key_list = list(index_key_bytes[:32])  # Convert to 32-element list
                while len(index_key_list) < 32:
                    index_key_list.append(0)
                
                CyborgDBManager.upsert_vectors(str(document.tenant_id), cyborg_batch, index_key=index_key_list)
                logger.info(f"Uploaded batch of {len(cyborg_batch)} vectors to CyborgDB for tenant {document.tenant_id}")
            except Exception as e:
                logger.error(f"CyborgDB upsert failed for batch: {e}", exc_info=True)
                # Continue processing even if CyborgDB fails - documents are still searchable in DB
        
        # Bulk insert chunks
        db.add_all(db_chunks)
        
        # Update document stats
        document.chunk_count = len(db_chunks)
        document.status = "completed"
        
        db.commit()
        
        logger.info(f"Successfully processed document {document_id}: {len(db_chunks)} chunks created")
        return {
            "status": "success",
            "document_id": str(document_id),
            "chunk_count": len(db_chunks),
            "text_length": len(cleaned_text)
        }
        
    except Exception as e:
        logger.exception(f"Error processing document {document_id}")
        db.rollback()
        
        # Update document status
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = "failed"
                document.error_message = str(e)
                db.commit()
        except Exception as db_e:
            logger.error(f"Database error during error handling: {db_e}")
        
        return {"status": "failed", "error": str(e)}
