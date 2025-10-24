"""
BAPAO List Command - Show all configured profiles.
"""
import os
from pathlib import Path
from typing import Dict, Any

import click
from rich.console import Console
from rich.table import Table

from ..core.config import ConfigManager

console = Console()


@click.command()
@click.option('--verbose', '-v', is_flag=True, help='Show detailed information')
def list_profiles(verbose: bool) -> None:
    """
    List all configured BAPAO profiles.
    
    Shows profile names, directories, host aliases, and key status.
    Use --verbose for additional details like Git configuration and key fingerprints.
    """
    config_manager = ConfigManager()
    profiles = config_manager.load_profiles()
    
    if not profiles:
        console.print("📭 No profiles found. Create one with:")
        console.print("   [cyan]bapao init <profile-name>[/cyan]")
        return
    
    console.print(f"📋 [bold]Found {len(profiles)} profile(s):[/bold]")
    console.print()
    
    # Create table
    if verbose:
        table = Table(title="BAPAO Profiles (Detailed)")
        table.add_column("Profile", style="cyan", no_wrap=True)
        table.add_column("Directory", style="blue")
        table.add_column("Git Identity", style="green")
        table.add_column("Host Alias", style="yellow")
        table.add_column("SSH Key", style="magenta")
        table.add_column("GPG Key", style="red")
    else:
        table = Table(title="BAPAO Profiles")
        table.add_column("Profile", style="cyan", no_wrap=True)
        table.add_column("Directory", style="blue")
        table.add_column("Host Alias", style="yellow")
        table.add_column("Status", style="green")
    
    # Add profile data
    for name, profile_obj in profiles.items():
        profile = profile_obj.to_dict()
        
        # Check key status
        ssh_key_path = Path.home() / '.ssh' / f'id_ed25519_{name}'
        ssh_status = "✅" if ssh_key_path.exists() else "❌"
        
        gpg_status = "❌"
        if profile.get('gpg_key_fingerprint'):
            # Quick check if GPG key exists (simplified)
            gpg_status = "✅"
        
        # Format directory path (shorten if too long)
        base_dir = profile.get('base_directory', 'N/A')
        if len(base_dir) > 40:
            base_dir = "..." + base_dir[-37:]
        
        if verbose:
            git_identity = f"{profile.get('git_name', 'N/A')}\n{profile.get('git_email', 'N/A')}"
            gpg_detail = profile.get('gpg_key_fingerprint', 'None')
            if gpg_detail and len(gpg_detail) > 16:
                gpg_detail = gpg_detail[:16] + "..."
            
            table.add_row(
                name,
                base_dir,
                git_identity,
                profile.get('git_host_alias', 'N/A'),
                ssh_status,
                f"{gpg_status} {gpg_detail}" if gpg_detail != 'None' else gpg_status
            )
        else:
            # Combined status
            if ssh_status == "✅" and gpg_status == "✅":
                status = "✅ Ready"
            elif ssh_status == "✅" or gpg_status == "✅":
                status = "⚠️ Partial"
            else:
                status = "❌ Not Set"
            
            table.add_row(
                name,
                base_dir,
                profile.get('git_host_alias', 'N/A'),
                status
            )
    
    console.print(table)
    
    # Show usage hints
    console.print()
    console.print("[dim]Commands:[/dim]")
    console.print("  [cyan]bapao verify <profile>[/cyan]  - Check specific profile")
    console.print("  [cyan]bapao cleanup <profile>[/cyan] - Remove profile completely")
    if not verbose:
        console.print("  [cyan]bapao list --verbose[/cyan]   - Show detailed information")