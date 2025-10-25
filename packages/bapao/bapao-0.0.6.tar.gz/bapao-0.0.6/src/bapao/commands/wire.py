"""
Configure Git and SSH settings for a profile.
"""

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.config import ConfigManager
from ..core.git_ssh import GitConfigManager, SSHConfigManager

console = Console()


@click.command()
@click.argument('profile_name')
@click.option('--force', is_flag=True, help='Force overwrite existing configurations')
@click.pass_context
def wire(ctx, profile_name: str, force: bool):
    """Configure Git and SSH settings for a profile.
    
    PROFILE_NAME: Name of the profile to configure
    
    This command will:
    - Create a profile-specific .gitconfig file
    - Add includeIf directive to main .gitconfig
    - Configure SSH host aliases in ~/.ssh/config
    
    Example:
        bapao wire work
        bapao wire work --force  # Overwrite existing configs
    """
    config: ConfigManager = ctx.obj['config']
    
    # Load the profile
    profile = config.get_profile(profile_name)
    if not profile:
        console.print(f"[red]❌ Profile '{profile_name}' not found.[/red]")
        console.print("Run [cyan]bapao init[/cyan] to create it first.")
        return
    
    console.print(f"[cyan]🔌 Wiring configuration for profile: {profile_name}[/cyan]")
    console.print()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        # Create profile-specific Git config
        git_task = progress.add_task("Configuring Git settings...", total=None)
        try:
            GitConfigManager.create_profile_gitconfig(profile, force=force)
            profile_config_path = GitConfigManager.get_profile_gitconfig_path(profile.name)
            progress.update(git_task, description="✅ Profile Git config created")
            console.print(f"   Created: {profile_config_path}")
            
        except Exception as e:
            progress.update(git_task, description="❌ Git config creation failed")
            console.print(f"[red]Failed to create Git config: {e}[/red]")
            return
        
        # Add includeIf block to main .gitconfig
        include_task = progress.add_task("Adding Git includeIf directive...", total=None)
        try:
            GitConfigManager.add_include_if_block(profile)
            gitconfig_path = GitConfigManager.get_gitconfig_path()
            progress.update(include_task, description="✅ Git includeIf added")
            console.print(f"   Updated: {gitconfig_path}")
            
        except Exception as e:
            progress.update(include_task, description="❌ Git includeIf addition failed")
            console.print(f"[red]Failed to update .gitconfig: {e}[/red]")
            return
        
        # Configure SSH host alias
        if profile.ssh_key_path and profile.git_host_alias:
            ssh_task = progress.add_task("Configuring SSH host alias...", total=None)
            try:
                SSHConfigManager.add_host_config(profile)
                ssh_config_path = SSHConfigManager.get_ssh_config_path()
                progress.update(ssh_task, description="✅ SSH config updated")
                console.print(f"   Updated: {ssh_config_path}")
                console.print(f"   Host alias: {profile.git_host_alias}")
                
            except Exception as e:
                progress.update(ssh_task, description="❌ SSH config update failed")
                console.print(f"[red]Failed to update SSH config: {e}[/red]")
                return
        else:
            console.print("   [yellow]⚠️  SSH key not available, skipping SSH config[/yellow]")
    
    console.print()
    console.print("[green]🎉 Configuration wired successfully![/green]")
    console.print()
    console.print("[cyan]How to use:[/cyan]")
    console.print(f"   cd {profile.base_directory}")
    console.print(f"   git clone git@{profile.git_host_alias}:user/repo.git")
    console.print("   # Git will automatically use the correct identity and signing key!")
    console.print()
    console.print("[cyan]Next step:[/cyan]")
    console.print(f"   bapao verify {profile_name} # Verify everything is working")