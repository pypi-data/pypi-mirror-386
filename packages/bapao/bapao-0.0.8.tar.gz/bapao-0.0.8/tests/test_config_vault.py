"""
Unit tests for BAPAO enhanced configuration manager with quantum-safe vault integration.

Tests ConfigManager functionality including:
- Legacy file-based profile storage
- Quantum-safe vault storage integration
- Automatic migration between storage types
- Vault exception handling
- Storage backend selection and fallback
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.bapao.core.config import ConfigManager, Profile
from src.bapao.core.quantum_crypto import (
    VaultManager, 
    VaultLockedError, 
    QuantumSafeError,
    InvalidVaultPasswordError
)


class TestProfile:
    """Test the Profile dataclass."""
    
    def test_profile_creation(self):
        """Test creating a Profile with required fields."""
        profile = Profile(
            name="test_profile",
            git_name="Test User",
            git_email="test@example.com",
            base_directory="/home/test"
        )
        
        assert profile.name == "test_profile"
        assert profile.git_name == "Test User"
        assert profile.git_email == "test@example.com"
        assert profile.base_directory == "/home/test"
        assert profile.ssh_key_path is None
        assert profile.has_passkey is False
    
    def test_profile_to_dict(self):
        """Test converting Profile to dictionary."""
        profile = Profile(
            name="work",
            git_name="John Doe",
            git_email="john@company.com", 
            base_directory="/home/john/work",
            ssh_key_path="/home/john/.ssh/work_ed25519",
            has_passkey=True,
            passkey_hint="Work laptop"
        )
        
        profile_dict = profile.to_dict()
        
        expected = {
            "name": "work",
            "git_name": "John Doe", 
            "git_email": "john@company.com",
            "base_directory": "/home/john/work",
            "ssh_key_path": "/home/john/.ssh/work_ed25519",
            "gpg_key_fingerprint": None,
            "git_host_alias": None,
            "has_passkey": True,
            "passkey_hint": "Work laptop",
            "created_at": None,
            "updated_at": None
        }
        
        assert profile_dict == expected
    
    def test_profile_from_dict(self):
        """Test creating Profile from dictionary."""
        data = {
            "name": "personal",
            "git_name": "Jane Smith",
            "git_email": "jane@personal.com",
            "base_directory": "/home/jane/personal"
        }
        
        profile = Profile.from_dict(data)
        
        assert profile.name == "personal"
        assert profile.git_name == "Jane Smith"
        assert profile.git_email == "jane@personal.com"
        assert profile.base_directory == "/home/jane/personal"


class TestConfigManagerLegacyMode:
    """Test ConfigManager in legacy file-based mode."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "bapao_config"
        self.config = ConfigManager(config_dir=self.config_dir, use_vault=False)
    
    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_config_directory_creation(self):
        """Test that configuration directory is created."""
        assert self.config_dir.exists()
        assert self.config_dir.is_dir()
    
    def test_load_profiles_empty(self):
        """Test loading profiles when no profiles file exists."""
        profiles = self.config.load_profiles()
        assert profiles == {}
    
    def test_save_and_load_profiles(self):
        """Test saving and loading profiles in legacy mode."""
        # Create test profiles
        profile1 = Profile(
            name="work",
            git_name="John Doe", 
            git_email="john@work.com",
            base_directory="/home/john/work"
        )
        
        profile2 = Profile(
            name="personal",
            git_name="John Doe",
            git_email="john@personal.com", 
            base_directory="/home/john/personal"
        )
        
        profiles = {"work": profile1, "personal": profile2}
        
        # Save profiles
        self.config.save_profiles(profiles)
        
        # Verify file was created
        assert self.config.profiles_file.exists()
        
        # Load profiles back
        loaded_profiles = self.config.load_profiles()
        
        assert len(loaded_profiles) == 2
        assert "work" in loaded_profiles
        assert "personal" in loaded_profiles
        
        # Verify profile data
        work_profile = loaded_profiles["work"]
        assert work_profile.name == "work"
        assert work_profile.git_email == "john@work.com"
    
    def test_create_profile(self):
        """Test creating a single profile."""
        profile = Profile(
            name="test",
            git_name="Test User",
            git_email="test@example.com",
            base_directory="/home/test"
        )
        
        self.config.create_profile(profile)
        
        # Verify profile was saved
        loaded_profile = self.config.get_profile("test")
        assert loaded_profile is not None
        assert loaded_profile.name == "test"
        assert loaded_profile.git_email == "test@example.com"
    
    def test_delete_profile(self):
        """Test deleting a profile."""
        # Create profile
        profile = Profile("delete_me", "User", "user@example.com", "/home/user")
        self.config.create_profile(profile)
        
        # Verify it exists
        assert self.config.profile_exists("delete_me")
        
        # Delete it
        result = self.config.delete_profile("delete_me")
        assert result is True
        
        # Verify it's gone
        assert not self.config.profile_exists("delete_me")
        
        # Try to delete non-existent profile
        result = self.config.delete_profile("nonexistent")
        assert result is False
    
    def test_list_profiles(self):
        """Test listing profile names."""
        # Initially empty
        assert self.config.list_profiles() == []
        
        # Add profiles
        profile1 = Profile("alpha", "User1", "user1@example.com", "/home/user1")
        profile2 = Profile("beta", "User2", "user2@example.com", "/home/user2")
        
        self.config.create_profile(profile1)
        self.config.create_profile(profile2)
        
        # Should return sorted list
        profile_names = self.config.list_profiles()
        assert set(profile_names) == {"alpha", "beta"}
    
    def test_malformed_yaml_handling(self):
        """Test handling of malformed YAML files."""
        # Write malformed YAML
        self.config.profiles_file.write_text("invalid: yaml: content: [")
        
        with pytest.raises(ValueError, match="Failed to load"):
            self.config.load_profiles()


