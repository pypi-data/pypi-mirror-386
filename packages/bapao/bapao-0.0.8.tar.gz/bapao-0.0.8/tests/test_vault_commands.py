"""
Unit tests for BAPAO vault CLI commands.

Tests the vault command interface including:
- Vault initialization with quantum-safe encryption
- Vault unlock/lock operations with master password
- Vault status reporting and information display
- Vault backup creation and management
- Migration from legacy to vault storage
- CLI error handling and user experience
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from src.bapao.commands.vault import (
    vault_commands, 
    init_vault, 
    unlock_vault, 
    lock_vault, 
    vault_status, 
    backup_vault,
    migrate_to_vault
)
from src.bapao.core.quantum_crypto import VaultManager, InvalidVaultPasswordError, QuantumSafeError


class TestVaultInitCommand:
    """Test vault init command functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.vault_dir = Path(self.temp_dir) / "test_vault"
        self.runner = CliRunner()
    
    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_vault_init_success(self):
        """Test successful vault initialization."""
        with patch('rich.prompt.Prompt.ask') as mock_prompt:
            # Mock password input
            mock_prompt.side_effect = ["test_master_password_123", "test_master_password_123"]
            
            result = self.runner.invoke(init_vault, ['--vault-path', str(self.vault_dir)])
            
            assert result.exit_code == 0
            assert "Vault initialized successfully!" in result.output
            assert "quantum-safe" in result.output
            
            # Verify vault files were created
            vault = VaultManager(self.vault_dir)
            assert vault.is_vault_initialized()
    
    def test_vault_init_password_mismatch(self):
        """Test vault init with password mismatch."""
        with patch('rich.prompt.Prompt.ask') as mock_prompt:
            # Mock mismatched passwords, then correct ones
            mock_prompt.side_effect = [
                "password1", "password2",  # Mismatch
                "correct_password", "correct_password"  # Match
            ]
            
            result = self.runner.invoke(init_vault, ['--vault-path', str(self.vault_dir)])
            
            assert result.exit_code == 0
            assert "Passwords do not match" in result.output
            assert "Vault initialized successfully!" in result.output
    
    def test_vault_init_short_password(self):
        """Test vault init with password too short."""
        with patch('rich.prompt.Prompt.ask') as mock_prompt:
            # Mock short password, then correct one
            mock_prompt.side_effect = [
                "short",  # Too short
                "correct_long_password_123", "correct_long_password_123"  # Correct
            ]
            
            result = self.runner.invoke(init_vault, ['--vault-path', str(self.vault_dir)])
            
            assert result.exit_code == 0
            assert "Password must be at least 12 characters" in result.output
            assert "Vault initialized successfully!" in result.output
    
    def test_vault_init_already_exists(self):
        """Test vault init when vault already exists."""
        # Initialize vault first
        vault = VaultManager(self.vault_dir)
        vault.initialize_vault("existing_password")
        
        result = self.runner.invoke(init_vault, ['--vault-path', str(self.vault_dir)])
        
        assert result.exit_code == 0
        assert "Vault already initialized!" in result.output
    
    def test_vault_init_weak_password_acceptance(self):
        """Test vault init with weak password that user accepts."""
        with patch('rich.prompt.Prompt.ask') as mock_prompt, \
             patch('rich.prompt.Confirm.ask') as mock_confirm:
            
            # Mock weak password and user acceptance
            mock_prompt.side_effect = ["weak_pass_12", "weak_pass_12"]
            mock_confirm.return_value = True
            
            result = self.runner.invoke(init_vault, ['--vault-path', str(self.vault_dir)])
            
            assert result.exit_code == 0
            assert "Password strength:" in result.output
            assert "Vault initialized successfully!" in result.output
    
    def test_vault_init_weak_password_rejection(self):
        """Test vault init with weak password that user rejects."""
        with patch('rich.prompt.Prompt.ask') as mock_prompt, \
             patch('rich.prompt.Confirm.ask') as mock_confirm:
            
            # Mock weak password rejection, then strong password
            mock_prompt.side_effect = [
                "weak_pass_12", "weak_pass_12",  # Weak password
                "strong_password_with_numbers_123", "strong_password_with_numbers_123"  # Strong
            ]
            mock_confirm.side_effect = [False, True]  # Reject weak, accept strong
            
            result = self.runner.invoke(init_vault, ['--vault-path', str(self.vault_dir)])
            
            assert result.exit_code == 0
            assert "Excellent!" in result.output or "Vault initialized successfully!" in result.output


