"""
Tests for encryption key management.
"""

import pytest
import uuid
import base64
from cryptography.fernet import Fernet
from unittest.mock import MagicMock, patch

from app.core.encryption import KeyManager
from app.models.database import EncryptionKey
from app.core.config import settings

# Mock Master Key for testing
TEST_MASTER_KEY = Fernet.generate_key().decode('utf-8')

@pytest.fixture
def mock_settings():
    """Mock configuration to use test master key"""
    with patch("app.core.encryption.settings") as mock_settings:
        mock_settings.MASTER_ENCRYPTION_KEY = TEST_MASTER_KEY
        yield mock_settings

def test_generate_key():
    """Test random key generation"""
    key = KeyManager.generate_key()
    assert isinstance(key, str)
    # Validate it's a valid Fernet key
    f = Fernet(key)
    assert len(base64.urlsafe_b64decode(key)) == 32

def test_encrypt_decrypt_key(mock_settings):
    """Test master key wrapping"""
    tenant_key = KeyManager.generate_key()
    
    # Encrypt
    encrypted = KeyManager.encrypt_key(tenant_key)
    assert encrypted != tenant_key
    assert isinstance(encrypted, str)
    
    # Decrypt
    decrypted = KeyManager.decrypt_key(encrypted)
    assert decrypted == tenant_key

def test_fingerprint():
    """Test fingerprint generation"""
    key = "some_key"
    fp1 = KeyManager.get_fingerprint(key)
    fp2 = KeyManager.get_fingerprint(key)
    assert fp1 == fp2
    assert len(fp1) == 64 # SHA-256 hex digest

@patch("app.core.encryption.settings")
def test_create_tenant_key(mock_config, db_session):
    """Test database creation logic"""
    # Use real key for testing
    mock_config.MASTER_ENCRYPTION_KEY = TEST_MASTER_KEY
    
    tenant_id = uuid.uuid4()
    
    # Mock DB session
    key = KeyManager.create_tenant_key(db_session, tenant_id, commit=True)
    
    assert key.tenant_id == tenant_id
    assert key.encrypted_key is not None
    assert key.key_fingerprint is not None
    assert key.is_active is True
    
    # Check it was added to DB
    from app.models.database import EncryptionKey
    saved = db_session.query(EncryptionKey).filter_by(tenant_id=tenant_id).first()
    assert saved is not None
    assert saved.id == key.id

@patch("app.core.encryption.settings")
def test_get_tenant_key_caching(mock_config, db_session):
    """Test retrieval and caching"""
    mock_config.MASTER_ENCRYPTION_KEY = TEST_MASTER_KEY
    tenant_id = uuid.uuid4()
    
    # Create key
    KeyManager.create_tenant_key(db_session, tenant_id)
    
    # First fetch - from DB
    key1 = KeyManager.get_tenant_key(db_session, tenant_id)
    assert isinstance(key1, str)
    
    # Check cache was populated
    assert str(tenant_id) in KeyManager._key_cache
    
    # Second fetch - should be cached
    # We can verify it doesn't query DB by mocking the query, but for now just value check
    key2 = KeyManager.get_tenant_key(db_session, tenant_id)
    assert key1 == key2
    
    # Clear cache
    KeyManager.clear_cache()
    assert len(KeyManager._key_cache) == 0
