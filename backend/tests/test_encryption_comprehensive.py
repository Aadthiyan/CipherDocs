"""
Comprehensive tests for encryption module.
Tests key management, encryption/decryption, key fingerprinting, and edge cases.
Coverage: Key generation, encryption, decryption, key storage, caching, rotation.
"""

import pytest
import uuid
import base64
import hashlib
from cryptography.fernet import Fernet
from unittest.mock import MagicMock, patch, Mock
import time

from app.core.encryption import KeyManager
from app.models.database import EncryptionKey
from app.core.config import settings


# Test fixtures
@pytest.fixture
def test_master_key():
    """Generate a valid test master key"""
    return Fernet.generate_key().decode('utf-8')


@pytest.fixture
def mock_settings(test_master_key):
    """Mock configuration with test master key"""
    with patch("app.core.encryption.settings") as mock_config:
        mock_config.MASTER_ENCRYPTION_KEY = test_master_key
        yield mock_config


# ============================================================================
# Key Generation Tests
# ============================================================================

class TestKeyGeneration:
    """Test random key generation"""
    
    def test_generate_key_returns_string(self):
        """generate_key should return a string"""
        key = KeyManager.generate_key()
        assert isinstance(key, str)
        assert len(key) > 0
    
    def test_generate_key_valid_fernet_key(self):
        """Generated key should be a valid Fernet key"""
        key = KeyManager.generate_key()
        # Should not raise exception
        f = Fernet(key)
        assert f is not None
    
    def test_generate_key_correct_length(self):
        """Generated key should be correct length (32 bytes base64)"""
        key = KeyManager.generate_key()
        # Fernet keys are 32 bytes, base64 encoded (44 chars with padding)
        decoded = base64.urlsafe_b64decode(key)
        assert len(decoded) == 32
    
    def test_generate_key_randomness(self):
        """Multiple keys should be different"""
        key1 = KeyManager.generate_key()
        key2 = KeyManager.generate_key()
        key3 = KeyManager.generate_key()
        
        assert key1 != key2
        assert key2 != key3
        assert key1 != key3
    
    def test_generate_key_multiple_times(self):
        """Should generate multiple keys without issue"""
        keys = [KeyManager.generate_key() for _ in range(100)]
        # All should be unique
        assert len(set(keys)) == 100


# ============================================================================
# Key Encryption/Decryption Tests
# ============================================================================

class TestKeyEncryptionDecryption:
    """Test master key wrapping (encryption/decryption of tenant keys)"""
    
    def test_encrypt_key_returns_string(self, mock_settings):
        """encrypt_key should return an encrypted string"""
        tenant_key = KeyManager.generate_key()
        encrypted = KeyManager.encrypt_key(tenant_key)
        
        assert isinstance(encrypted, str)
        assert len(encrypted) > 0
        assert encrypted != tenant_key
    
    def test_encrypt_key_different_ciphertexts(self, mock_settings):
        """Same key encrypted multiple times should produce different ciphertexts"""
        tenant_key = KeyManager.generate_key()
        
        encrypted1 = KeyManager.encrypt_key(tenant_key)
        encrypted2 = KeyManager.encrypt_key(tenant_key)
        
        # Fernet includes timestamp, so ciphertexts differ
        assert encrypted1 != encrypted2
    
    def test_decrypt_key_returns_original(self, mock_settings):
        """decrypt_key should return original key"""
        original_key = KeyManager.generate_key()
        encrypted = KeyManager.encrypt_key(original_key)
        decrypted = KeyManager.decrypt_key(encrypted)
        
        assert decrypted == original_key
    
    def test_encrypt_decrypt_roundtrip(self, mock_settings):
        """Multiple encrypt/decrypt rounds should work"""
        original = KeyManager.generate_key()
        
        encrypted1 = KeyManager.encrypt_key(original)
        decrypted1 = KeyManager.decrypt_key(encrypted1)
        encrypted2 = KeyManager.encrypt_key(decrypted1)
        decrypted2 = KeyManager.decrypt_key(encrypted2)
        
        assert decrypted1 == original
        assert decrypted2 == original
    
    def test_decrypt_invalid_encrypted_key_raises(self, mock_settings):
        """Decrypting invalid data should raise"""
        with pytest.raises(Exception):
            KeyManager.decrypt_key("invalid_encrypted_key")
    
    def test_decrypt_tampered_key_raises(self, mock_settings):
        """Decrypting tampered data should raise"""
        original_key = KeyManager.generate_key()
        encrypted = KeyManager.encrypt_key(original_key)
        
        # Tamper with encrypted value
        tampered = encrypted[:-10] + "xxxxxxxxxx"
        
        with pytest.raises(Exception):
            KeyManager.decrypt_key(tampered)