class TestConfigManagerVaultMode:
    """Test ConfigManager with quantum-safe vault integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "bapao_config"
        self.vault_dir = self.config_dir
        self.master_password = "test_vault_password_123"
        
        # Initialize vault first
        self.vault = VaultManager(self.vault_dir)
        self.vault.initialize_vault(self.master_password)
        self.vault.unlock_vault(self.master_password)
        
        # Create config manager with vault enabled
        self.config = ConfigManager(config_dir=self.config_dir, use_vault=True)
    
    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_vault_availability_checks(self):
        """Test vault availability detection."""
        assert self.config.is_vault_available()
        assert self.config.is_vault_unlocked()
    
    def test_vault_mode_profile_operations(self):
        """Test profile operations in vault mode."""
        # Create profiles
        profile1 = Profile("vault_work", "Vault User", "vault@work.com", "/home/vault/work")
        profile2 = Profile("vault_personal", "Vault User", "vault@personal.com", "/home/vault/personal")
        
        # Save profiles (should use vault)
        profiles = {"vault_work": profile1, "vault_personal": profile2}
        self.config.save_profiles(profiles)
        
        # Load profiles (should use vault)
        loaded_profiles = self.config.load_profiles()
        
        assert len(loaded_profiles) == 2
        assert "vault_work" in loaded_profiles
        assert loaded_profiles["vault_work"].git_email == "vault@work.com"
    
    def test_vault_locked_error_handling(self):
        """Test handling of VaultLockedError."""
        # Lock the vault
        self.vault.lock_vault()
        
        # Operations should raise VaultLockedError
        with pytest.raises(VaultLockedError):
            self.config.load_profiles()
        
        with pytest.raises(VaultLockedError):
            self.config.save_profiles({})
        
        with pytest.raises(VaultLockedError):
            self.config.get_profile("test")
        
        with pytest.raises(VaultLockedError):
            profile = Profile("test", "Test", "test@example.com", "/home/test")
            self.config.create_profile(profile)
    
    def test_vault_fallback_to_legacy(self):
        """Test fallback to legacy storage when vault fails."""
        # Create config with vault that will fail
        with patch.object(self.config.vault_manager, 'retrieve_data', side_effect=Exception("Vault error")):
            with patch('builtins.print') as mock_print:  # Capture warning message
                
                # Create legacy file for fallback
                legacy_data = {
                    "profiles": {
                        "fallback_profile": {
                            "name": "fallback_profile",
                            "git_name": "Fallback User",
                            "git_email": "fallback@example.com",
                            "base_directory": "/home/fallback"
                        }
                    }
                }
                
                with open(self.config.profiles_file, 'w') as f:
                    yaml.dump(legacy_data, f)
                
                # Should fall back to legacy file
                profiles = self.config.load_profiles()
                
                assert len(profiles) == 1
                assert "fallback_profile" in profiles
                
                # Should have printed warning
                mock_print.assert_called()
                assert "Warning: Vault error, falling back to legacy storage" in str(mock_print.call_args)
    
    def test_storage_status_reporting(self):
        """Test storage status reporting."""
        status = self.config.get_storage_status()
        
        assert status["vault_enabled"] is True
        assert status["vault_available"] is True
        assert status["vault_unlocked"] is True
        assert status["storage_backend"] == "vault"
        assert "vault_path" in status
        
        # Test when vault is locked
        self.vault.lock_vault()
        status = self.config.get_storage_status()
        
        assert status["vault_unlocked"] is False
        assert status["storage_backend"] == "legacy"


class TestConfigManagerMigration:
    """Test migration functionality from legacy to vault storage."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "bapao_config"
        self.master_password = "migration_test_password_456"
        
        # Create legacy config with data
        self.legacy_config = ConfigManager(config_dir=self.config_dir, use_vault=False)
        
        # Add test profiles to legacy storage
        profile1 = Profile("legacy_work", "Legacy User", "legacy@work.com", "/home/legacy/work")
        profile2 = Profile("legacy_personal", "Legacy User", "legacy@personal.com", "/home/legacy/personal")
        
        profiles = {"legacy_work": profile1, "legacy_personal": profile2}
        self.legacy_config.save_profiles(profiles)
    
    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_successful_migration(self):
        """Test successful migration from legacy to vault."""
        # Create vault-enabled config
        vault_config = ConfigManager(config_dir=self.config_dir, use_vault=True)
        
        # Perform migration
        result = vault_config.migrate_to_vault(self.master_password)
        
        assert result is True
        
        # Verify vault was initialized and profiles migrated
        assert vault_config.is_vault_available()
        assert vault_config.is_vault_unlocked()
        
        # Load profiles from vault
        migrated_profiles = vault_config.load_profiles()
        
        assert len(migrated_profiles) == 2
        assert "legacy_work" in migrated_profiles
        assert "legacy_personal" in migrated_profiles
        assert migrated_profiles["legacy_work"].git_email == "legacy@work.com"
        
        # Verify legacy file was backed up
        backup_file = self.legacy_config.profiles_file.with_suffix('.yaml.legacy')
        assert backup_file.exists()
        
        # Original file should be gone
        assert not self.legacy_config.profiles_file.exists()
    
    def test_migration_no_legacy_data(self):
        """Test migration when no legacy data exists."""
        # Remove legacy file
        if self.legacy_config.profiles_file.exists():
            self.legacy_config.profiles_file.unlink()
        
        vault_config = ConfigManager(config_dir=self.config_dir, use_vault=True)
        
        # Migration should return False (no data to migrate)
        result = vault_config.migrate_to_vault(self.master_password)
        
        assert result is False
    
    def test_migration_to_existing_vault(self):
        """Test migration to an already initialized vault."""
        # Initialize vault first
        vault = VaultManager(self.config_dir)
        vault.initialize_vault(self.master_password)
        vault.unlock_vault(self.master_password)
        
        # Add some data to vault first
        existing_data = {
            "profiles": {
                "existing_profile": {
                    "name": "existing_profile",
                    "git_name": "Existing User",
                    "git_email": "existing@example.com", 
                    "base_directory": "/home/existing"
                }
            }
        }
        vault.store_data("profiles", existing_data)
        
        # Now try migration
        vault_config = ConfigManager(config_dir=self.config_dir, use_vault=True)
        result = vault_config.migrate_to_vault(self.master_password)
        
        assert result is True
        
        # Should have both existing and migrated profiles
        all_profiles = vault_config.load_profiles()
        
        assert len(all_profiles) >= 3  # 2 legacy + 1 existing
        assert "existing_profile" in all_profiles
        assert "legacy_work" in all_profiles
        assert "legacy_personal" in all_profiles


