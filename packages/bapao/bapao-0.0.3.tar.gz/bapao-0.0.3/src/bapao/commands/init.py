"""
Initialize a new BAPAO profile.
"""

import click
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt

from ..core.config import ConfigManager, Profile

console = Console()


@click.command()
@click.argument('profile_name')
@click.option('--name', help='Git name for commits')
@click.option('--email', help='Git email for commits')  
@click.option('--base-dir', help='Base working directory for this profile')
@click.option('--host-alias', help='Git host alias (e.g. github.com-work)')
@click.pass_context
def init(ctx, profile_name: str, name: str, email: str, base_dir: str, host_alias: str):
    """Initialize a new BAPAO profile.
    
    PROFILE_NAME: Name of the profile to create
    
    Example:
        bapao init work --name "John Doe" --email john@company.com
    """
    config: ConfigManager = ctx.obj['config']
    
    # Check if profile already exists
    if config.profile_exists(profile_name):
        console.print(f"[yellow]Profile '{profile_name}' already exists.[/yellow]")
        if not click.confirm("Do you want to update it?"):
            return
    
    # Interactive prompts for missing information
    if not name:
        name = Prompt.ask("Enter your Git name")
    
    if not email:
        email = Prompt.ask("Enter your Git email")
    
    if not base_dir:
        default_base = str(Path.home() / "code" / profile_name)
        base_dir = Prompt.ask(
            f"Enter base working directory", 
            default=default_base
        )
    
    # Expand and resolve the base directory path
    base_dir = str(Path(base_dir).expanduser().resolve())
    
    # Create base directory if it doesn't exist
    Path(base_dir).mkdir(parents=True, exist_ok=True)
    
    # Generate default host alias if not provided
    if not host_alias:
        # Smart default based on profile name
        if 'gitlab' in profile_name.lower():
            host_alias = f"gitlab.com-{profile_name}"
        elif 'bitbucket' in profile_name.lower():
            host_alias = f"bitbucket.org-{profile_name}"
        else:
            host_alias = f"github.com-{profile_name}"
    
    # Create the profile
    profile = Profile(
        name=profile_name,
        git_name=name,
        git_email=email,
        base_directory=base_dir,
        git_host_alias=host_alias,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )
    
    try:
        config.create_profile(profile)
        
        console.print(f"[green]✅ Profile '{profile_name}' created successfully![/green]")
        console.print(f"   Git Name: {name}")
        console.print(f"   Git Email: {email}")
        console.print(f"   Base Directory: {base_dir}")
        console.print(f"   Host Alias: {host_alias}")
        console.print()
        console.print("[cyan]Next steps:[/cyan]")
        console.print(f"   bapao forge {profile_name}  # Generate SSH and GPG keys")
        console.print(f"   bapao wire {profile_name}   # Configure Git and SSH")
        console.print(f"   bapao verify {profile_name} # Verify setup")
        
    except Exception as e:
        console.print(f"[red]❌ Failed to create profile: {e}[/red]")