# ============================================================================
# Key Fingerprinting Tests
# ============================================================================

class TestKeyFingerprinting:
    """Test key fingerprint generation"""
    
    def test_get_fingerprint_returns_string(self):
        """get_fingerprint should return a string"""
        key = "test_key"
        fp = KeyManager.get_fingerprint(key)
        
        assert isinstance(fp, str)
        assert len(fp) > 0
    
    def test_get_fingerprint_sha256_format(self):
        """Fingerprint should be SHA256 hex digest (64 chars)"""
        key = "test_key"
        fp = KeyManager.get_fingerprint(key)
        
        # SHA256 hex digest is 64 characters
        assert len(fp) == 64
        # Should be hexadecimal
        int(fp, 16)  # Should not raise
    
    def test_get_fingerprint_deterministic(self):
        """Same key should always produce same fingerprint"""
        key = "consistent_key"
        
        fp1 = KeyManager.get_fingerprint(key)
        fp2 = KeyManager.get_fingerprint(key)
        fp3 = KeyManager.get_fingerprint(key)
        
        assert fp1 == fp2 == fp3
    
    def test_get_fingerprint_different_keys(self):
        """Different keys should produce different fingerprints"""
        key1 = "key_one"
        key2 = "key_two"
        
        fp1 = KeyManager.get_fingerprint(key1)
        fp2 = KeyManager.get_fingerprint(key2)
        
        assert fp1 != fp2
    
    def test_get_fingerprint_matches_sha256(self):
        """Fingerprint should match manual SHA256 calculation"""
        key = "test_key"
        fp = KeyManager.get_fingerprint(key)
        
        expected = hashlib.sha256(key.encode()).hexdigest()
        assert fp == expected
    
    def test_get_fingerprint_unicode_key(self):
        """Should handle unicode keys"""
        key = "ключ_🔐_clé"
        fp = KeyManager.get_fingerprint(key)
        
        assert len(fp) == 64
        assert isinstance(fp, str)


# ============================================================================
# Database Key Creation Tests
# ============================================================================

