"""
Configuration management for BAPAO profiles.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


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
    """Manages BAPAO configuration and profiles."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize configuration manager.
        
        Args:
            config_dir: Custom config directory path. Defaults to ~/.config/bapao
        """
        self.config_dir = config_dir or Path.home() / ".config" / "bapao"
        self.profiles_file = self.config_dir / "profiles.yaml"
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        """Ensure configuration directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load_profiles(self) -> Dict[str, Profile]:
        """Load all profiles from configuration file.
        
        Returns:
            Dictionary mapping profile names to Profile objects
        """
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
            raise ValueError(f"Failed to load profiles: {e}")

    def save_profiles(self, profiles: Dict[str, Profile]) -> None:
        """Save profiles to configuration file.
        
        Args:
            profiles: Dictionary mapping profile names to Profile objects
        """
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
            raise ValueError(f"Failed to save profiles: {e}")

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