class TestConfigManagerIntegration:
    """Integration tests for ConfigManager with various scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "bapao_config"
    
    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_seamless_storage_switching(self):
        """Test seamless switching between storage backends."""
        # Start with legacy mode
        legacy_config = ConfigManager(config_dir=self.config_dir, use_vault=False)
        
        profile = Profile("switch_test", "Switch User", "switch@example.com", "/home/switch")
        legacy_config.create_profile(profile)
        
        # Verify in legacy mode
        assert legacy_config.profile_exists("switch_test")
        
        # Switch to vault mode with migration
        vault_config = ConfigManager(config_dir=self.config_dir, use_vault=True)
        
        # If vault not initialized, the profile should still be accessible via fallback
        if not vault_config.is_vault_available():
            loaded_profile = vault_config.get_profile("switch_test") 
            assert loaded_profile is not None
            assert loaded_profile.name == "switch_test"
    
    def test_concurrent_config_managers(self):
        """Test multiple ConfigManager instances."""
        # Create two config managers
        config1 = ConfigManager(config_dir=self.config_dir, use_vault=False)
        config2 = ConfigManager(config_dir=self.config_dir, use_vault=False)
        
        # Create profile with first instance
        profile1 = Profile("concurrent1", "User1", "user1@example.com", "/home/user1") 
        config1.create_profile(profile1)
        
        # Second instance should see the profile
        loaded_profile = config2.get_profile("concurrent1")
        assert loaded_profile is not None
        assert loaded_profile.name == "concurrent1"
    
    def test_config_manager_error_recovery(self):
        """Test ConfigManager behavior during various error conditions."""
        config = ConfigManager(config_dir=self.config_dir, use_vault=False)
        
        # Test handling corrupted profiles file
        config.profiles_file.write_text("corrupted yaml content {[}")
        
        with pytest.raises(ValueError):
            config.load_profiles()
        
        # Test recovery after fixing corruption
        config.profiles_file.write_text('profiles: {}')
        profiles = config.load_profiles()
        assert profiles == {}
    
    def test_profile_update_workflow(self):
        """Test typical profile update workflow."""
        config = ConfigManager(config_dir=self.config_dir, use_vault=False)
        
        # Create initial profile
        profile = Profile("update_test", "Original Name", "original@example.com", "/home/original")
        config.create_profile(profile)
        
        # Update profile
        updated_profile = Profile(
            "update_test", 
            "Updated Name", 
            "updated@example.com", 
            "/home/updated",
            ssh_key_path="/home/updated/.ssh/id_ed25519"
        )
        config.create_profile(updated_profile)
        
        # Verify update
        loaded_profile = config.get_profile("update_test")
        assert loaded_profile.git_name == "Updated Name"
        assert loaded_profile.git_email == "updated@example.com"
        assert loaded_profile.ssh_key_path == "/home/updated/.ssh/id_ed25519"
        
        # Should still only have one profile
        assert len(config.list_profiles()) == 1


class TestConfigManagerEdgeCases:
    """Test edge cases and error conditions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "bapao_config"
    
    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_readonly_config_directory(self):
        """Test behavior when config directory is read-only."""
        config = ConfigManager(config_dir=self.config_dir, use_vault=False)
        
        # Make config directory read-only
        self.config_dir.chmod(0o444)
        
        try:
            profile = Profile("readonly_test", "User", "user@example.com", "/home/user")
            
            with pytest.raises(ValueError):
                config.create_profile(profile)
        finally:
            # Restore permissions for cleanup
            self.config_dir.chmod(0o755)
    
    def test_nonexistent_profile_operations(self):
        """Test operations on non-existent profiles."""
        config = ConfigManager(config_dir=self.config_dir, use_vault=False)
        
        # Get non-existent profile
        profile = config.get_profile("nonexistent")
        assert profile is None
        
        # Delete non-existent profile
        result = config.delete_profile("nonexistent")
        assert result is False
        
        # Check existence of non-existent profile
        assert not config.profile_exists("nonexistent")
    
    def test_empty_profile_name(self):
        """Test handling of empty or invalid profile names."""
        config = ConfigManager(config_dir=self.config_dir, use_vault=False)
        
        # Empty name should work (dataclass allows it)
        profile = Profile("", "User", "user@example.com", "/home/user")
        config.create_profile(profile)
        
        # Should be able to retrieve with empty name
        loaded_profile = config.get_profile("")
        assert loaded_profile is not None
    
    def test_special_characters_in_profile_name(self):
        """Test handling of special characters in profile names.""" 
        config = ConfigManager(config_dir=self.config_dir, use_vault=False)
        
        # Profile names with special characters
        special_names = [
            "test-profile",
            "test_profile", 
            "test.profile",
            "test@profile",
            "test profile",  # space
            "test/profile",  # slash (might be problematic)
        ]
        
        for name in special_names:
            profile = Profile(name, "User", f"{name}@example.com", "/home/user")
            config.create_profile(profile)
            
            # Should be able to retrieve it
            loaded_profile = config.get_profile(name)
            assert loaded_profile is not None
            assert loaded_profile.name == name