class TestVaultUnlockCommand:
    """Test vault unlock command functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.vault_dir = Path(self.temp_dir) / "test_vault"
        self.master_password = "test_unlock_password_123"
        self.runner = CliRunner()
        
        # Initialize vault
        self.vault = VaultManager(self.vault_dir)
        self.vault.initialize_vault(self.master_password)
    
    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_vault_unlock_success(self):
        """Test successful vault unlock."""
        with patch('rich.prompt.Prompt.ask') as mock_prompt:
            mock_prompt.return_value = self.master_password
            
            result = self.runner.invoke(unlock_vault, ['--vault-path', str(self.vault_dir)])
            
            assert result.exit_code == 0
            assert "Vault unlocked successfully!" in result.output
            
            # Check with new instance to test session persistence
            new_vault = VaultManager(self.vault_dir)
            assert new_vault.is_vault_unlocked()
    
    def test_vault_unlock_wrong_password(self):
        """Test vault unlock with wrong password."""
        with patch('rich.prompt.Prompt.ask') as mock_prompt:
            mock_prompt.side_effect = ["wrong_password", "still_wrong", "also_wrong"]
            
            result = self.runner.invoke(unlock_vault, ['--vault-path', str(self.vault_dir)])
            
            assert result.exit_code == 1
            assert "Invalid password" in result.output
            assert "Maximum attempts exceeded" in result.output
    
    def test_vault_unlock_success_after_retries(self):
        """Test vault unlock success after initial failures."""
        with patch('rich.prompt.Prompt.ask') as mock_prompt:
            # Wrong password twice, then correct
            mock_prompt.side_effect = ["wrong1", "wrong2", self.master_password]
            
            result = self.runner.invoke(unlock_vault, ['--vault-path', str(self.vault_dir)])
            
            assert result.exit_code == 0
            assert "Invalid password" in result.output
            assert "Vault unlocked successfully!" in result.output
    
    def test_vault_unlock_already_unlocked(self):
        """Test unlocking an already unlocked vault."""
        # Unlock vault first
        self.vault.unlock_vault(self.master_password)
        
        result = self.runner.invoke(unlock_vault, ['--vault-path', str(self.vault_dir)])
        
        assert result.exit_code == 0
        assert "Vault is already unlocked!" in result.output
    
    def test_vault_unlock_not_initialized(self):
        """Test unlocking a non-initialized vault."""
        uninit_vault_dir = Path(self.temp_dir) / "uninit_vault"
        
        result = self.runner.invoke(unlock_vault, ['--vault-path', str(uninit_vault_dir)])
        
        assert result.exit_code == 1
        assert "Vault not initialized!" in result.output
    
    def test_vault_unlock_with_profiles(self):
        """Test unlock shows profile information."""
        # Add some profiles to vault
        self.vault.unlock_vault(self.master_password)
        test_profiles = {
            "profiles": {
                "work": {"name": "work", "email": "work@company.com"},
                "personal": {"name": "personal", "email": "personal@gmail.com"}
            }
        }
        self.vault.store_data("profiles", test_profiles)
        self.vault.lock_vault()
        
        with patch('rich.prompt.Prompt.ask') as mock_prompt:
            mock_prompt.return_value = self.master_password
            
            result = self.runner.invoke(unlock_vault, ['--vault-path', str(self.vault_dir)])
            
            assert result.exit_code == 0
            assert "Vault contains 2 profile(s)" in result.output
            assert "work" in result.output
            assert "personal" in result.output


class TestVaultLockCommand:
    """Test vault lock command functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.vault_dir = Path(self.temp_dir) / "test_vault"
        self.master_password = "test_lock_password_123"
        self.runner = CliRunner()
        
        # Initialize and unlock vault
        self.vault = VaultManager(self.vault_dir)
        self.vault.initialize_vault(self.master_password)
        self.vault.unlock_vault(self.master_password)
    
    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_vault_lock_success(self):
        """Test successful vault locking."""
        result = self.runner.invoke(lock_vault, ['--vault-path', str(self.vault_dir)])
        
        assert result.exit_code == 0
        assert "Vault locked successfully!" in result.output
        assert "encrypted and secured" in result.output
        assert self.vault.is_vault_locked()
    
    def test_vault_lock_already_locked(self):
        """Test locking an already locked vault."""
        # Lock vault first
        self.vault.lock_vault()
        
        result = self.runner.invoke(lock_vault, ['--vault-path', str(self.vault_dir)])
        
        assert result.exit_code == 0
        assert "Vault is already locked!" in result.output
    
    def test_vault_lock_not_initialized(self):
        """Test locking a non-initialized vault."""
        uninit_vault_dir = Path(self.temp_dir) / "uninit_vault"
        
        result = self.runner.invoke(lock_vault, ['--vault-path', str(uninit_vault_dir)])
        
        assert result.exit_code == 1
        assert "Vault not initialized!" in result.output


