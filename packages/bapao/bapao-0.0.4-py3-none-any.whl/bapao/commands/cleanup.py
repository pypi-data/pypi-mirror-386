"""
BAPAO Cleanup Command - Remove all traces of a profile.
"""
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any

import click
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from ..core.config import ConfigManager

console = Console()


def _select_profile_to_cleanup(config_manager: ConfigManager, interactive: bool) -> str:
    """Show profile selection for cleanup."""
    profiles = config_manager.load_profiles()
    
    if not profiles:
        console.print("📭 No profiles found to cleanup.")
        return None
    
    console.print("🧹 [bold red]Select profile to cleanup:[/bold red]")
    console.print()
    
    # Show profiles in a table
    table = Table()
    table.add_column("#", style="cyan", width=3)
    table.add_column("Profile", style="yellow")
    table.add_column("Directory", style="blue")
    table.add_column("Host Alias", style="green")
    
    profile_list = list(profiles.items())
    
    for i, (name, profile_obj) in enumerate(profile_list, 1):
        profile = profile_obj.to_dict()
        base_dir = profile.get('base_directory', 'N/A')
        if len(base_dir) > 35:
            base_dir = "..." + base_dir[-32:]
        
        table.add_row(
            str(i),
            name,
            base_dir,
            profile.get('git_host_alias', 'N/A')
        )
    
    console.print(table)
    console.print()
    console.print("[dim]Enter the number of the profile to cleanup, or press Enter to cancel.[/dim]")
    
    while True:
        try:
            choice = Prompt.ask("Profile to cleanup", default="")
            
            if not choice:
                console.print("❌ Cleanup cancelled.")
                return None
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(profile_list):
                selected_profile = profile_list[choice_num - 1][0]
                console.print(f"Selected: [yellow]{selected_profile}[/yellow]")
                console.print()
                return selected_profile
            else:
                console.print(f"❌ Please enter a number between 1 and {len(profile_list)}")
                
        except ValueError:
            console.print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            console.print("\n❌ Cleanup cancelled.")
            return None


@click.command()
@click.argument('profile_name', required=False)
@click.option('--force', '-f', is_flag=True, help='Skip confirmation prompts')
@click.option('--interactive', '-i', is_flag=True, help='Interactive profile selection')
def cleanup(profile_name: str, force: bool, interactive: bool) -> None:
    """
    Remove all traces of a profile - SSH keys, GPG keys, configs, and profile data.
    
    If no PROFILE_NAME is provided, shows a list of profiles to choose from.
    Use --interactive for a selection menu.
    
    This command will:
    - Delete SSH keypair
    - Remove GPG key from keyring
    - Clean Git configuration entries
    - Clean SSH configuration entries
    - Remove profile from profiles.yaml
    - Remove base directory (if empty)
    
    Use with caution - this action cannot be undone!
    """
    config_manager = ConfigManager()
    
    # If no profile specified or interactive mode, show selection
    if not profile_name or interactive:
        profile_name = _select_profile_to_cleanup(config_manager, interactive)
        if not profile_name:
            return
    
    console.print(f"🧹 [red]Cleaning up profile:[/red] {profile_name}")
    console.print()
    
    # Load the selected profile
    profile = config_manager.get_profile(profile_name)
    
    if not profile:
        console.print(f"❌ Profile '{profile_name}' not found!")
        raise click.Abort()
    
    # Show what will be deleted
    cleanup_items = _get_cleanup_items(profile_name, profile.to_dict())
    _show_cleanup_preview(cleanup_items)
    
    if not force:
        console.print()
        if not Confirm.ask(f"[red]Delete all traces of profile '{profile_name}'?[/red]", default=False):
            console.print("❌ Cleanup cancelled.")
            raise click.Abort()
    
    console.print()
    console.print("🗑️  Starting cleanup...")
    
    # Execute cleanup
    _execute_cleanup(profile_name, profile.to_dict(), cleanup_items, force, config_manager)
    
    console.print()
    console.print("🎉 [green]Profile completely removed![/green] It's like it never existed.")


def _get_cleanup_items(profile_name: str, profile: Dict[str, Any]) -> Dict[str, Any]:
    """Get list of items that will be cleaned up."""
    home = Path.home()
    
    items = {
        'ssh_private': home / '.ssh' / f'id_ed25519_{profile_name}',
        'ssh_public': home / '.ssh' / f'id_ed25519_{profile_name}.pub',
        'git_config': home / f'.gitconfig-{profile_name}',
        'profiles_entry': f"Profile entry in ~/.config/bapao/profiles.yaml",
        'gpg_key': profile.get('gpg_key_fingerprint'),
        'base_directory': Path(profile['base_directory']) if profile.get('base_directory') else None,
    }
    
    return items


