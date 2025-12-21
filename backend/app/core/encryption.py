"""
Encryption key management and cryptographic operations.
"""

import base64
import hashlib
import logging
import time
from typing import Optional, Dict, Tuple
from functools import lru_cache

from cryptography.fernet import Fernet
from sqlalchemy.orm import Session
import uuid

from app.core.config import settings
from app.models.database import EncryptionKey, Tenant

logger = logging.getLogger(__name__)

class KeyManager:
    """
    Manages generation, storage, and retrieval of tenant encryption keys.
    """
    
    # Internal cache for decrypted keys: {tenant_id: (key_bytes, expiry_timestamp)}
    _key_cache: Dict[str, Tuple[bytes, float]] = {}
    _cache_ttl: int = 300  # 5 minutes
    
    @staticmethod
    def generate_key() -> str:
        """Generate a new random 32-byte Fernet key (url-safe base64)"""
        return Fernet.generate_key().decode('utf-8')

    @staticmethod
    def get_fingerprint(key: str) -> str:
        """Generate a SHA-256 fingerprint of the key"""
        return hashlib.sha256(key.encode()).hexdigest()

    @staticmethod
    def encrypt_key(tenant_key: str) -> str:
        """
        Encrypt a tenant key using the Master Encryption Key.
        
        Args:
            tenant_key: The plaintext tenant key (base64 string)
            
        Returns:
            Encrypted key string (Fernet token)
        """
        f = Fernet(settings.MASTER_ENCRYPTION_KEY)
        return f.encrypt(tenant_key.encode()).decode('utf-8')

    @staticmethod
    def decrypt_key(encrypted_key: str) -> str:
        """
        Decrypt a tenant key using the Master Encryption Key.
        
        Args:
            encrypted_key: The encrypted key string
            
        Returns:
            Plaintext tenant key (base64 string)
        """
        f = Fernet(settings.MASTER_ENCRYPTION_KEY)
        return f.decrypt(encrypted_key.encode()).decode('utf-8')

    @classmethod
    def create_tenant_key(cls, db: Session, tenant_id: uuid.UUID, commit: bool = True) -> Tuple[EncryptionKey, str]:
        """
        Generate and store a new encryption key for a tenant.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            commit: Whether to commit the transaction
            
        Returns:
            Tuple of (EncryptionKey record, raw_key_string)
        """
        # Generate new key
        raw_key = cls.generate_key()
        
        # Create record
        db_key = EncryptionKey(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            key_fingerprint=cls.get_fingerprint(raw_key),
            encrypted_key=cls.encrypt_key(raw_key),
            is_active=True
        )
        
        db.add(db_key)
        if commit:
            db.commit()
            db.refresh(db_key)
        
        logger.info(f"Created new encryption key for tenant {tenant_id}")
        return db_key, raw_key

    @classmethod
    def get_tenant_key(cls, db: Session, tenant_id: uuid.UUID) -> str:
        """
        Retrieve and decrypt the active key for a tenant.
        Uses caching for performance.
        
        Args:
            db: Database session
            tenant_id: Tenant UUID
            
        Returns:
            Decrypted tenant key (base64 string)
            
        Raises:
            ValueError: If no active key found
        """
        tenant_id_str = str(tenant_id)
        
        # Check cache
        if tenant_id_str in cls._key_cache:
            key, expiry = cls._key_cache[tenant_id_str]
            if time.time() < expiry:
                return key.decode('utf-8')
            else:
                del cls._key_cache[tenant_id_str]
        
        # Fetch from DB
        key_record = db.query(EncryptionKey).filter(
            EncryptionKey.tenant_id == tenant_id,
            EncryptionKey.is_active == True
        ).first()
        
        if not key_record:
            # Auto-generate if missing? Better to raise error to detect issues.
            # But for seamlessness in dev, we might assume it exists if tenant does.
            # Let's enforce it must exist (created at signup).
            logger.error(f"No active encryption key found for tenant {tenant_id}")
            raise ValueError(f"Encryption key not found for tenant {tenant_id}")
            
        # Decrypt
        try:
            plaintext_key = cls.decrypt_key(key_record.encrypted_key)
        except Exception as e:
            logger.critical(f"Failed to decrypt key for tenant {tenant_id}: {e}")
            raise ValueError("Encryption key corruption detected")
            
        # Update cache
        cls._key_cache[tenant_id_str] = (
            plaintext_key.encode('utf-8'), 
            time.time() + cls._cache_ttl
        )
        
        return plaintext_key

    @classmethod
    def clear_cache(cls):
        """Clear the key cache"""
        cls._key_cache.clear()
        
