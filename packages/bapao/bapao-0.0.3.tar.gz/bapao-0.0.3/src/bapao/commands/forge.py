"""
Generate SSH and GPG keys for a profile.
"""

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.config import ConfigManager
from ..core.keys import KeyGenerator

console = Console()


@click.command()
@click.argument('profile_name')
@click.pass_context
def forge(ctx, profile_name: str):
    """Generate SSH and GPG keys for a profile.
    
    PROFILE_NAME: Name of the profile to generate keys for
    
    This command will:
    - Generate an Ed25519 SSH key pair
    - Generate a GPG key for signing commits
    - Update the profile with key information
    
    Example:
        bapao forge work
    """
    config: ConfigManager = ctx.obj['config']
    
    # Load the profile
    profile = config.get_profile(profile_name)
    if not profile:
        console.print(f"[red]❌ Profile '{profile_name}' not found.[/red]")
        console.print("Run [cyan]bapao init[/cyan] to create it first.")
        return
    
    console.print(f"[cyan]🔨 Forging keys for profile: {profile_name}[/cyan]")
    console.print()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        # Generate SSH key
        ssh_task = progress.add_task("Generating SSH key...", total=None)
        try:
            private_key_path, public_key_path = KeyGenerator.generate_ssh_key(
                profile_name, profile.git_email
            )
            profile.ssh_key_path = str(private_key_path)
            progress.update(ssh_task, description="✅ SSH key generated")
            
            console.print(f"   Private key: {private_key_path}")
            console.print(f"   Public key:  {public_key_path}")
            
        except Exception as e:
            progress.update(ssh_task, description="❌ SSH key generation failed")
            console.print(f"[red]Failed to generate SSH key: {e}[/red]")
            return
        
        # Generate GPG key
        gpg_task = progress.add_task("Generating GPG key...", total=None)
        try:
            fingerprint = KeyGenerator.generate_gpg_key(
                profile.git_name, profile.git_email, profile_name
            )
            if fingerprint:
                profile.gpg_key_fingerprint = fingerprint
                progress.update(gpg_task, description="✅ GPG key generated")
                console.print(f"   GPG fingerprint: {fingerprint}")
            else:
                progress.update(gpg_task, description="⚠️  GPG key generation skipped")
                console.print("   [yellow]GPG not available or key generation failed[/yellow]")
                
        except Exception as e:
            progress.update(gpg_task, description="❌ GPG key generation failed")
            console.print(f"[yellow]GPG key generation failed: {e}[/yellow]")
        
        # Save profile updates
        save_task = progress.add_task("Saving profile...", total=None)
        try:
            from datetime import datetime
            profile.updated_at = datetime.now().isoformat()
            config.create_profile(profile)
            progress.update(save_task, description="✅ Profile updated")
            
        except Exception as e:
            progress.update(save_task, description="❌ Profile save failed")
            console.print(f"[red]Failed to save profile: {e}[/red]")
            return
    
    console.print()
    console.print("[green]🎉 Keys forged successfully![/green]")
    console.print()
    console.print("[cyan]Next steps:[/cyan]")
    console.print(f"   bapao wire {profile_name}   # Configure Git and SSH")
    console.print(f"   bapao verify {profile_name} # Verify setup")
    
    if profile.gpg_key_fingerprint:
        console.print()
        console.print("[cyan]📋 Add this public key to your Git hosting service:[/cyan]")
        console.print(f"   SSH: {public_key_path}")
        if fingerprint:
            console.print(f"   GPG: gpg --armor --export {fingerprint}")