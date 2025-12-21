"""
CyborgDB Embedded client configuration and connection management.

Uses CyborgDB as an embedded Python library directly integrated into the FastAPI application.
This approach requires no separate service deployment and keeps vector search within the backend process.
"""

import logging
import time
import os
import secrets
from typing import Optional

try:
    from cyborgdb_core import Client, IndexIVFFlat
except ImportError:
    # Fallback for dev/mocking if package not installed
    logging.warning("CyborgDB embedded package not found. Using mock client.")
    
    class IndexIVFFlat:
        """Mock index config"""
        def __init__(self, dimension: int, n_clusters: int):
            self.dimension = dimension
            self.n_clusters = n_clusters
    
    class MockIndex:
        """Mock index for development/testing"""
        def __init__(self, name: str):
            self.name = name
            self.vectors = {}
            
        def upsert(self, vectors):
            """Store vectors in mock index"""
            for v in vectors:
                self.vectors[v["id"]] = v
            return len(vectors)
            
        def query(self, vector, top_k=10):
            """Mock query - returns all stored vectors (no actual search)"""
            # In a real implementation, would do similarity search
            # For mock, just return stored vectors
            results = list(self.vectors.values())[:top_k]
            return {"matches": results} if results else {"matches": []}
    
    class Client:
        def __init__(self, backing_store: str = "memory", connection_string: str = None):
            """Initialize embedded client"""
            self.backing_store = backing_store
            self.connection_string = connection_string
            self.indexes = {}
        
        def list_indexes(self):
            return list(self.indexes.keys())
            
        def create_index(self, index_name: str, index_key: bytes, index_config=None, embedding_model=None, metric=None):
            if index_name in self.indexes:
                raise ValueError("Index already exists")
            self.indexes[index_name] = {
                "key": index_key,
                "config": index_config,
                "index": MockIndex(index_name)
            }
            return self.indexes[index_name]["index"]
            
        def load_index(self, index_name: str, index_key: bytes = None):
            """Load an existing index"""
            if index_name not in self.indexes:
                raise ValueError(f"Index {index_name} not found")
            return self.indexes[index_name]["index"]
            
        def delete_index(self, index_name: str):
            if index_name in self.indexes:
                del self.indexes[index_name]

from app.core.config import settings

logger = logging.getLogger(__name__)

