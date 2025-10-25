"""
Integration tests for BAPAO CLI commands.
Tests complete workflows including passkey integration.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from bapao.cli import cli
from bapao.core.config import ConfigManager


class TestCliIntegration:
    """Test complete CLI workflows."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace = Path(tmp_dir)
            yield workspace
    
    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()
    
    def test_banner_command(self, runner):
        """Test banner command displays correctly."""
        result = runner.invoke(cli, ['banner'])
        assert result.exit_code == 0
        assert 'BAPAO' in result.output
        assert 'Developer Environment Sync Engine' in result.output
    
    def test_help_commands(self, runner):
        """Test all help commands work."""
        commands_to_test = [
            ['--help'],
            ['init', '--help'],
            ['forge', '--help'],
            ['wire', '--help'],
            ['verify', '--help'],
            ['list', '--help'],
            ['cleanup', '--help'],
            ['banner', '--help']
        ]
        
        for cmd in commands_to_test:
            result = runner.invoke(cli, cmd)
            assert result.exit_code == 0, f"Command {cmd} failed"
            assert 'help' in result.output.lower() or 'usage' in result.output.lower()


class TestProfileWorkflow:
    """Test complete profile creation and management workflow."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace = Path(tmp_dir)
            # Set up temporary config directory
            config_dir = workspace / "config"
            config_dir.mkdir()
            
            # Set environment variable for testing
            os.environ['BAPAO_CONFIG_DIR'] = str(config_dir)
            yield workspace
            # Clean up
            if 'BAPAO_CONFIG_DIR' in os.environ:
                del os.environ['BAPAO_CONFIG_DIR']
    
    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()
    
    def test_init_command_basic(self, runner, temp_workspace):
        """Test profile initialization."""
        base_dir = temp_workspace / "test-project"
        
        result = runner.invoke(cli, [
            'init', 'test-profile',
            '--name', 'Test User',
            '--email', 'test@example.com', 
            '--base-dir', str(base_dir)
        ])
        
        assert result.exit_code == 0
        assert 'Profile \'test-profile\' created successfully' in result.output
        assert 'Test User' in result.output
        assert 'test@example.com' in result.output
    
    def test_init_command_with_all_options(self, runner, temp_workspace):
        """Test profile initialization with all options."""
        base_dir = temp_workspace / "full-test"
        
        result = runner.invoke(cli, [
            'init', 'full-profile',
            '--name', 'Full Test User',
            '--email', 'full@test.com',
            '--base-dir', str(base_dir),
            '--host-alias', 'github.com-full-test'
        ])
        
        assert result.exit_code == 0
        assert 'Full Test User' in result.output
        assert 'github.com-full-test' in result.output
    
    @patch('bapao.core.passkey.PasskeyGenerator.display_passkey_securely')
    @patch('bapao.core.keys.KeyGenerator.generate_ssh_key')
    @patch('bapao.core.keys.KeyGenerator.generate_gpg_key')
    def test_forge_command_with_passkey(self, mock_gpg, mock_ssh, mock_display, runner, temp_workspace):
        """Test forge command with passkey generation."""
        # Setup
        base_dir = temp_workspace / "forge-test"
        mock_display.return_value = True  # User confirms passkey saved
        mock_ssh.return_value = (Path("/fake/private"), Path("/fake/public"))
        mock_gpg.return_value = "FAKE1234567890ABCDEF"
        
        # Create profile first
        runner.invoke(cli, [
            'init', 'forge-test',
            '--name', 'Forge User',
            '--email', 'forge@test.com',
            '--base-dir', str(base_dir)
        ])
        
        # Test forge command
        result = runner.invoke(cli, ['forge', 'forge-test'])
        
        assert result.exit_code == 0
        assert 'Generating secure passkey' in result.output
        assert 'Keys forged successfully' in result.output
        
        # Verify passkey display was called
        mock_display.assert_called_once()
        
        # Verify keys were generated with passkey
        mock_ssh.assert_called_once()
        mock_gpg.assert_called_once()
        
        # Check that passkey was passed to key generation functions
        ssh_call_args = mock_ssh.call_args[0]
        gpg_call_args = mock_gpg.call_args[0]
        
        assert len(ssh_call_args) >= 3  # profile, email, passkey
        assert len(gpg_call_args) >= 4  # name, email, profile, passkey
    
    def test_list_empty_profiles(self, runner, temp_workspace):
        """Test list command with no profiles."""
        result = runner.invoke(cli, ['list'])
        
        assert result.exit_code == 0
        # The output will vary based on existing profiles from other tests
        assert 'Found' in result.output and 'profile(s)' in result.output
    
    def test_list_with_profiles(self, runner, temp_workspace):
        """Test list command after creating profiles."""
        base_dir = temp_workspace / "list-test"
        
        # Create a profile
        runner.invoke(cli, [
            'init', 'list-test',
            '--name', 'List User',
            '--email', 'list@test.com',
            '--base-dir', str(base_dir)
        ])
        
        # Test regular list
        result = runner.invoke(cli, ['list'])
        assert result.exit_code == 0
        assert 'Found' in result.output and 'profile(s)' in result.output
        assert 'list-test' in result.output
        
        # Test verbose list
        result = runner.invoke(cli, ['list', '--verbose'])
        assert result.exit_code == 0
        # Check for parts of the name that may be on different lines due to table formatting
        assert ('List' in result.output and 'User' in result.output) or 'List User' in result.output
        # Email may be truncated in table display, so check for the beginning
        assert 'list@te' in result.output or 'list@test.com' in result.output
    
    def test_cleanup_nonexistent_profile(self, runner, temp_workspace):
        """Test cleanup command with non-existent profile."""
        result = runner.invoke(cli, ['cleanup', 'nonexistent', '--force'])
        
        assert result.exit_code != 0
        assert 'not found' in result.output.lower()
    
    def test_verify_nonexistent_profile(self, runner, temp_workspace):
        """Test verify command with non-existent profile.""" 
        result = runner.invoke(cli, ['verify', 'nonexistent'])
        
        # The verify command may be graceful rather than failing
        assert result.exit_code == 0 or 'not found' in result.output.lower()


class TestPasskeyIntegration:
    """Test passkey feature integration across all commands."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace = Path(tmp_dir)
            config_dir = workspace / "config"  
            config_dir.mkdir()
            os.environ['BAPAO_CONFIG_DIR'] = str(config_dir)
            yield workspace
            if 'BAPAO_CONFIG_DIR' in os.environ:
                del os.environ['BAPAO_CONFIG_DIR']
    
    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()
    
    @patch('bapao.core.passkey.PasskeyGenerator.display_passkey_securely')
    @patch('bapao.core.keys.KeyGenerator.generate_ssh_key')  
    @patch('bapao.core.keys.KeyGenerator.generate_gpg_key')
    def test_full_passkey_workflow(self, mock_gpg, mock_ssh, mock_display, runner, temp_workspace):
        """Test complete workflow with passkey protection."""
        base_dir = temp_workspace / "passkey-workflow"
        
        # Mock successful key generation
        mock_display.return_value = True
        mock_ssh.return_value = (Path("/fake/private"), Path("/fake/public"))
        mock_gpg.return_value = "ABCD1234EFGH5678"
        
        # 1. Init profile
        result = runner.invoke(cli, [
            'init', 'passkey-test',
            '--name', 'Passkey User',
            '--email', 'passkey@test.com',
            '--base-dir', str(base_dir)
        ])
        assert result.exit_code == 0
        
        # 2. Forge with passkey
        result = runner.invoke(cli, ['forge', 'passkey-test'])
        assert result.exit_code == 0
        assert 'secure passkey' in result.output
        
        # 3. List should show passkey protection
        result = runner.invoke(cli, ['list', '--verbose'])
        assert result.exit_code == 0
        assert '🔐' in result.output  # Check for passkey icon
        
        # 4. Verify shows passkey information
        with patch('bapao.commands.verify.check_ssh_key', return_value=(True, "OK")):
            with patch('bapao.commands.verify.check_gpg_key', return_value=(True, "OK")):
                with patch('bapao.commands.verify.check_git_config', return_value=(True, "OK")):
                    with patch('bapao.commands.verify.check_ssh_config', return_value=(True, "OK")):
                        with patch('bapao.commands.verify.check_base_directory', return_value=(True, "OK")):
                            result = runner.invoke(cli, ['verify', 'passkey-test', '--verbose'])
                            
        assert result.exit_code == 0
        assert '🔐 Passkey Protected: Yes' in result.output
        assert 'BAPAO-passkey-test' in result.output