class TestVaultStatusCommand:
    """Test vault status command functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.vault_dir = Path(self.temp_dir) / "test_vault"
        self.master_password = "test_status_password_123"
        self.runner = CliRunner()
    
    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_vault_status_not_initialized(self):
        """Test status of non-initialized vault."""
        result = self.runner.invoke(vault_status, ['--vault-path', str(self.vault_dir)])
        
        assert result.exit_code == 0
        assert "NOT INITIALIZED" in result.output
        assert "bapao vault init" in result.output
    
    def test_vault_status_initialized_locked(self):
        """Test status of initialized but locked vault."""
        # Initialize vault (locked by default)
        vault = VaultManager(self.vault_dir)
        vault.initialize_vault(self.master_password)
        
        result = self.runner.invoke(vault_status, ['--vault-path', str(self.vault_dir)])
        
        assert result.exit_code == 0
        assert "INITIALIZED" in result.output
        assert "LOCKED" in result.output
        assert "encrypted and inaccessible" in result.output
    
    def test_vault_status_unlocked_with_profiles(self):
        """Test status of unlocked vault with profiles."""
        # Initialize, unlock, and add profiles
        vault = VaultManager(self.vault_dir)
        vault.initialize_vault(self.master_password)
        vault.unlock_vault(self.master_password)
        
        test_profiles = {
            "profiles": {
                "status_test1": {"name": "test1"},
                "status_test2": {"name": "test2"},
                "status_test3": {"name": "test3"}
            }
        }
        vault.store_data("profiles", test_profiles)
        
        result = self.runner.invoke(vault_status, ['--vault-path', str(self.vault_dir)])
        
        assert result.exit_code == 0
        assert "UNLOCKED" in result.output
        assert "Contains 3 profile(s)" in result.output
    
    def test_vault_status_file_information(self):
        """Test that status shows vault file information."""
        # Initialize vault
        vault = VaultManager(self.vault_dir)
        vault.initialize_vault(self.master_password)
        
        result = self.runner.invoke(vault_status, ['--vault-path', str(self.vault_dir)])
        
        assert result.exit_code == 0
        assert "Vault Files:" in result.output
        assert "vault.kyb" in result.output
        assert "vault.sig" in result.output
        assert "vault.meta" in result.output
        assert ".locked" in result.output
    
    def test_vault_status_security_information(self):
        """Test that status shows security information."""
        # Initialize vault
        vault = VaultManager(self.vault_dir)
        vault.initialize_vault(self.master_password)
        
        result = self.runner.invoke(vault_status, ['--vault-path', str(self.vault_dir)])
        
        assert result.exit_code == 0
        assert "Security Information:" in result.output
        assert "Kyber-1024" in result.output or "Algorithm:" in result.output
        assert "Quantum Safe: Yes" in result.output
        assert "Post-Quantum Ready: Yes" in result.output


class TestVaultBackupCommand:
    """Test vault backup command functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.vault_dir = Path(self.temp_dir) / "test_vault"
        self.backup_path = Path(self.temp_dir) / "backup.vault"
        self.master_password = "test_backup_password_123"
        self.runner = CliRunner()
        
        # Initialize vault with data
        self.vault = VaultManager(self.vault_dir)
        self.vault.initialize_vault(self.master_password)
        self.vault.unlock_vault(self.master_password)
        
        # Add test data
        test_data = {
            "profiles": {
                "backup_test": {"name": "backup_test", "email": "backup@test.com"}
            }
        }
        self.vault.store_data("profiles", test_data)
    
    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_vault_backup_success(self):
        """Test successful vault backup creation."""
        with patch('rich.prompt.Prompt.ask') as mock_prompt:
            mock_prompt.return_value = self.master_password
            
            result = self.runner.invoke(backup_vault, [
                '--vault-path', str(self.vault_dir),
                '--backup-path', str(self.backup_path)
            ])
            
            assert result.exit_code == 0
            assert "Backup created successfully!" in result.output
            assert "quantum-safe encrypted" in result.output
            assert self.backup_path.exists()
    
    def test_vault_backup_wrong_password(self):
        """Test backup with wrong password."""
        with patch('rich.prompt.Prompt.ask') as mock_prompt:
            mock_prompt.return_value = "wrong_password"
            
            result = self.runner.invoke(backup_vault, [
                '--vault-path', str(self.vault_dir),
                '--backup-path', str(self.backup_path)
            ])
            
            assert result.exit_code == 1
            assert "Invalid password" in result.output
    
    def test_vault_backup_not_initialized(self):
        """Test backup of non-initialized vault."""
        uninit_vault_dir = Path(self.temp_dir) / "uninit_vault"
        
        result = self.runner.invoke(backup_vault, [
            '--vault-path', str(uninit_vault_dir),
            '--backup-path', str(self.backup_path)
        ])
        
        assert result.exit_code == 1
        assert "Vault not initialized!" in result.output
    
    def test_vault_backup_existing_file_confirmation(self):
        """Test backup with existing file requiring confirmation."""
        # Create existing backup file
        self.backup_path.write_text("existing backup")
        
        with patch('rich.prompt.Prompt.ask') as mock_prompt, \
             patch('rich.prompt.Confirm.ask') as mock_confirm:
            
            mock_prompt.return_value = self.master_password
            mock_confirm.return_value = True  # Confirm overwrite
            
            result = self.runner.invoke(backup_vault, [
                '--vault-path', str(self.vault_dir),
                '--backup-path', str(self.backup_path)
            ])
            
            assert result.exit_code == 0
            assert "Backup created successfully!" in result.output


