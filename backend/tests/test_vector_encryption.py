"""
Tests for vector encryption.
"""

import pytest
import numpy as np
from cryptography.fernet import Fernet

from app.core.vector_encryption import VectorEncryptor

@pytest.fixture
def key():
    """Generates a valid Fernet key"""
    return Fernet.generate_key().decode('utf-8')

def test_encrypt_decrypt_cycle(key):
    """Test full encryption and decryption cycle"""
    # Create random vector (dim=384)
    original_vector = np.random.rand(384).astype(np.float32).tolist()
    
    # Encrypt
    encrypted = VectorEncryptor.encrypt_vector(original_vector, key)
    assert isinstance(encrypted, str)
    assert len(encrypted) > 0
    
    # Decrypt
    decrypted = VectorEncryptor.decrypt_vector(encrypted, key)
    
    # Compare (using approx for floats)
    np.testing.assert_allclose(original_vector, decrypted, rtol=1e-5)

def test_encryption_output_format(key):
    """Test that encrypted output is a valid Fernet token structure"""
    vector = [0.1, 0.2, 0.3]
    encrypted = VectorEncryptor.encrypt_vector(vector, key)
    
    # Fernet tokens are base64 encoded strings
    import base64
    decoded = base64.urlsafe_b64decode(encrypted)
    # Check version byte (0x80)
    assert decoded[0] == 0x80

def test_incorrect_key(key):
    """Test decryption with wrong key fails"""
    vector = [1.0, 2.0, 3.0]
    encrypted = VectorEncryptor.encrypt_vector(vector, key)
    
    wrong_key = Fernet.generate_key().decode('utf-8')
    
    with pytest.raises(ValueError, match="Failed to decrypt"):
        VectorEncryptor.decrypt_vector(encrypted, wrong_key)

def test_batch_processing(key):
    """Test batch encryption/decryption"""
    vectors = [
        np.random.rand(10).astype(np.float32).tolist() 
        for _ in range(5)
    ]
    
    # Batch Encrypt
    encrypted_batch = VectorEncryptor.batch_encrypt(vectors, key)
    assert len(encrypted_batch) == 5
    
    # Batch Decrypt
    decrypted_batch = VectorEncryptor.batch_decrypt(encrypted_batch, key)
    assert len(decrypted_batch) == 5
    
    for orig, dec in zip(vectors, decrypted_batch):
        np.testing.assert_allclose(orig, dec, rtol=1e-5)