class TestDatabaseKeyCreation:
    """Test creation and storage of encryption keys in database"""
    
    def test_create_tenant_key_returns_tuple(self, mock_settings, db_session):
        """create_tenant_key should return (EncryptionKey, raw_key)"""
        tenant_id = uuid.uuid4()
        
        db_key, raw_key = KeyManager.create_tenant_key(db_session, tenant_id)
        
        assert isinstance(db_key, EncryptionKey)
        assert isinstance(raw_key, str)
    
    def test_create_tenant_key_stores_in_db(self, mock_settings, db_session):
        """create_tenant_key should save to database"""
        tenant_id = uuid.uuid4()
        
        db_key, raw_key = KeyManager.create_tenant_key(db_session, tenant_id)
        
        # Should be queryable
        saved = db_session.query(EncryptionKey).filter_by(
            tenant_id=tenant_id
        ).first()
        assert saved is not None
        assert saved.id == db_key.id
    
    def test_create_tenant_key_has_fingerprint(self, mock_settings, db_session):
        """Created key should have fingerprint"""
        tenant_id = uuid.uuid4()
        
        db_key, raw_key = KeyManager.create_tenant_key(db_session, tenant_id)
        
        assert db_key.key_fingerprint is not None
        assert len(db_key.key_fingerprint) == 64
        # Should match the raw key
        expected_fp = KeyManager.get_fingerprint(raw_key)
        assert db_key.key_fingerprint == expected_fp
    
    def test_create_tenant_key_encrypted(self, mock_settings, db_session):
        """Created key should be encrypted in database"""
        tenant_id = uuid.uuid4()
        
        db_key, raw_key = KeyManager.create_tenant_key(db_session, tenant_id)
        
        assert db_key.encrypted_key is not None
        # Encrypted key should differ from raw key
        assert db_key.encrypted_key != raw_key
        # Should be decryptable
        decrypted = KeyManager.decrypt_key(db_key.encrypted_key)
        assert decrypted == raw_key
    
    def test_create_tenant_key_active_flag(self, mock_settings, db_session):
        """New key should be marked as active"""
        tenant_id = uuid.uuid4()
        
        db_key, _ = KeyManager.create_tenant_key(db_session, tenant_id)
        
        assert db_key.is_active is True
    
    def test_create_tenant_key_has_id(self, mock_settings, db_session):
        """Created key should have UUID id"""
        tenant_id = uuid.uuid4()
        
        db_key, _ = KeyManager.create_tenant_key(db_session, tenant_id)
        
        assert db_key.id is not None
        assert isinstance(db_key.id, uuid.UUID)
    
    def test_create_tenant_key_without_commit(self, mock_settings, db_session):
        """create_tenant_key with commit=False should not persist"""
        tenant_id = uuid.uuid4()
        
        db_key, _ = KeyManager.create_tenant_key(
            db_session, tenant_id, commit=False
        )
        
        # Key should be in session but not yet persisted
        assert db_key in db_session.new or db_key in db_session.identity_map.values()


# ============================================================================
# Key Retrieval and Caching Tests
# ============================================================================

class TestKeyRetrieval:
    """Test retrieval of tenant keys"""
    
    def test_get_tenant_key_retrieves_from_db(self, mock_settings, db_session):
        """get_tenant_key should retrieve from database"""
        tenant_id = uuid.uuid4()
        
        # Create and commit key
        created_key, original_raw = KeyManager.create_tenant_key(
            db_session, tenant_id, commit=True
        )
        db_session.refresh(created_key)
        
        # Retrieve it
        retrieved_key = KeyManager.get_tenant_key(db_session, tenant_id)
        
        assert retrieved_key == original_raw
    
    def test_get_tenant_key_caching(self, mock_settings, db_session):
        """Multiple calls should use cache"""
        tenant_id = uuid.uuid4()
        
        KeyManager.create_tenant_key(db_session, tenant_id, commit=True)
        
        # First call
        key1 = KeyManager.get_tenant_key(db_session, tenant_id)
        # Second call should use cache
        key2 = KeyManager.get_tenant_key(db_session, tenant_id)
        
        assert key1 == key2
    
    def test_get_tenant_key_nonexistent_raises(self, mock_settings, db_session):
        """Getting nonexistent key should raise"""
        tenant_id = uuid.uuid4()
        
        with pytest.raises(Exception):
            KeyManager.get_tenant_key(db_session, tenant_id)


# ============================================================================
# Multiple Keys Per Tenant Tests
# ============================================================================

