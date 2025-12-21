from typing import List, Any, Optional
try:
    from langchain_core.retrievers import BaseRetriever
    from langchain_core.documents import Document
except ImportError:
    # Fallback for older langchain versions
    from langchain.schema import BaseRetriever, Document
from pydantic import Field
from sqlalchemy.orm import Session
import uuid
import logging

from app.core.cyborg import CyborgDBManager
from app.core.embedding import get_embedding_service
from app.core.encryption import KeyManager
from app.core.vector_encryption import VectorEncryptor
from app.models.database import DocumentChunk, Document as DB_Document

logger = logging.getLogger(__name__)

class CyborgDBRetriever(BaseRetriever):
    """
    LangChain Retriever for Encrypted CyborgDB Indexes.
    Handles embedding, encryption, search, and content hydration.
    """
    tenant_id: str = Field(..., description="UUID of the tenant")
    db_session: Any = Field(..., description="SQLAlchemy Session")
    top_k: int = Field(10, description="Number of results to retrieve")
    augment_context: bool = Field(False, description="Fetch adjacent chunks for context")

    def _get_relevant_documents(self, query: str) -> List[Document]:
        try:
            # 1. Embed
            embedding_service = get_embedding_service()
            # Returns List[List[float]]
            embeddings = embedding_service.generate_embeddings([query])
            query_vector = embeddings[0]
            
            # 2. Get or create tenant encryption key
            tenant_uuid = uuid.UUID(self.tenant_id)
            try:
                tenant_key = KeyManager.get_tenant_key(self.db_session, tenant_uuid)
            except ValueError as e:
                logger.warning(f"No encryption key found for tenant {self.tenant_id}, creating new one")
                KeyManager.create_tenant_key(self.db_session, tenant_uuid)
                tenant_key = KeyManager.get_tenant_key(self.db_session, tenant_uuid)
            
            # 3. Encrypt query vector
            encrypted_query = VectorEncryptor.encrypt_vector(query_vector, tenant_key)
            
            # 4. Search CyborgDB
            import base64
            index_key = base64.urlsafe_b64decode(tenant_key)
            raw_results = CyborgDBManager.search(self.tenant_id, encrypted_query, self.top_k, index_key=index_key)
            
            if not raw_results:
                logger.info(f"No search results found for tenant {self.tenant_id}")
                return []
                
            # 5. Hydrate Results (Fetch Text from DB)
            chunk_ids = []
            scores_map = {}
            for res in raw_results:
                # Handle different SDK response formats
                mid = res.get('id') if isinstance(res, dict) else getattr(res, 'id', None)
                if mid:
                    chunk_ids.append(str(mid))
                    # CyborgDB returns 'distance', convert to similarity
                    if isinstance(res, dict):
                        distance = res.get('distance')
                        if distance is not None:
                            # Convert distance to similarity: similarity = 1 - distance
                            score = max(0.0, 1.0 - float(distance))
                        else:
                            score = res.get('score') or res.get('similarity') or 0.0
                    else:
                        distance = getattr(res, 'distance', None)
                        if distance is not None:
                            score = max(0.0, 1.0 - float(distance))
                        else:
                            score = getattr(res, 'score', None) or getattr(res, 'similarity', None) or 0.0
                    scores_map[str(mid)] = float(score) if score is not None else 0.0
            
            if not chunk_ids:
                return []

            # Determine IDs to fetch (including adjacent if requested)
            fetch_ids = set(chunk_ids)
            
            # 4b. Fetch Chunks
            # We fetch base chunks first to handle context
            base_chunks = self.db_session.query(DocumentChunk).filter(
                DocumentChunk.id.in_(chunk_ids),
                DocumentChunk.tenant_id == tenant_uuid
            ).all()
            
            base_chunks_map = {str(c.id): c for c in base_chunks}
            
            documents = []
            
            # Resolve filenames
            doc_ids = list(set([c.doc_id for c in base_chunks]))
            db_docs = self.db_session.query(DB_Document).filter(DB_Document.id.in_(doc_ids)).all()
            docs_map = {d.id: d for d in db_docs}
            
            for mid in chunk_ids:
                chunk = base_chunks_map.get(mid)
                if not chunk:
                    continue
                
                content = chunk.text
                metadata = {
                    "source": mid,
                    "score": scores_map.get(mid, 0.0),
                    "doc_id": str(chunk.doc_id),
                    "page": chunk.page_number,
                    "filename": docs_map[chunk.doc_id].filename if chunk.doc_id in docs_map else "Unknown"
                }
                
                # Context Augmentation
                if self.augment_context:
                    # Logic: Fetch seq-1 and seq+1 for same doc_id
                    adj_content = self._fetch_adjacent_context(chunk)
                    if adj_content:
                        content = adj_content # Replace or append? Usually replace with wider window
                        metadata["augmented"] = True
                
                documents.append(Document(page_content=content, metadata=metadata))
                
            return documents
            
        except Exception as e:
            logger.error(f"Retriever error: {e}")
            return []
            
    def _fetch_adjacent_context(self, chunk: DocumentChunk) -> str:
        """Fetch previous and next chunks if available"""
        try:
            # Query for seq-1 and seq+1
            start = chunk.chunk_sequence - 1
            end = chunk.chunk_sequence + 1
            
            adj_chunks = self.db_session.query(DocumentChunk).filter(
                DocumentChunk.doc_id == chunk.doc_id,
                DocumentChunk.chunk_sequence.in_([start, end])
            ).all()
            
            # Sort by sequence
            sorted_chunks = sorted(adj_chunks + [chunk], key=lambda c: c.chunk_sequence)
            return "\n...\n".join([c.text for c in sorted_chunks])
            
        except Exception:
            return chunk.text # Fallback

    def get_relevant_documents(self, query: str) -> List[Document]:
        """
        Public method to get relevant documents.
        This is called by the search API.
        """
        return self._get_relevant_documents(query)

    async def _aget_relevant_documents(self, query: str) -> List[Document]:
        return self._get_relevant_documents(query)
