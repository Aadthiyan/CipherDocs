"""
Vector encryption and decryption logic.
Handles serialization and encryption of embedding vectors.
"""

import logging
import json
import numpy as np
from typing import List, Union
from cryptography.fernet import Fernet
import base64

logger = logging.getLogger(__name__)

class VectorEncryptor:
    """
    Handles encryption and decryption of vector embeddings.
    """
    
    @staticmethod
    def encrypt_vector(vector: List[float], key: str) -> str:
        """
        Encrypt a single vector embedding.
        
        Args:
            vector: List of floats (embedding)
            key: Tenant encryption key (Fernet base64 string)
            
        Returns:
            Encrypted string (Fernet token)
        """
        try:
            # Serialize: float32 numpy array -> bytes
            # float32 is standard for embeddings (384 * 4 bytes = 1536 bytes)
            # much deeper than JSON text
            arr = np.array(vector, dtype=np.float32)
            data = arr.tobytes()
            
            f = Fernet(key)
            token = f.encrypt(data)
            return token.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Vector encryption failed: {e}")
            raise ValueError("Failed to encrypt vector") from e

    @staticmethod
    def decrypt_vector(encrypted_data: str, key: str) -> List[float]:
        """
        Decrypt a single vector embedding.
        
        Args:
            encrypted_data: Encrypted Fernet token string
            key: Tenant encryption key
            
        Returns:
            List of floats
        """
        try:
            f = Fernet(key)
            data = f.decrypt(encrypted_data.encode('utf-8'))
            
            # Deserialize
            arr = np.frombuffer(data, dtype=np.float32)
            return arr.tolist()
            
        except Exception as e:
            logger.error(f"Vector decryption failed: {e}")
            raise ValueError("Failed to decrypt vector") from e

    @staticmethod
    def batch_encrypt(vectors: List[List[float]], key: str) -> List[str]:
        """
        Encrypt a batch of vectors efficiently.
        """
        # Fernet init is cheap, but we can reuse the instance
        try:
            f = Fernet(key)
            encrypted_batch = []
            
            for vector in vectors:
                arr = np.array(vector, dtype=np.float32)
                data = arr.tobytes()
                token = f.encrypt(data)
                encrypted_batch.append(token.decode('utf-8'))
                
            return encrypted_batch
            
        except Exception as e:
            logger.error(f"Batch encryption failed: {e}")
            raise e

    @staticmethod
    def batch_decrypt(encrypted_vectors: List[str], key: str) -> List[List[float]]:
        """
        Decrypt a batch of vectors efficiently.
        """
        try:
            f = Fernet(key)
            decrypted_batch = []
            
            for token in encrypted_vectors:
                data = f.decrypt(token.encode('utf-8'))
                arr = np.frombuffer(data, dtype=np.float32)
                decrypted_batch.append(arr.tolist())
                
            return decrypted_batch
            
        except Exception as e:
            logger.error(f"Batch decryption failed: {e}")
            raise e
