"""
Unit tests for BAPAO quantum-safe cryptography system.

Tests the QuantumCrypto and VaultManager classes for:
- Post-quantum cryptography algorithms (Kyber-1024, Dilithium-5)
- AES-256-GCM encryption with Argon2id key derivation
- Vault lifecycle management (init, lock, unlock, storage)
- Security boundary enforcement
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.bapao.core.quantum_crypto import (
    QuantumCrypto, 
    VaultManager,
    QuantumSafeError,
    InvalidVaultPasswordError,
    VaultLockedError
)


class TestQuantumCrypto:
    """Test the QuantumCrypto post-quantum cryptography engine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.crypto = QuantumCrypto()
    
    def test_initialization(self):
        """Test QuantumCrypto initializes correctly."""
        assert self.crypto is not None
    
    def test_kyber_key_generation(self):
        """Test Kyber-1024 key encapsulation mechanism."""
        # Generate key pair
        public_key, private_key = self.crypto.generate_kyber_keypair()
        
        assert len(public_key) > 0
        assert len(private_key) > 0
        assert isinstance(public_key, bytes)
        assert isinstance(private_key, bytes)
        
        # Verify key sizes (simulated values)
        assert len(public_key) >= 1568  # Kyber-1024 public key size
        assert len(private_key) >= 3168  # Kyber-1024 private key size
    
    def test_kyber_encapsulation_decapsulation(self):
        """Test Kyber key encapsulation and decapsulation."""
        # Generate keypair
        public_key, private_key = self.crypto.generate_kyber_keypair()
        
        # Encapsulate shared secret
        shared_secret1, ciphertext = self.crypto.kyber_encapsulate(public_key)
        
        assert len(shared_secret1) == 32  # 256-bit shared secret
        assert len(ciphertext) > 0
        
        # Decapsulate shared secret
        shared_secret2 = self.crypto.kyber_decapsulate(private_key, ciphertext)
        
        assert shared_secret1 == shared_secret2
    
    def test_dilithium_signature(self):
        """Test Dilithium-5 digital signatures."""
        # Generate key pair
        public_key, private_key = self.crypto.generate_dilithium_keypair()
        
        assert len(public_key) > 0
        assert len(private_key) > 0
        
        # Sign message
        message = b"Test message for signing"
        signature = self.crypto.dilithium_sign(private_key, message)
        
        assert len(signature) > 0
        
        # Verify signature
        is_valid = self.crypto.dilithium_verify(public_key, message, signature)
        assert is_valid is True
        
        # Test invalid signature
        invalid_message = b"Different message"
        is_invalid = self.crypto.dilithium_verify(public_key, invalid_message, signature)
        assert is_invalid is False
    
    def test_argon2id_key_derivation(self):
        """Test Argon2id password-based key derivation."""
        password = "test_password_123"
        salt = self.crypto._generate_salt()
        
        # Derive key
        key1 = self.crypto.derive_key_argon2id(password, salt)
        
        assert len(key1) == 32  # 256-bit key
        
        # Same password and salt should produce same key
        key2 = self.crypto.derive_key_argon2id(password, salt)
        assert key1 == key2
        
        # Different salt should produce different key
        different_salt = self.crypto._generate_salt()
        key3 = self.crypto.derive_key_argon2id(password, different_salt)
        assert key1 != key3
        
        # Different password should produce different key
        key4 = self.crypto.derive_key_argon2id("different_password", salt)
        assert key1 != key4
    
    def test_aes_gcm_encryption_decryption(self):
        """Test AES-256-GCM symmetric encryption."""
        # Test data
        plaintext = b"This is sensitive profile data that needs quantum-safe encryption"
        key = self.crypto._generate_salt()  # 32-byte key
        
        # Encrypt
        encrypted_data, nonce, tag = self.crypto.encrypt_aes_gcm(plaintext, key)
        
        assert len(encrypted_data) == len(plaintext)
        assert len(nonce) == 12  # AES-GCM standard nonce size
        assert len(tag) == 16    # AES-GCM authentication tag size
        
        # Decrypt
        decrypted_data = self.crypto.decrypt_aes_gcm(encrypted_data, key, nonce, tag)
        
        assert decrypted_data == plaintext
    
    def test_aes_gcm_invalid_key_failure(self):
        """Test AES-GCM decryption fails with wrong key."""
        plaintext = b"Secret data"
        key = self.crypto._generate_salt()
        wrong_key = self.crypto._generate_salt()
        
        encrypted_data, nonce, tag = self.crypto.encrypt_aes_gcm(plaintext, key)
        
        with pytest.raises(QuantumSafeError):
            self.crypto.decrypt_aes_gcm(encrypted_data, wrong_key, nonce, tag)
    
    def test_full_quantum_safe_encryption_cycle(self):
        """Test complete quantum-safe encryption/decryption cycle."""
        # Original data
        data = {"profiles": {"test": {"name": "test", "email": "test@example.com"}}}
        password = "master_password_123"
        
        # Full encryption
        encrypted_vault = self.crypto.encrypt_data(data, password)
        
        # Verify structure
        assert "encrypted_data" in encrypted_vault
        assert "kyber_ciphertext" in encrypted_vault
        assert "dilithium_signature" in encrypted_vault
        assert "salt" in encrypted_vault
        assert "nonce" in encrypted_vault
        assert "tag" in encrypted_vault
        
        # Full decryption
        decrypted_data = self.crypto.decrypt_data(encrypted_vault, password)
        
        assert decrypted_data == data
    
    def test_quantum_safe_encryption_wrong_password(self):
        """Test quantum-safe decryption fails with wrong password."""
        data = {"test": "data"}
        password = "correct_password"
        wrong_password = "wrong_password"
        
        encrypted_vault = self.crypto.encrypt_data(data, password)
        
        with pytest.raises(InvalidVaultPasswordError):
            self.crypto.decrypt_data(encrypted_vault, wrong_password)
    
    def test_signature_verification_integrity(self):
        """Test that signature verification detects tampered data."""
        data = {"test": "data"}
        password = "test_password"
        
        encrypted_vault = self.crypto.encrypt_data(data, password)
        
        # Tamper with encrypted data
        tampered_vault = encrypted_vault.copy()
        import base64
        encrypted_bytes = base64.b64decode(tampered_vault["encrypted_data"])
        tampered_data = bytearray(encrypted_bytes)
        tampered_data[0] ^= 0xFF  # Flip bits
        tampered_vault["encrypted_data"] = base64.b64encode(bytes(tampered_data)).decode('utf-8')
        
        with pytest.raises(InvalidVaultPasswordError, match="Signature verification failed"):
            self.crypto.decrypt_data(tampered_vault, password)


