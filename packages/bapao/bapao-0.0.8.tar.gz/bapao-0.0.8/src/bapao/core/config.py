"""
Configuration management for BAPAO profiles.
Supports both legacy file-based storage and quantum-safe vault storage.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from .quantum_crypto import VaultManager, VaultLockedError, QuantumSafeError


@dataclass
class Profile:
    """Represents a BAPAO development profile."""
    name: str
    git_name: str
    git_email: str
    base_directory: str
    ssh_key_path: Optional[str] = None
    gpg_key_fingerprint: Optional[str] = None
    git_host_alias: Optional[str] = None
    has_passkey: bool = False
    passkey_hint: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Profile':
        """Create profile from dictionary."""
        return cls(**data)


class ConfigManager:
    """
    Manages BAPAO configuration and profiles.
    
    Supports both legacy file-based storage and quantum-safe vault storage
    with automatic migration capabilities.
    """
    
    def __init__(self, config_dir: Optional[Path] = None, use_vault: bool = True):
        """Initialize configuration manager.
        
        Args:
            config_dir: Custom config directory path. Defaults to ~/.config/bapao
            use_vault: Whether to use quantum-safe vault storage (default: True)
        """
        self.config_dir = config_dir or Path.home() / ".config" / "bapao"
        self.profiles_file = self.config_dir / "profiles.yaml"
        self.use_vault = use_vault
        self.vault_manager = VaultManager(self.config_dir) if use_vault else None
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        """Ensure configuration directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def is_vault_available(self) -> bool:
        """Check if quantum-safe vault is available and initialized."""
        return self.vault_manager is not None and self.vault_manager.is_vault_initialized()

    def is_vault_unlocked(self) -> bool:
        """Check if vault is currently unlocked."""
        if not self.is_vault_available():
            return False
        return self.vault_manager.is_vault_unlocked()

    def migrate_to_vault(self, master_password: str) -> bool:
        """
        Migrate legacy profiles to quantum-safe vault storage.
        
        Args:
            master_password: Master password for vault initialization
            
        Returns:
            True if migration was successful, False if no legacy data found
        """
        if not self.vault_manager:
            raise QuantumSafeError("Vault manager not initialized")
            
        # Load legacy profiles if they exist
        legacy_profiles = self._load_legacy_profiles()
        if not legacy_profiles:
            return False
            
        # Initialize vault if not already done
        if not self.vault_manager.is_vault_initialized():
            self.vault_manager.initialize_vault(master_password)
        
        # Unlock vault for migration
        if not self.vault_manager.is_vault_unlocked():
            self.vault_manager.unlock_vault(master_password)
        
        # Store profiles in vault
        profiles_data = {
            'profiles': {
                name: profile.to_dict() 
                for name, profile in legacy_profiles.items()
            }
        }
        
        self.vault_manager.store_data('profiles', profiles_data)
        
        # Backup legacy file and remove it
        backup_file = self.profiles_file.with_suffix('.yaml.legacy')
        if self.profiles_file.exists():
            self.profiles_file.rename(backup_file)
            
        return True

    def _load_legacy_profiles(self) -> Dict[str, Profile]:
        """Load profiles from legacy YAML file."""
        if not self.profiles_file.exists():
            return {}
        
        try:
            with open(self.profiles_file, 'r') as f:
                data = yaml.safe_load(f) or {}
            
            profiles = {}
            for name, profile_data in data.get('profiles', {}).items():
                profiles[name] = Profile.from_dict(profile_data)
            
            return profiles
        except (yaml.YAMLError, KeyError, TypeError) as e:
            raise ValueError(f"Failed to load legacy profiles: {e}")

    def _save_legacy_profiles(self, profiles: Dict[str, Profile]) -> None:
        """Save profiles to legacy YAML file."""
        data = {
            'profiles': {
                name: profile.to_dict() 
                for name, profile in profiles.items()
            }
        }
        
        try:
            with open(self.profiles_file, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, indent=2)
        except (OSError, yaml.YAMLError) as e:
            raise ValueError(f"Failed to save legacy profiles: {e}")

    def load_profiles(self) -> Dict[str, Profile]:
        """
        Load all profiles from storage.
        
        Uses vault storage if available and unlocked, otherwise falls back to legacy file.
        
        Returns:
            Dictionary mapping profile names to Profile objects
        """
        # Try vault storage first if available
        if self.use_vault and self.is_vault_available():
            if not self.is_vault_unlocked():
                raise VaultLockedError("Vault is locked. Use 'bapao vault unlock' to unlock it.")
            
            try:
                data = self.vault_manager.retrieve_data('profiles')
                if data and 'profiles' in data:
                    profiles = {}
                    for name, profile_data in data['profiles'].items():
                        profiles[name] = Profile.from_dict(profile_data)
                    return profiles
            except Exception as e:
                # If vault fails, fall back to legacy but warn
                print(f"Warning: Vault error, falling back to legacy storage: {e}")
        
        # Fall back to legacy file storage
        return self._load_legacy_profiles()

    def save_profiles(self, profiles: Dict[str, Profile]) -> None:
        """
        Save profiles to storage.
        
        Uses vault storage if available and unlocked, otherwise saves to legacy file.
        
        Args:
            profiles: Dictionary mapping profile names to Profile objects
        """
        # Try vault storage first if available
        if self.use_vault and self.is_vault_available():
            if not self.is_vault_unlocked():
                raise VaultLockedError("Vault is locked. Use 'bapao vault unlock' to unlock it.")
            
            try:
                profiles_data = {
                    'profiles': {
                        name: profile.to_dict() 
                        for name, profile in profiles.items()
                    }
                }
                self.vault_manager.store_data('profiles', profiles_data)
                return
            except Exception as e:
                # If vault fails, fall back to legacy but warn
                print(f"Warning: Vault error, falling back to legacy storage: {e}")
        
        # Fall back to legacy file storage
        self._save_legacy_profiles(profiles)

    def get_profile(self, name: str) -> Optional[Profile]:
        """Get a specific profile by name.
        
        Args:
            name: Profile name
            
        Returns:
            Profile object if found, None otherwise
        """
        profiles = self.load_profiles()
        return profiles.get(name)

    def create_profile(self, profile: Profile) -> None:
        """Create or update a profile.
        
        Args:
            profile: Profile object to save
        """
        profiles = self.load_profiles()
        profiles[profile.name] = profile
        self.save_profiles(profiles)

    def delete_profile(self, name: str) -> bool:
        """Delete a profile.
        
        Args:
            name: Profile name to delete
            
        Returns:
            True if profile was deleted, False if not found
        """
        profiles = self.load_profiles()
        if name in profiles:
            del profiles[name]
            self.save_profiles(profiles)
            return True
        return False

    def list_profiles(self) -> List[str]:
        """List all profile names.
        
        Returns:
            List of profile names
        """
        profiles = self.load_profiles()
        return list(profiles.keys())

    def profile_exists(self, name: str) -> bool:
        """Check if a profile exists.
        
        Args:
            name: Profile name
            
        Returns:
            True if profile exists, False otherwise
        """
        return name in self.load_profiles()

    def get_storage_status(self) -> Dict[str, Any]:
        """
        Get status information about current storage backend.
        
        Returns:
            Dictionary with storage status information
        """
        status = {
            'vault_enabled': self.use_vault,
            'vault_available': self.is_vault_available(),
            'vault_unlocked': self.is_vault_unlocked() if self.is_vault_available() else False,
            'legacy_file_exists': self.profiles_file.exists(),
            'storage_backend': 'vault' if (self.use_vault and self.is_vault_available() and self.is_vault_unlocked()) else 'legacy'
        }
        
        if self.is_vault_available():
            status['vault_path'] = str(self.vault_manager.vault_file)
            
        return status