class CyborgDBManager:
    """
    Singleton manager for embedded CyborgDB client.
    Handles initialization, connection pooling, and resource management.
    
    The embedded approach runs CyborgDB directly in the FastAPI process,
    eliminating the need for a separate microservice and reducing latency.
    """
    _client: Optional[Client] = None
    _storage_path: str = "/tmp/cyborgdb_storage"  # Persistent storage location
    
    @classmethod
    def get_client(cls) -> Client:
        """
        Get or initialize the embedded CyborgDB client.
        """
        if cls._client:
            return cls._client
        
        try:
            logger.info("Initializing embedded CyborgDB client...")
            
            # Ensure storage directory exists
            os.makedirs(cls._storage_path, exist_ok=True)
            
            # Initialize embedded client with file-based backing store
            # "redis" backing store for persistent storage (optional)
            # "memory" for in-memory (faster but not persistent)
            backing_store = settings.CYBORGDB_BACKING_STORE
            
            if backing_store == "redis" and settings.REDIS_URL:
                # Use Redis as backing store for persistence
                cls._client = Client(backing_store="redis", connection_string=settings.REDIS_URL)
                logger.info("CyborgDB using Redis backing store")
            else:
                # Use memory-based storage (recommended for Render)
                cls._client = Client(backing_store="memory")
                logger.info("CyborgDB using in-memory backing store")
            
            return cls._client
            
        except Exception as e:
            logger.error(f"Failed to initialize CyborgDB embedded client: {e}")
            raise e

    @classmethod
    def check_health(cls) -> bool:
        """Check availability"""
        try:
            client = cls.get_client()
            logger.debug("CyborgDB health check passed")
            return True
        except Exception as e:
            logger.error(f"CyborgDB health check failed: {e}")
            return False
            
    @classmethod
    def create_tenant_index(cls, tenant_id: str, dimension: int = 384, key: bytes = None) -> str:
        """
        Create an encrypted index for a tenant using embedded CyborgDB.
        
        Args:
            tenant_id: UUID string
            dimension: Vector dimension (default 384 for sentence-transformers)
            key: Tenant encryption key (32 bytes)
            
        Returns:
            Index name (str)
        """
        client = cls.get_client()
        index_name = f"tenant_{tenant_id}"
        
        try:
            logger.info(f"Creating embedded CyborgDB index: {index_name}")
            
            # Generate key if not provided
            if key is None:
                key = secrets.token_bytes(32)
                logger.debug(f"Generated 32-byte encryption key for {index_name}")
            
            # Create encrypted index using embedded SDK
            # IndexIVFFlat: Inverted File Index with Flat quantization (good balance)
            index_config = IndexIVFFlat(dimension, n_clusters=min(100, max(4, dimension // 40)))
            
            index = client.create_index(
                index_name=index_name,
                index_key=key,
                index_config=index_config,
                metric="cosine"
            )
            logger.info(f"Index {index_name} created successfully with dimension={dimension}")
            return index_name
            
        except Exception as e:
            if "exists" in str(e).lower() or "conflict" in str(e).lower():
                logger.info(f"Index {index_name} already exists")
                return index_name
            
            logger.error(f"Failed to create index {index_name}: {e}")
            raise e

    @classmethod
    def delete_tenant_index(cls, tenant_id: str):
        """Delete a tenant's encrypted index"""
        client = cls.get_client()
        index_name = f"tenant_{tenant_id}"
        
        try:
            logger.info(f"Deleting embedded CyborgDB index: {index_name}")
            client.delete_index(index_name)
            logger.info(f"Index {index_name} deleted successfully")
            
        except Exception as e:
            logger.error(f"Failed to delete index {index_name}: {e}")
            if "not found" in str(e).lower():
                pass
            else:
                raise e

    @classmethod
    def upsert_vectors(cls, tenant_id: str, vectors: list, index_key: bytes = None) -> int:
        """
        Upsert encrypted vectors to the tenant's embedded index.
        
        Args:
            tenant_id: Tenant UUID
            vectors: List of dicts [{"id": str, "values": list[float], "metadata": dict}]
            index_key: 32-byte encryption key for the index (bytes)
            
        Returns:
            Number of vectors upserted
        """
        client = cls.get_client()
        index_name = f"tenant_{tenant_id}"
        
        try:
            # Load index reference
            index = client.load_index(index_name, index_key)
            
            logger.info(f"Upserting {len(vectors)} vectors to {index_name}")
            
            # Upsert vectors to embedded index
            result = index.upsert(vectors)
            logger.debug(f"Upserted {result} vectors to {index_name}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to upsert vectors to {index_name}: {e}")
            raise e

    @classmethod
    def search(cls, tenant_id: str, query_vector: list, top_k: int = 10, index_key: bytes = None) -> list:
        """
        Search the tenant's encrypted embedded index.
        
        Args:
            tenant_id: Tenant UUID
            query_vector: Query vector as list of floats (384-dimensional for sentence-transformers)
            top_k: Number of results to return
            index_key: 32-byte encryption key for the index (bytes)
            
        Returns:
            List of search results with metadata
        """
        client = cls.get_client()
        index_name = f"tenant_{tenant_id}"
        
        try:
            # Load index reference
            index = client.load_index(index_name, index_key)
            
            # Perform encrypted search on embedded index
            response = index.query(
                query_vectors=[query_vector],
                top_k=top_k
            )
            
            logger.debug(f"Embedded CyborgDB search returned results")
            
            # Normalize response if needed
            if isinstance(response, dict) and 'matches' in response:
                return response['matches']
                
            return response if isinstance(response, list) else []
            
        except Exception as e:
            # Check if it's an index not found error
            if "does not exist" in str(e).lower() or "not found" in str(e).lower():
                logger.warning(f"Index {index_name} not found - returning empty results")
                return []
            logger.error(f"Search failed for {index_name}: {e}")
            raise e

# Global access
def get_cyborg_client() -> Client:
    return CyborgDBManager.get_client()