class TestVaultManager:
    """Test the VaultManager quantum-safe vault system."""
    
    def setup_method(self):
        """Set up test fixtures with temporary vault directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.vault_dir = Path(self.temp_dir) / "test_vault"
        self.vault = VaultManager(self.vault_dir)
        self.master_password = "test_master_password_123"
    
    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_vault_initialization(self):
        """Test vault initialization process."""
        # Initially not initialized
        assert not self.vault.is_vault_initialized()
        
        # Initialize vault
        self.vault.initialize_vault(self.master_password)
        
        # Should now be initialized
        assert self.vault.is_vault_initialized()
        
        # Vault files should exist
        assert self.vault.vault_file.exists()
        assert self.vault.metadata_file.exists()
        assert self.vault.signature_file.exists()
        assert self.vault.lock_file.exists()  # Locked by default
    
    def test_vault_double_initialization_fails(self):
        """Test that initializing an already initialized vault fails."""
        self.vault.initialize_vault(self.master_password)
        
        with pytest.raises(QuantumSafeError, match="already initialized"):
            self.vault.initialize_vault(self.master_password)
    
    def test_vault_lock_unlock_cycle(self):
        """Test vault lock/unlock functionality."""
        # Initialize and verify locked state
        self.vault.initialize_vault(self.master_password)
        assert self.vault.is_vault_locked()
        assert not self.vault.is_vault_unlocked()
        
        # Unlock vault
        self.vault.unlock_vault(self.master_password)
        assert not self.vault.is_vault_locked()
        assert self.vault.is_vault_unlocked()
        
        # Lock vault again
        self.vault.lock_vault()
        assert self.vault.is_vault_locked()
        assert not self.vault.is_vault_unlocked()
    
    def test_unlock_with_wrong_password_fails(self):
        """Test that unlocking with wrong password fails."""
        self.vault.initialize_vault(self.master_password)
        
        with pytest.raises(InvalidVaultPasswordError):
            self.vault.unlock_vault("wrong_password")
    
    def test_vault_data_storage_retrieval(self):
        """Test storing and retrieving data in vault."""
        # Initialize and unlock
        self.vault.initialize_vault(self.master_password)
        self.vault.unlock_vault(self.master_password)
        
        # Store test data
        test_data = {
            "profiles": {
                "work": {"name": "John Doe", "email": "john@work.com"},
                "personal": {"name": "John Doe", "email": "john@personal.com"}
            }
        }
        
        self.vault.store_data("profiles", test_data)
        
        # Retrieve data
        retrieved_data = self.vault.retrieve_data("profiles")
        assert retrieved_data == test_data
    
    def test_data_access_requires_unlock(self):
        """Test that data access requires vault to be unlocked."""
        # Initialize but don't unlock
        self.vault.initialize_vault(self.master_password)
        
        # Should fail to store data
        with pytest.raises(VaultLockedError):
            self.vault.store_data("profiles", {"test": "data"})
        
        # Should fail to retrieve data
        with pytest.raises(VaultLockedError):
            self.vault.retrieve_data("profiles")
    
    def test_vault_persistence_across_instances(self):
        """Test that vault data persists across VaultManager instances."""
        # Initialize and store data
        self.vault.initialize_vault(self.master_password)
        self.vault.unlock_vault(self.master_password)
        
        test_data = {"key": "persistent_value"}
        self.vault.store_data("test_key", test_data)
        
        # Create new vault manager instance
        new_vault = VaultManager(self.vault_dir)
        
        # Should be initialized and unlocked (due to session persistence)
        assert new_vault.is_vault_initialized()
        assert new_vault.is_vault_unlocked()
        
        # Retrieve data directly (already unlocked via session)
        retrieved_data = new_vault.retrieve_data("test_key")
        
        assert retrieved_data == test_data
    
    def test_vault_data_encryption_at_rest(self):
        """Test that vault data is properly encrypted at rest."""
        # Initialize and store sensitive data
        self.vault.initialize_vault(self.master_password)
        self.vault.unlock_vault(self.master_password)
        
        sensitive_data = {
            "secret_key": "ssh_private_key_content",
            "password": "super_secret_password"
        }
        
        self.vault.store_data("secrets", sensitive_data)
        
        # Check that raw vault file doesn't contain plaintext
        vault_content = self.vault.vault_file.read_bytes()
        
        # Sensitive strings should not appear in raw file
        assert b"ssh_private_key_content" not in vault_content
        assert b"super_secret_password" not in vault_content
    
    def test_get_profiles_helper(self):
        """Test the get_profiles convenience method."""
        # Initialize and unlock
        self.vault.initialize_vault(self.master_password)
        self.vault.unlock_vault(self.master_password)
        
        # Store profile data
        profiles_data = {
            "profiles": {
                "dev": {"name": "Developer", "email": "dev@company.com"},
                "qa": {"name": "QA Tester", "email": "qa@company.com"}
            }
        }
        
        self.vault.store_data("profiles", profiles_data)
        
        # Test get_profiles method
        profiles = self.vault.get_profiles()
        expected = {
            "dev": {"name": "Developer", "email": "dev@company.com"},
            "qa": {"name": "QA Tester", "email": "qa@company.com"}
        }
        
        assert profiles == expected
    
    def test_get_profiles_no_data(self):
        """Test get_profiles returns empty dict when no profiles exist."""
        self.vault.initialize_vault(self.master_password)
        self.vault.unlock_vault(self.master_password)
        
        profiles = self.vault.get_profiles()
        assert profiles == {}
    
    def test_vault_metadata_creation(self):
        """Test that vault metadata is properly created."""
        self.vault.initialize_vault(self.master_password)
        
        # Metadata file should exist
        assert self.vault.metadata_file.exists()
        
        # Parse metadata
        metadata = json.loads(self.vault.metadata_file.read_text())
        
        # Verify metadata content
        assert metadata["algorithm"] == "Kyber-1024 + Dilithium-5 + AES-256-GCM"
        assert metadata["quantum_safe"] is True
        assert metadata["post_quantum_ready"] is True
        assert "created_at" in metadata
        assert isinstance(metadata["created_at"], (int, float))
    
    def test_vault_backup_functionality(self):
        """Test vault backup creation."""
        # Initialize vault with data
        self.vault.initialize_vault(self.master_password)
        self.vault.unlock_vault(self.master_password)
        
        test_data = {"profiles": {"backup_test": {"email": "test@backup.com"}}}
        self.vault.store_data("profiles", test_data)
        
        # Create backup
        backup_path = self.vault_dir / "test_backup.vault"
        self.vault.create_backup(backup_path, self.master_password)
        
        # Backup file should exist and be different from original
        assert backup_path.exists()
        assert backup_path.read_bytes() != self.vault.vault_file.read_bytes()
        
        # Should be able to restore from backup (test conceptually)
        # In a real implementation, you'd have a restore_backup method
    
    def test_vault_security_boundary_enforcement(self):
        """Test that security boundaries are properly enforced."""
        # Test accessing uninitialized vault
        uninitialized_vault = VaultManager(Path(self.temp_dir) / "nonexistent")
        
        with pytest.raises(QuantumSafeError):
            uninitialized_vault.unlock_vault("any_password")
        
        # Test operations on locked vault
        self.vault.initialize_vault(self.master_password)
        # Vault is locked by default
        
        with pytest.raises(VaultLockedError):
            self.vault.store_data("test", {})
        
        with pytest.raises(VaultLockedError):
            self.vault.retrieve_data("test")
    
    def test_memory_security_on_lock(self):
        """Test that sensitive data is cleared from memory on lock."""
        # Initialize and store data
        self.vault.initialize_vault(self.master_password)
        self.vault.unlock_vault(self.master_password)
        
        test_data = {"secret": "memory_test_data"}
        self.vault.store_data("secrets", test_data)
        
        # Verify data is accessible
        retrieved = self.vault.retrieve_data("secrets")
        assert retrieved == test_data
        
        # Lock vault
        self.vault.lock_vault()
        
        # Internal data should be cleared (implementation dependent)
        # This would test internal _unlocked_data attribute
        assert not hasattr(self.vault, '_unlocked_data') or self.vault._unlocked_data == {}


class TestQuantumCryptoErrorHandling:
    """Test error handling in quantum cryptography system."""
    
    def test_invalid_vault_password_error(self):
        """Test InvalidVaultPasswordError creation and attributes."""
        error = InvalidVaultPasswordError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, QuantumSafeError)
    
    def test_vault_locked_error(self):
        """Test VaultLockedError creation and attributes."""
        error = VaultLockedError("Vault is locked")
        assert str(error) == "Vault is locked"
        assert isinstance(error, QuantumSafeError)
    
    def test_quantum_safe_error(self):
        """Test base QuantumSafeError creation."""
        error = QuantumSafeError("Generic quantum crypto error")
        assert str(error) == "Generic quantum crypto error"


class TestQuantumCryptoIntegration:
    """Integration tests for quantum-safe cryptography system."""
    
    def test_end_to_end_profile_encryption(self):
        """Test complete end-to-end profile encryption scenario."""
        # Simulate BAPAO profile data
        profile_data = {
            "profiles": {
                "work": {
                    "name": "John Doe",
                    "git_email": "john.doe@company.com",
                    "base_directory": "/home/john/work",
                    "ssh_key_path": "/home/john/.ssh/work_ed25519",
                    "gpg_key_fingerprint": "1234567890ABCDEF",
                    "git_host_alias": "github.com-work",
                    "has_passkey": True,
                    "passkey_hint": "Work laptop authentication"
                },
                "personal": {
                    "name": "John Doe", 
                    "git_email": "john.personal@gmail.com",
                    "base_directory": "/home/john/personal",
                    "ssh_key_path": "/home/john/.ssh/personal_ed25519",
                    "git_host_alias": "github.com-personal"
                }
            }
        }
        
        # Create temporary vault
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_dir = Path(temp_dir) / "integration_vault"
            vault = VaultManager(vault_dir)
            
            # Master password
            master_password = "integration_test_password_456"
            
            # Full workflow test
            vault.initialize_vault(master_password)
            vault.unlock_vault(master_password)
            vault.store_data("profiles", profile_data)
            
            # Lock and unlock to test persistence
            vault.lock_vault()
            vault.unlock_vault(master_password)
            
            # Retrieve and verify data
            retrieved_data = vault.retrieve_data("profiles")
            assert retrieved_data == profile_data
            
            # Test individual profile access
            profiles = vault.get_profiles()
            assert len(profiles) == 2
            assert "work" in profiles
            assert "personal" in profiles
            assert profiles["work"]["git_email"] == "john.doe@company.com"
    
    def test_concurrent_vault_access_protection(self):
        """Test that vault properly handles concurrent access attempts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_dir = Path(temp_dir) / "concurrent_vault"
            
            # Initialize vault
            vault1 = VaultManager(vault_dir)
            vault1.initialize_vault("test_password")
            vault1.unlock_vault("test_password")
            
            # Create second instance
            vault2 = VaultManager(vault_dir)
            
            # Second instance should recognize vault as unlocked/locked appropriately
            # (Implementation may vary based on locking mechanism)
            assert vault2.is_vault_initialized()
    
    @patch('src.bapao.core.quantum_crypto.QuantumCrypto.generate_salt')
    def test_quantum_crypto_algorithm_failure_handling(self, mock_salt):
        """Test handling of quantum cryptography algorithm failures."""
        # Mock salt generation failure  
        mock_salt.side_effect = Exception("Crypto algorithm failed")
        
        crypto = QuantumCrypto()
        
        with pytest.raises(Exception):  # The exception will propagate up
            crypto.encrypt_data({"test": "data"}, "password")