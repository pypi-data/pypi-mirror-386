"""
Git and SSH configuration utilities.
"""

import os
import re
from pathlib import Path
from typing import List, Optional


class GitConfigManager:
    """Manages Git configuration for profiles."""
    
    @staticmethod
    def get_gitconfig_path() -> Path:
        """Get the main Git config file path."""
        return Path.home() / ".gitconfig"
    
    @staticmethod
    def get_profile_gitconfig_path(profile_name: str) -> Path:
        """Get the profile-specific Git config file path."""
        return Path.home() / f".gitconfig-{profile_name}"
    
    @staticmethod
    def create_profile_gitconfig(profile, force: bool = False) -> None:
        """Create a profile-specific Git config file.
        
        Args:
            profile: Profile object with Git settings
            force: Whether to overwrite existing config
        """
        config_path = GitConfigManager.get_profile_gitconfig_path(profile.name)
        
        if config_path.exists() and not force:
            return  # Don't overwrite existing config
        
        config_content = f"""[user]
    name = {profile.git_name}
    email = {profile.git_email}
"""
        
        if profile.gpg_key_fingerprint:
            config_content += f"""    signingkey = {profile.gpg_key_fingerprint}

[commit]
    gpgsign = true

[tag]
    gpgsign = true
"""
        
        config_path.write_text(config_content)
    
    @staticmethod
    def add_include_if_block(profile) -> None:
        """Add includeIf block to main .gitconfig for directory-based profile switching.
        
        Args:
            profile: Profile object
        """
        gitconfig_path = GitConfigManager.get_gitconfig_path()
        profile_config_path = GitConfigManager.get_profile_gitconfig_path(profile.name)
        
        # Read existing gitconfig or create empty
        if gitconfig_path.exists():
            content = gitconfig_path.read_text()
        else:
            content = ""
        
        # Check if includeIf block already exists
        include_pattern = f'[includeIf "gitdir:{profile.base_directory}/"]'
        if include_pattern in content:
            return  # Already configured
        
        # Add the includeIf block
        include_block = f"""
[includeIf "gitdir:{profile.base_directory}/"]
    path = {profile_config_path}
"""
        
        content += include_block
        gitconfig_path.write_text(content)


class SSHConfigManager:
    """Manages SSH configuration for profiles."""
    
    @staticmethod
    def get_ssh_config_path() -> Path:
        """Get SSH config file path."""
        ssh_dir = Path.home() / ".ssh"
        ssh_dir.mkdir(mode=0o700, exist_ok=True)
        return ssh_dir / "config"
    
    @staticmethod
    def add_host_config(profile) -> None:
        """Add SSH host configuration for the profile.
        
        Args:
            profile: Profile object with SSH settings
        """
        if not profile.ssh_key_path or not profile.git_host_alias:
            return
        
        ssh_config_path = SSHConfigManager.get_ssh_config_path()
        
        # Read existing SSH config
        if ssh_config_path.exists():
            content = ssh_config_path.read_text()
        else:
            content = ""
        
        # Check if host config already exists
        host_pattern = f"Host {profile.git_host_alias}"
        if host_pattern in content:
            return  # Already configured
        
        # Determine the base hostname (e.g., github.com from github.com-work)
        if '-' in profile.git_host_alias:
            base_hostname = profile.git_host_alias.split('-')[0]
        else:
            base_hostname = profile.git_host_alias
        
        # Add SSH host configuration
        host_config = f"""
Host {profile.git_host_alias}
    HostName {base_hostname}
    User git
    IdentityFile {profile.ssh_key_path}
    IdentitiesOnly yes
"""
        
        content += host_config
        ssh_config_path.write_text(content)
        ssh_config_path.chmod(0o600)
    
    @staticmethod
    def list_host_configs() -> List[str]:
        """List all configured SSH hosts.
        
        Returns:
            List of host aliases
        """
        ssh_config_path = SSHConfigManager.get_ssh_config_path()
        
        if not ssh_config_path.exists():
            return []
        
        content = ssh_config_path.read_text()
        hosts = []
        
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('Host ') and not line.startswith('Host *'):
                host = line.split('Host ')[1].strip()
                hosts.append(host)
        
        return hosts