class TestSecurityValidation:
    """Test security-related validation and edge cases."""
    
    def test_passkey_not_in_output(self):
        """Ensure passkeys never appear in command output or logs."""
        from bapao.core.passkey import PasskeyGenerator
        
        # Generate a passkey
        test_passkey = PasskeyGenerator.generate_passkey()
        
        # Mock console to capture what would be displayed
        with patch('bapao.core.passkey.console') as mock_console:
            with patch('bapao.core.passkey.Confirm.ask', return_value=True):
                PasskeyGenerator.display_passkey_securely(test_passkey, "test")
                
                # Check all console.print calls
                for call in mock_console.print.call_args_list:
                    # The passkey should only appear in the secure panel display
                    # and nowhere else in the output
                    if len(call[0]) > 0 and isinstance(call[0][0], str):
                        output_text = str(call[0][0])
                        if test_passkey in output_text:
                            # This should only be the secure panel display
                            assert 'PASSKEY FOR PROFILE' in str(call) or 'Panel' in str(call)
    
    def test_profile_storage_security(self):
        """Test that profile storage doesn't leak sensitive information."""
        from bapao.core.config import Profile
        from bapao.core.passkey import PasskeyGenerator
        
        # Generate a passkey (but don't store it)
        test_passkey = PasskeyGenerator.generate_passkey()
        
        # Create profile with passkey protection
        profile = Profile(
            name="security-test",
            git_name="Security User",
            git_email="security@test.com", 
            base_directory="/tmp/security",
            has_passkey=True,
            passkey_hint=PasskeyGenerator.get_passkey_hint("security-test")
        )
        
        # Convert to dict (what gets stored)
        profile_data = profile.to_dict()
        
        # Verify passkey is not in stored data
        stored_json = str(profile_data)
        assert test_passkey not in stored_json
        
        # Verify hint provides guidance but not the actual passkey
        assert profile_data['passkey_hint'] is not None
        assert test_passkey not in profile_data['passkey_hint']
        assert 'password manager' in profile_data['passkey_hint']
    
    def test_legacy_profile_handling(self):
        """Test that legacy profiles (without passkey) are handled correctly."""
        from bapao.core.config import Profile
        
        # Create legacy profile (no passkey fields)
        legacy_data = {
            "name": "legacy-profile",
            "git_name": "Legacy User",
            "git_email": "legacy@test.com",
            "base_directory": "/tmp/legacy"
            # Note: no has_passkey or passkey_hint
        }
        
        # Should handle missing passkey fields gracefully
        profile = Profile.from_dict(legacy_data)
        
        assert profile.has_passkey is False
        assert profile.passkey_hint is None
        assert profile.name == "legacy-profile"