def _show_cleanup_preview(items: Dict[str, Any]) -> None:
    """Show what will be deleted."""
    table = Table(title="Items to be Deleted", title_style="red bold")
    table.add_column("Type", style="cyan")
    table.add_column("Location/Details", style="white")
    table.add_column("Exists", style="green")
    
    # SSH Keys
    for key in ['ssh_private', 'ssh_public']:
        path = items[key]
        exists = "✅" if path.exists() else "❌"
        table.add_row(
            "SSH Key" if "private" in key else "SSH Public Key",
            str(path),
            exists
        )
    
    # Git Config
    path = items['git_config']
    exists = "✅" if path.exists() else "❌"
    table.add_row("Git Config", str(path), exists)
    
    # GPG Key
    if items['gpg_key']:
        table.add_row("GPG Key", f"Fingerprint: {items['gpg_key']}", "✅")
    
    # Profile Entry
    table.add_row("Profile Entry", items['profiles_entry'], "✅")
    
    # Base Directory
    if items['base_directory']:
        base_dir = items['base_directory']
        if base_dir.exists():
            is_empty = not any(base_dir.iterdir()) if base_dir.is_dir() else False
            status = "✅ (empty - will delete)" if is_empty else "✅ (has files - will keep)"
        else:
            status = "❌"
        table.add_row("Base Directory", str(base_dir), status)
    
    console.print(table)


def _execute_cleanup(profile_name: str, profile: Dict[str, Any], items: Dict[str, Any], force: bool, config_manager: ConfigManager) -> None:
    """Execute the actual cleanup."""
    
    # 1. Remove SSH keys
    for key_type in ['ssh_private', 'ssh_public']:
        ssh_file = items[key_type]
        if ssh_file.exists():
            try:
                ssh_file.unlink()
                console.print(f"   ✅ Removed {ssh_file}")
            except Exception as e:
                console.print(f"   ❌ Failed to remove {ssh_file}: {e}")
    
    # 2. Remove GPG key
    if items['gpg_key']:
        try:
            result = subprocess.run(
                ['gpg', '--batch', '--yes', '--delete-secret-keys', items['gpg_key']], 
                capture_output=True, text=True
            )
            if result.returncode == 0:
                console.print(f"   ✅ Removed GPG secret key")
            
            result = subprocess.run(
                ['gpg', '--batch', '--yes', '--delete-keys', items['gpg_key']], 
                capture_output=True, text=True
            )
            if result.returncode == 0:
                console.print(f"   ✅ Removed GPG public key")
                
        except Exception as e:
            console.print(f"   ❌ Failed to remove GPG key: {e}")
    
    # 3. Remove Git config file
    git_config_file = items['git_config']
    if git_config_file.exists():
        try:
            git_config_file.unlink()
            console.print(f"   ✅ Removed Git config file")
        except Exception as e:
            console.print(f"   ❌ Failed to remove Git config: {e}")
    
    # 4. Clean main Git config
    _clean_git_config(profile_name)
    
    # 5. Clean SSH config
    _clean_ssh_config(profile_name)
    
    # 6. Remove base directory if empty
    base_dir = items['base_directory']
    if base_dir and base_dir.exists() and base_dir.is_dir():
        try:
            if not any(base_dir.iterdir()):  # Directory is empty
                base_dir.rmdir()
                console.print(f"   ✅ Removed empty base directory")
            else:
                console.print(f"   ⚠️  Base directory has files - keeping it")
        except Exception as e:
            console.print(f"   ❌ Failed to remove base directory: {e}")
    
    # 7. Remove profile from profiles.yaml
    if config_manager.delete_profile(profile_name):
        console.print(f"   ✅ Removed profile entry")
    else:
        console.print(f"   ❌ Failed to remove profile entry")


def _clean_git_config(profile_name: str) -> None:
    """Remove includeIf entries from main Git config."""
    gitconfig_path = Path.home() / '.gitconfig'
    
    if not gitconfig_path.exists():
        return
    
    try:
        with open(gitconfig_path, 'r') as f:
            lines = f.readlines()
        
        # Filter out lines related to this profile
        filtered_lines = []
        skip_section = False
        
        for line in lines:
            line_stripped = line.strip()
            
            # Check if this is the start of our includeIf section
            if f'gitdir:{profile_name}' in line_stripped or f'gitconfig-{profile_name}' in line_stripped:
                skip_section = True
                continue
            
            # Check if we're starting a new section
            if line_stripped.startswith('[') and skip_section:
                skip_section = False
            
            if not skip_section:
                filtered_lines.append(line)
        
        # Write back the cleaned config
        with open(gitconfig_path, 'w') as f:
            f.writelines(filtered_lines)
        
        console.print(f"   ✅ Cleaned Git config includeIf entries")
        
    except Exception as e:
        console.print(f"   ❌ Failed to clean Git config: {e}")


def _clean_ssh_config(profile_name: str) -> None:
    """Remove SSH host entries from SSH config."""
    ssh_config_path = Path.home() / '.ssh' / 'config'
    
    if not ssh_config_path.exists():
        return
    
    try:
        with open(ssh_config_path, 'r') as f:
            lines = f.readlines()
        
        # Filter out lines related to this profile
        filtered_lines = []
        skip_section = False
        
        for line in lines:
            line_stripped = line.strip()
            
            # Check if this is the start of our host section
            if line_stripped.startswith('Host ') and profile_name in line_stripped:
                skip_section = True
                continue
            
            # Check if we're starting a new Host section
            if line_stripped.startswith('Host ') and skip_section:
                skip_section = False
            
            # Skip empty lines after our section
            if skip_section and not line_stripped:
                continue
            
            if not skip_section:
                filtered_lines.append(line)
        
        # Write back the cleaned config
        with open(ssh_config_path, 'w') as f:
            f.writelines(filtered_lines)
        
        console.print(f"   ✅ Cleaned SSH config entries")
        
    except Exception as e:
        console.print(f"   ❌ Failed to clean SSH config: {e}")