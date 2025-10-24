"""
Key generation utilities for SSH and GPG keys.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


class KeyGenerator:
    """Handles SSH and GPG key generation."""
    
    @staticmethod
    def generate_ssh_key(profile_name: str, email: str, key_path: Optional[Path] = None) -> Tuple[Path, Path]:
        """Generate an Ed25519 SSH key pair.
        
        Args:
            profile_name: Name of the profile
            email: Email for key comment
            key_path: Custom path for the key. Defaults to ~/.ssh/id_ed25519_{profile_name}
            
        Returns:
            Tuple of (private_key_path, public_key_path)
        """
        if key_path is None:
            ssh_dir = Path.home() / ".ssh"
            ssh_dir.mkdir(mode=0o700, exist_ok=True)
            key_path = ssh_dir / f"id_ed25519_{profile_name}"
        
        private_key_path = Path(key_path)
        public_key_path = Path(f"{key_path}.pub")
        
        # Check if key already exists
        if private_key_path.exists():
            return private_key_path, public_key_path
        
        # Generate Ed25519 private key
        private_key = ed25519.Ed25519PrivateKey.generate()
        
        # Serialize private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.OpenSSH,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # Get public key
        public_key = private_key.public_key()
        public_openssh = public_key.public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH
        )
        
        # Write private key
        private_key_path.write_bytes(private_pem)
        private_key_path.chmod(0o600)
        
        # Write public key with comment
        public_key_content = public_openssh.decode() + f" {email}"
        public_key_path.write_text(public_key_content)
        public_key_path.chmod(0o644)
        
        return private_key_path, public_key_path
    
    @staticmethod
    def generate_gpg_key(name: str, email: str, profile_name: str) -> Optional[str]:
        """Generate a GPG key using gpg command.
        
        Args:
            name: Full name for the key
            email: Email for the key
            profile_name: Profile name for key comment
            
        Returns:
            GPG key fingerprint if successful, None otherwise
        """
        # Check if gpg is available
        try:
            subprocess.run(['gpg', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
        
        # Check if key already exists
        try:
            result = subprocess.run(
                ['gpg', '--list-secret-keys', '--with-colons', email],
                capture_output=True, text=True
            )
            if result.returncode == 0 and 'sec:' in result.stdout:
                # Extract fingerprint from existing key
                for line in result.stdout.split('\n'):
                    if line.startswith('fpr:'):
                        return line.split(':')[9]
        except subprocess.CalledProcessError:
            pass
        
        # Generate batch file for GPG key generation
        batch_content = f"""
Key-Type: RSA
Key-Length: 4096
Subkey-Type: RSA
Subkey-Length: 4096
Name-Real: {name}
Name-Email: {email}
Name-Comment: BAPAO Profile: {profile_name}
Expire-Date: 0
%no-protection
%commit
"""
        
        try:
            # Create temporary batch file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.batch', delete=False) as f:
                f.write(batch_content.strip())
                batch_file = f.name
            
            # Generate the key
            result = subprocess.run(
                ['gpg', '--batch', '--generate-key', batch_file],
                capture_output=True, text=True
            )
            
            # Clean up batch file
            os.unlink(batch_file)
            
            if result.returncode != 0:
                return None
            
            # Get the fingerprint of the newly created key
            result = subprocess.run(
                ['gpg', '--list-secret-keys', '--with-colons', email],
                capture_output=True, text=True, check=True
            )
            
            for line in result.stdout.split('\n'):
                if line.startswith('fpr:'):
                    return line.split(':')[9]
                    
        except (subprocess.CalledProcessError, OSError):
            return None
        
        return None