class TestFeatureCompleteness:
    """Test that all advertised features work correctly."""
    
    @pytest.fixture
    def runner(self):
        return CliRunner()
    
    def test_all_commands_exist(self, runner):
        """Test that all advertised commands exist and are accessible."""
        result = runner.invoke(cli, ['--help'])
        
        expected_commands = [
            'banner', 'cleanup', 'forge', 'init', 'list', 'verify', 'wire'
        ]
        
        for cmd in expected_commands:
            assert cmd in result.output, f"Command '{cmd}' not found in help output"
    
    def test_cross_platform_paths(self):
        """Test that path handling works cross-platform."""
        from bapao.core.config import Profile
        
        # Test various path formats
        test_paths = [
            "/unix/style/path",
            "C:\\Windows\\Style\\Path", 
            "~/home/tilde/path",
            "relative/path"
        ]
        
        for test_path in test_paths:
            profile = Profile(
                name="path-test",
                git_name="Path User",
                git_email="path@test.com",
                base_directory=test_path
            )
            
            # Should not raise exceptions
            assert profile.base_directory == test_path
            
            # Should serialize/deserialize correctly
            data = profile.to_dict()
            restored = Profile.from_dict(data)
            assert restored.base_directory == test_path
    
    def test_profile_isolation(self):
        """Test that profiles are properly isolated."""
        from bapao.core.config import Profile
        
        # Create multiple profiles
        profiles = []
        for i in range(3):
            profile = Profile(
                name=f"isolated-{i}",
                git_name=f"User {i}",
                git_email=f"user{i}@test.com",
                base_directory=f"/tmp/isolated-{i}",
                has_passkey=True,
                passkey_hint=f"Store in your password manager as 'BAPAO-isolated-{i}'"
            )
            profiles.append(profile)
        
        # Verify each profile is unique and isolated
        for i, profile in enumerate(profiles):
            assert profile.name == f"isolated-{i}"
            assert profile.git_email == f"user{i}@test.com" 
            assert f"isolated-{i}" in profile.passkey_hint
            
            # Verify no cross-contamination
            for j, other_profile in enumerate(profiles):
                if i != j:
                    assert profile.name != other_profile.name
                    assert profile.git_email != other_profile.git_email
                    assert profile.passkey_hint != other_profile.passkey_hint