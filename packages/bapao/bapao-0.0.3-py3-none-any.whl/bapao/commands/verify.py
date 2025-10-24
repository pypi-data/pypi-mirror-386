"""
Verify that a profile is correctly set up.
"""

import subprocess
from pathlib import Path
from typing import List, Tuple

import click
from rich.console import Console
from rich.table import Table

from ..core.config import ConfigManager
from ..core.git_ssh import GitConfigManager, SSHConfigManager

console = Console()


def check_ssh_key(ssh_key_path: str) -> Tuple[bool, str]:
    """Check if SSH key exists and is valid.
    
    Returns:
        Tuple of (success, message)
    """
    if not ssh_key_path:
        return False, "No SSH key path configured"
    
    key_path = Path(ssh_key_path)
    if not key_path.exists():
        return False, f"SSH key not found: {ssh_key_path}"
    
    # Check permissions
    stat = key_path.stat()
    if stat.st_mode & 0o077:
        return False, f"SSH key has incorrect permissions: {oct(stat.st_mode)[-3:]}"
    
    # Check if public key exists
    pub_key_path = Path(f"{ssh_key_path}.pub")
    if not pub_key_path.exists():
        return False, f"SSH public key not found: {pub_key_path}"
    
    return True, f"SSH key valid: {ssh_key_path}"


def check_gpg_key(fingerprint: str) -> Tuple[bool, str]:
    """Check if GPG key exists and is valid.
    
    Returns:
        Tuple of (success, message)
    """
    if not fingerprint:
        return False, "No GPG key fingerprint configured"
    
    try:
        result = subprocess.run(
            ['gpg', '--list-secret-keys', fingerprint],
            capture_output=True, text=True, check=True
        )
        if 'sec' in result.stdout:
            return True, f"GPG key found: {fingerprint[:16]}..."
        else:
            return False, f"GPG key not found: {fingerprint}"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False, "GPG not available or key not found"


def check_git_config(profile) -> Tuple[bool, str]:
    """Check if Git configuration is correct.
    
    Returns:
        Tuple of (success, message)
    """
    # Check profile-specific config file
    profile_config_path = GitConfigManager.get_profile_gitconfig_path(profile.name)
    if not profile_config_path.exists():
        return False, f"Profile Git config not found: {profile_config_path}"
    
    # Check main .gitconfig for includeIf
    gitconfig_path = GitConfigManager.get_gitconfig_path()
    if not gitconfig_path.exists():
        return False, f"Main Git config not found: {gitconfig_path}"
    
    content = gitconfig_path.read_text()
    include_pattern = f'[includeIf "gitdir:{profile.base_directory}/"]'
    if include_pattern not in content:
        return False, "includeIf directive not found in main .gitconfig"
    
    return True, "Git configuration valid"


def check_ssh_config(profile) -> Tuple[bool, str]:
    """Check if SSH configuration is correct.
    
    Returns:
        Tuple of (success, message)
    """
    if not profile.git_host_alias:
        return False, "No Git host alias configured"
    
    ssh_config_path = SSHConfigManager.get_ssh_config_path()
    if not ssh_config_path.exists():
        return False, f"SSH config not found: {ssh_config_path}"
    
    content = ssh_config_path.read_text()
    host_pattern = f"Host {profile.git_host_alias}"
    if host_pattern not in content:
        return False, f"SSH host alias not found: {profile.git_host_alias}"
    
    return True, f"SSH config valid: {profile.git_host_alias}"


def check_base_directory(base_dir: str) -> Tuple[bool, str]:
    """Check if base directory exists.
    
    Returns:
        Tuple of (success, message)
    """
    dir_path = Path(base_dir)
    if not dir_path.exists():
        return False, f"Base directory not found: {base_dir}"
    
    if not dir_path.is_dir():
        return False, f"Base directory is not a directory: {base_dir}"
    
    return True, f"Base directory exists: {base_dir}"


@click.command()
@click.argument('profile_name')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed verification results')
@click.pass_context
def verify(ctx, profile_name: str, verbose: bool):
    """Verify that a profile is correctly set up.
    
    PROFILE_NAME: Name of the profile to verify
    
    This command checks:
    - SSH key exists and has correct permissions
    - GPG key is available (if configured)
    - Git configuration is correct
    - SSH host alias is configured
    - Base directory exists
    
    Example:
        bapao verify work
        bapao verify work --verbose
    """
    config: ConfigManager = ctx.obj['config']
    
    # Load the profile
    profile = config.get_profile(profile_name)
    if not profile:
        console.print(f"[red]❌ Profile '{profile_name}' not found.[/red]")
        console.print("Run [cyan]bapao init[/cyan] to create it first.")
        return
    
    console.print(f"[cyan]🔍 Verifying profile: {profile_name}[/cyan]")
    console.print()
    
    # Run all checks
    checks = [
        ("Base Directory", lambda: check_base_directory(profile.base_directory)),
        ("SSH Key", lambda: check_ssh_key(profile.ssh_key_path)),
        ("GPG Key", lambda: check_gpg_key(profile.gpg_key_fingerprint)),
        ("Git Config", lambda: check_git_config(profile)),
        ("SSH Config", lambda: check_ssh_config(profile)),
    ]
    
    results = []
    all_passed = True
    
    for check_name, check_func in checks:
        try:
            success, message = check_func()
            results.append((check_name, success, message))
            if not success:
                all_passed = False
        except Exception as e:
            results.append((check_name, False, str(e)))
            all_passed = False
    
    # Create results table
    table = Table(title=f"Verification Results for '{profile_name}'")
    table.add_column("Check", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Details", style="dim" if not verbose else "")
    
    for check_name, success, message in results:
        status = "✅" if success else "❌"
        details = message if verbose else ("OK" if success else "FAIL")
        table.add_row(check_name, status, details)
    
    console.print(table)
    console.print()
    
    if all_passed:
        console.print("[green]🎉 All checks passed! Profile is ready to use.[/green]")
        console.print()
        console.print(f"[cyan]Usage example:[/cyan]")
        console.print(f"   cd {profile.base_directory}")
        console.print(f"   git clone git@{profile.git_host_alias}:user/repo.git")
        console.print("   # Commits will be signed with your GPG key automatically!")
    else:
        console.print("[red]❌ Some checks failed. Run the following to fix issues:[/red]")
        console.print(f"   bapao forge {profile_name}  # Generate missing keys")
        console.print(f"   bapao wire {profile_name}   # Fix configuration")
    
    # Show profile summary
    if verbose:
        console.print()
        console.print("[cyan]Profile Summary:[/cyan]")
        console.print(f"   Name: {profile.git_name}")
        console.print(f"   Email: {profile.git_email}")
        console.print(f"   Base Directory: {profile.base_directory}")
        console.print(f"   SSH Key: {profile.ssh_key_path or 'Not configured'}")
        console.print(f"   GPG Fingerprint: {profile.gpg_key_fingerprint or 'Not configured'}")
        console.print(f"   Git Host Alias: {profile.git_host_alias or 'Not configured'}")
        console.print(f"   Created: {profile.created_at or 'Unknown'}")
        console.print(f"   Updated: {profile.updated_at or 'Unknown'}")