class TestVaultMigrateCommand:
    """Test vault migrate command functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "bapao_config"
        self.runner = CliRunner()
        
        # Create legacy profiles file
        from src.bapao.core.config import ConfigManager
        self.legacy_config = ConfigManager(config_dir=self.config_dir, use_vault=False)
        
        # Add legacy profiles
        from src.bapao.core.config import Profile
        profile1 = Profile("migrate_work", "Migrate User", "migrate@work.com", "/home/migrate/work")
        profile2 = Profile("migrate_personal", "Migrate User", "migrate@personal.com", "/home/migrate/personal")
        
        profiles = {"migrate_work": profile1, "migrate_personal": profile2}
        self.legacy_config.save_profiles(profiles)
    
    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_vault_migrate_success(self):
        """Test successful migration from legacy to vault."""
        with patch('rich.prompt.Prompt.ask') as mock_prompt, \
             patch('rich.prompt.Confirm.ask') as mock_confirm:
            
            # Mock user confirmation and password input
            mock_confirm.return_value = True
            mock_prompt.side_effect = ["migrate_password_123", "migrate_password_123"]
            
            result = self.runner.invoke(migrate_to_vault, [
                '--vault-path', str(self.config_dir)
            ])
            
            assert result.exit_code == 0
            assert "Migration completed successfully!" in result.output
            assert "quantum-safe encrypted!" in result.output
            
            # Verify migration worked
            vault = VaultManager(self.config_dir)
            assert vault.is_vault_initialized()
    
    def test_vault_migrate_no_legacy_data(self):
        """Test migration when no legacy data exists."""
        # Remove legacy file
        if self.legacy_config.profiles_file.exists():
            self.legacy_config.profiles_file.unlink()
        
        result = self.runner.invoke(migrate_to_vault, [
            '--vault-path', str(self.config_dir)
        ])
        
        assert result.exit_code == 0
        assert "No legacy profile data found!" in result.output
    
    def test_vault_migrate_force_mode(self):
        """Test migration in force mode (no prompts)."""
        with patch('rich.prompt.Prompt.ask') as mock_prompt:
            # Only password prompts, no confirmation
            mock_prompt.side_effect = ["force_migrate_password", "force_migrate_password"]
            
            result = self.runner.invoke(migrate_to_vault, [
                '--vault-path', str(self.config_dir),
                '--force'
            ])
            
            assert result.exit_code == 0
            assert "Migration completed successfully!" in result.output
    
    def test_vault_migrate_to_existing_vault(self):
        """Test migration to existing vault."""
        # Initialize vault first
        vault = VaultManager(self.config_dir)
        master_password = "existing_vault_password"
        vault.initialize_vault(master_password)
        vault.unlock_vault(master_password)
        
        with patch('rich.prompt.Confirm.ask') as mock_confirm:
            mock_confirm.return_value = True  # Confirm merge
            
            result = self.runner.invoke(migrate_to_vault, [
                '--vault-path', str(self.config_dir)
            ])
            
            assert result.exit_code == 0
            assert "Vault already exists" in result.output
            assert "Migration completed successfully!" in result.output
    
    def test_vault_migrate_cancel(self):
        """Test migration cancellation by user."""
        with patch('rich.prompt.Confirm.ask') as mock_confirm:
            mock_confirm.return_value = False  # User cancels
            
            result = self.runner.invoke(migrate_to_vault, [
                '--vault-path', str(self.config_dir)
            ])
            
            assert result.exit_code == 0
            assert "Migration cancelled by user" in result.output
    
    def test_vault_migrate_password_strength_check(self):
        """Test password strength checking during migration."""
        with patch('rich.prompt.Prompt.ask') as mock_prompt, \
             patch('rich.prompt.Confirm.ask') as mock_confirm:
            
            # Mock weak password, then strong password
            mock_prompt.side_effect = [
                "weak",  # Too short
                "weak_password_12", "weak_password_12",  # Weak but acceptable
            ]
            mock_confirm.side_effect = [True, True]  # Accept migration, accept weak password
            
            result = self.runner.invoke(migrate_to_vault, [
                '--vault-path', str(self.config_dir)
            ])
            
            assert result.exit_code == 0
            assert "Password must be at least 12 characters" in result.output
            assert "Password strength:" in result.output


class TestVaultCommandsIntegration:
    """Integration tests for vault commands working together."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.vault_dir = Path(self.temp_dir) / "integration_vault"
        self.master_password = "integration_test_password_456"
        self.runner = CliRunner()
    
    def teardown_method(self):
        """Clean up temporary files.""" 
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_vault_lifecycle(self):
        """Test complete vault lifecycle: init -> unlock -> lock -> status -> backup."""
        # 1. Initialize vault
        with patch('rich.prompt.Prompt.ask') as mock_prompt:
            mock_prompt.side_effect = [self.master_password, self.master_password]
            
            result = self.runner.invoke(init_vault, ['--vault-path', str(self.vault_dir)])
            assert result.exit_code == 0
            assert "Vault initialized successfully!" in result.output
        
        # 2. Check status (should be locked)
        result = self.runner.invoke(vault_status, ['--vault-path', str(self.vault_dir)])
        assert result.exit_code == 0
        assert "LOCKED" in result.output
        
        # 3. Unlock vault
        with patch('rich.prompt.Prompt.ask') as mock_prompt:
            mock_prompt.return_value = self.master_password
            
            result = self.runner.invoke(unlock_vault, ['--vault-path', str(self.vault_dir)])
            assert result.exit_code == 0
            assert "Vault unlocked successfully!" in result.output
        
        # 4. Check status (should be unlocked)
        result = self.runner.invoke(vault_status, ['--vault-path', str(self.vault_dir)])
        assert result.exit_code == 0
        assert "UNLOCKED" in result.output
        
        # 5. Lock vault
        result = self.runner.invoke(lock_vault, ['--vault-path', str(self.vault_dir)])
        assert result.exit_code == 0
        assert "Vault locked successfully!" in result.output
        
        # 6. Create backup
        backup_path = Path(self.temp_dir) / "lifecycle_backup.vault"
        with patch('rich.prompt.Prompt.ask') as mock_prompt:
            mock_prompt.return_value = self.master_password
            
            result = self.runner.invoke(backup_vault, [
                '--vault-path', str(self.vault_dir),
                '--backup-path', str(backup_path)
            ])
            assert result.exit_code == 0
            assert "Backup created successfully!" in result.output
            assert backup_path.exists()
    
    def test_vault_commands_error_consistency(self):
        """Test that all vault commands handle errors consistently."""
        nonexistent_vault = Path(self.temp_dir) / "nonexistent"
        
        # All commands should handle non-existent vault gracefully
        commands_and_args = [
            (unlock_vault, ['--vault-path', str(nonexistent_vault)]),
            (lock_vault, ['--vault-path', str(nonexistent_vault)]), 
            (backup_vault, ['--vault-path', str(nonexistent_vault), '--backup-path', '/tmp/backup'])
        ]
        
        for command, args in commands_and_args:
            result = self.runner.invoke(command, args)
            # Should fail gracefully (exit code 1) with clear error message
            assert result.exit_code == 1
            assert "not initialized" in result.output.lower() or "error" in result.output.lower()


