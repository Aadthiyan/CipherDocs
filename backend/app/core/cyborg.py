"""
CyborgDB Embedded client configuration and connection management.

Uses CyborgDB Lite (evaluation version) for encrypted vector search.
Perfect for hackathons and prototypes with up to 1M vectors.
"""

import logging
import secrets
import os
from typing import Optional, List, Dict

try:
    import cyborgdb_lite as cyborgdb
    CYBORGDB_AVAILABLE = True
except ImportError:
    CYBORGDB_AVAILABLE = False
    logging.warning("CyborgDB Lite not installed. Vector search will not work.")

from app.core.config import settings

logger = logging.getLogger(__name__)


class CyborgDBManager:
    """
    Manager for CyborgDB Lite embedded client.
    Handles initialization and encrypted vector operations for tenants.
    """
    _client: Optional = None
    _indexes: Dict[str, any] = {}
    _index_keys: Dict[str, bytes] = {}
    
    @classmethod
    def get_client(cls):
        """Get or initialize the CyborgDB client"""
        if cls._client is not None:
            return cls._client
        
        if not CYBORGDB_AVAILABLE:
            raise RuntimeError("CyborgDB Lite is not installed")
        
        try:
            logger.info("Initializing CyborgDB Lite client...")
            
            # Configure storage locations - CyborgDB Lite only supports memory and redis
            # For hackathon: use memory (fast, in-process)
            # Note: Indexes lost on worker restart - acceptable for demo/hackathon
            # For production: use redis backing store (requires Redis setup)
            backing_store = "memory"
            
            logger.info(f"CyborgDB using memory backing store (indexes lost on restart)")
            index_location = cyborgdb.DBConfig(backing_store)
            config_location = cyborgdb.DBConfig(backing_store)
            items_location = cyborgdb.DBConfig(backing_store)
            
            # Get API key from settings (set CYBORGDB_API_KEY in .env)
            api_key = os.getenv("CYBORGDB_API_KEY", "")
            
            if not api_key:
                logger.warning("CYBORGDB_API_KEY not set. Using default (may have limitations)")
            
            # Create CyborgDB client
            cls._client = cyborgdb.Client(
                api_key=api_key,
                index_location=index_location,
                config_location=config_location,
                items_location=items_location
            )
            
            logger.info(f"CyborgDB Lite initialized with {backing_store} backing store")
            return cls._client
            
        except Exception as e:
            logger.error(f"Failed to initialize CyborgDB Lite: {e}")
            raise e
    
    @classmethod
    def check_health(cls) -> bool:
        """Check if CyborgDB is available and working"""
        try:
            if not CYBORGDB_AVAILABLE:
                return False
            cls.get_client()
            logger.debug("CyborgDB health check passed")
            return True
        except Exception as e:
            logger.error(f"CyborgDB health check failed: {e}")
            return False
            
    @classmethod
    def create_tenant_index(cls, tenant_id: str, dimension: int = 384, key: str = None) -> str:
        """
        Create an encrypted index for a tenant.
        
        Args:
            tenant_id: UUID string
            dimension: Vector dimension (default 384 for sentence-transformers)
            key: Tenant encryption key (base64 string or bytes)
            
        Returns:
            Index name (str)
        """
        client = cls.get_client()
        index_name = f"tenant_{tenant_id}"
        
        try:
            logger.info(f"Creating CyborgDB index: {index_name}")
            
            # Convert key to 32-element list if provided
            if key is None:
                # Generate random 32 bytes
                key_bytes = secrets.token_bytes(32)
                key_list = list(key_bytes)
                logger.debug(f"Generated 32-byte encryption key for {index_name}")
            elif isinstance(key, str):
                # If it's a base64 string, decode it first
                try:
                    import base64
                    key_bytes = base64.urlsafe_b64decode(key)
                    key_list = list(key_bytes[:32])  # Take first 32 bytes
                except Exception:
                    # If not valid base64, use as-is and convert to list
                    key_bytes = key.encode('utf-8')[:32]
                    key_list = list(key_bytes)
            elif isinstance(key, bytes):
                # If bytes, convert to list (max 32 elements)
                key_list = list(key[:32])
            else:
                # Already a list or similar
                key_list = list(key)[:32]
            
            # Ensure exactly 32 elements
            while len(key_list) < 32:
                key_list.append(0)
            key_list = key_list[:32]
            
            # Store the key for later use
            cls._index_keys[index_name] = key_list
            
            # Create encrypted index with 32-element list
            index = client.create_index(
                index_name=index_name,
                index_key=key_list
            )
            
            cls._indexes[index_name] = index
            logger.info(f"Index {index_name} created successfully with dimension={dimension}")
            return index_name
            
        except Exception as e:
            if "exists" in str(e).lower() or "already" in str(e).lower():
                logger.info(f"Index {index_name} already exists, loading it")
                try:
                    index = client.load_index(index_name=index_name, index_key=key_list)
                    cls._indexes[index_name] = index
                    cls._index_keys[index_name] = key_list
                    return index_name
                except Exception as load_err:
                    logger.error(f"Failed to load existing index {index_name}: {load_err}")
                    raise load_err
            
            logger.error(f"Failed to create index {index_name}: {e}")
            raise e

    @classmethod
    def delete_tenant_index(cls, tenant_id: str):
        """Delete a tenant's encrypted index"""
        client = cls.get_client()
        index_name = f"tenant_{tenant_id}"
        
        try:
            logger.info(f"Deleting CyborgDB index: {index_name}")
            client.delete_index(index_name)
            
            # Clean up local references
            if index_name in cls._indexes:
                del cls._indexes[index_name]
            if index_name in cls._index_keys:
                del cls._index_keys[index_name]
                
            logger.info(f"Index {index_name} deleted successfully")
            
        except Exception as e:
            logger.error(f"Failed to delete index {index_name}: {e}")
            if "not found" not in str(e).lower():
                raise e

    @classmethod
    def upsert_vectors(cls, tenant_id: str, vectors: list, index_key: list = None) -> int:
        """
        Upsert encrypted vectors to the tenant's index.
        
        Args:
            tenant_id: Tenant UUID
            vectors: List of dicts [{"id": str, "vector": list[float], "metadata": dict}]
            index_key: 32-element list encryption key for the index (list of int 0-255)
            
        Returns:
            Number of vectors upserted
        """
        index_name = f"tenant_{tenant_id}"
        
        try:
            # Get or create index
            if index_name not in cls._indexes:
                logger.warning(f"Index {index_name} not found, creating new one")
                cls.create_tenant_index(tenant_id, key=index_key)
            
            index = cls._indexes[index_name]
            
            # Convert to CyborgDB format: {"id": str, "vector": list, "contents": str or bytes}
            import json
            items = []
            for v in vectors:
                metadata = v.get("metadata", {})
                # Convert metadata dict to JSON string for contents field
                contents = json.dumps(metadata) if isinstance(metadata, dict) else str(metadata)
                item = {
                    "id": v["id"],
                    "vector": v["vector"],  # Use "vector" key from input
                    "contents": contents
                }
                items.append(item)
            
            logger.info(f"Upserting {len(items)} vectors to {index_name}")
            
            # Upsert to CyborgDB
            index.upsert(items)
            logger.debug(f"Upserted {len(items)} vectors to {index_name}")
            return len(items)
            
        except Exception as e:
            logger.error(f"Failed to upsert vectors to {index_name}: {e}")
            raise e

    @classmethod
    def search(cls, tenant_id: str, query_vector: list, top_k: int = 10, index_key: bytes = None) -> list:
        """
        Search the tenant's encrypted index.
        
        Args:
            tenant_id: Tenant UUID
            query_vector: Query vector as list of floats (384-dimensional for sentence-transformers)
            top_k: Number of results to return
            index_key: 32-byte encryption key for the index (bytes)
            
        Returns:
            List of search results with metadata
        """
        index_name = f"tenant_{tenant_id}"
        
        try:
            # Check if index exists in memory
            if index_name not in cls._indexes:
                logger.info(f"Index {index_name} not in memory, attempting to load from persistent storage")
                client = cls.get_client()
                try:
                    # Try to load the index from persistent backing store
                    # For PostgreSQL, the index is saved and can be reloaded
                    key = index_key or cls._index_keys.get(index_name)
                    if not key:
                        logger.warning(f"No encryption key available for {index_name}")
                        # Try without key (for unencrypted indexes)
                        try:
                            index = client.load_index(index_name=index_name)
                            cls._indexes[index_name] = index
                            logger.info(f"Loaded index {index_name} from persistent storage (unencrypted)")
                        except Exception:
                            logger.warning(f"Failed to load unencrypted index {index_name} - returning empty results")
                            return []
                    else:
                        index = client.load_index(index_name=index_name, index_key=key)
                        cls._indexes[index_name] = index
                        cls._index_keys[index_name] = key
                        logger.info(f"Loaded index {index_name} from persistent storage")
                except Exception as load_err:
                    logger.warning(f"Failed to load index {index_name}: {load_err} - returning empty results")
                    return []
            
            index = cls._indexes[index_name]
            
            # Perform encrypted search
            # CyborgDB expects query_vectors as List[List[float]] (2D array)
            # Input query_vector is List[float] (1D array), so wrap it
            if not isinstance(query_vector[0], list):
                query_vectors = [query_vector]  # Wrap 1D list into 2D
            else:
                query_vectors = query_vector  # Already 2D
            
            results = index.query(query_vectors=query_vectors, top_k=top_k)
            
            # Convert CyborgDB results to expected format
            import json
            formatted_results = []
            for result in results:
                # Parse contents JSON string back to dict
                contents = result.get("contents", "{}")
                metadata = json.loads(contents) if isinstance(contents, str) else contents
                formatted_results.append({
                    "id": result["id"],
                    "score": 1.0 / (1.0 + result.get("distance", 0)),  # Convert distance to similarity
                    "metadata": metadata
                })
            
            logger.debug(f"CyborgDB search returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed for {index_name}: {e}")
            raise e


# Global access (compatibility)
def get_cyborg_client():
    """Get the CyborgDB client"""
    return CyborgDBManager.get_client()