class TestMultipleKeysPerTenant:
    """Test key rotation and multiple active keys"""
    
    def test_create_multiple_keys_for_tenant(self, mock_settings, db_session):
        """Can create multiple keys for same tenant"""
        tenant_id = uuid.uuid4()
        
        key1, raw1 = KeyManager.create_tenant_key(db_session, tenant_id)
        db_session.commit()
        
        key2, raw2 = KeyManager.create_tenant_key(db_session, tenant_id)
        db_session.commit()
        
        # Both should exist and be different
        all_keys = db_session.query(EncryptionKey).filter_by(
            tenant_id=tenant_id
        ).all()
        
        assert len(all_keys) == 2
        assert raw1 != raw2
        assert key1.id != key2.id
    
    def test_get_tenant_key_gets_active_key(self, mock_settings, db_session):
        """get_tenant_key should get active key when multiple exist"""
        tenant_id = uuid.uuid4()
        
        key1, raw1 = KeyManager.create_tenant_key(db_session, tenant_id)
        key1.is_active = False
        db_session.commit()
        
        key2, raw2 = KeyManager.create_tenant_key(db_session, tenant_id)
        key2.is_active = True
        db_session.commit()
        
        # Should get the active key
        retrieved = KeyManager.get_tenant_key(db_session, tenant_id)
        assert retrieved == raw2


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

class TestEncryptionEdgeCases:
    """Test edge cases in encryption operations"""
    
    def test_encrypt_empty_string(self, mock_settings):
        """Should handle empty string keys"""
        encrypted = KeyManager.encrypt_key("")
        decrypted = KeyManager.decrypt_key(encrypted)
        assert decrypted == ""
    
    def test_encrypt_very_long_key(self, mock_settings):
        """Should handle very long keys"""
        long_key = "x" * 10000
        encrypted = KeyManager.encrypt_key(long_key)
        decrypted = KeyManager.decrypt_key(encrypted)
        assert decrypted == long_key
    
    def test_fingerprint_empty_string(self):
        """Should handle empty string fingerprinting"""
        fp = KeyManager.get_fingerprint("")
        assert len(fp) == 64
    
    def test_fingerprint_very_long_string(self):
        """Should handle very long string fingerprinting"""
        long_str = "x" * 1000000
        fp = KeyManager.get_fingerprint(long_str)
        assert len(fp) == 64
    
    def test_unicode_in_key_operations(self, mock_settings):
        """Should handle unicode in key operations"""
        unicode_key = "ключ_🔐_clé_κλειδί"
        
        encrypted = KeyManager.encrypt_key(unicode_key)
        decrypted = KeyManager.decrypt_key(encrypted)
        
        assert decrypted == unicode_key


# ============================================================================
# Integration Tests
# ============================================================================

class TestEncryptionIntegration:
    """Integration tests for encryption workflow"""
    
    def test_full_key_lifecycle(self, mock_settings, db_session):
        """Test complete key lifecycle"""
        tenant_id = uuid.uuid4()
        
        # Create key
        db_key, raw_key = KeyManager.create_tenant_key(db_session, tenant_id)
        db_session.commit()
        
        # Retrieve it
        retrieved_key = KeyManager.get_tenant_key(db_session, tenant_id)
        assert retrieved_key == raw_key
        
        # Use for encryption
        plaintext = "sensitive_data"
        f = Fernet(retrieved_key)
        ciphertext = f.encrypt(plaintext.encode())
        
        # Decrypt with retrieved key
        decrypted = f.decrypt(ciphertext).decode()
        assert decrypted == plaintext
    
    def test_multiple_tenants_keys_isolated(self, mock_settings, db_session):
        """Keys for different tenants should be isolated"""
        tenant1 = uuid.uuid4()
        tenant2 = uuid.uuid4()
        
        key1, raw1 = KeyManager.create_tenant_key(db_session, tenant1)
        key2, raw2 = KeyManager.create_tenant_key(db_session, tenant2)
        
        db_session.commit()
        
        # Keys should be different
        assert raw1 != raw2
        
        # Retrieving should get correct keys
        retrieved1 = KeyManager.get_tenant_key(db_session, tenant1)
        retrieved2 = KeyManager.get_tenant_key(db_session, tenant2)
        
        assert retrieved1 == raw1
        assert retrieved2 == raw2
        assert retrieved1 != retrieved2