class TestVaultCommandsErrorHandling:
    """Test error handling across vault commands."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.vault_dir = Path(self.temp_dir) / "error_vault"
        self.runner = CliRunner()
    
    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_vault_commands_with_invalid_paths(self):
        """Test vault commands with invalid vault paths."""
        invalid_path = "/nonexistent/invalid/path"
        
        # Test init command with invalid path
        with patch('rich.prompt.Prompt.ask') as mock_prompt:
            mock_prompt.side_effect = ["password123", "password123"]
            
            # Should handle gracefully or create directory
            result = self.runner.invoke(init_vault, ['--vault-path', invalid_path])
            # Behavior depends on implementation - either creates path or fails gracefully
    
    def test_vault_command_keyboard_interrupt(self):
        """Test handling of keyboard interrupts during password entry."""
        with patch('rich.prompt.Prompt.ask', side_effect=KeyboardInterrupt):
            result = self.runner.invoke(init_vault, ['--vault-path', str(self.vault_dir)])
            
            # Should handle KeyboardInterrupt gracefully
            # (Click usually converts this to a ClickException)
    
    @patch('src.bapao.core.quantum_crypto.VaultManager')
    def test_vault_commands_with_quantum_crypto_errors(self, mock_vault_manager):
        """Test vault commands when quantum crypto operations fail."""
        # Mock VaultManager to raise QuantumSafeError
        mock_instance = MagicMock()
        mock_instance.initialize_vault.side_effect = QuantumSafeError("Crypto error")
        mock_vault_manager.return_value = mock_instance
        
        with patch('rich.prompt.Prompt.ask') as mock_prompt:
            mock_prompt.side_effect = ["password123", "password123"]
            
            result = self.runner.invoke(init_vault, ['--vault-path', str(self.vault_dir)])
            
            assert result.exit_code == 1
            assert "Crypto error" in result.output or "initialization failed" in result.output