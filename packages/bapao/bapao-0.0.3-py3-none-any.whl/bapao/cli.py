"""
BAPAO CLI - Developer Environment Sync Engine
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .commands.init import init
from .commands.forge import forge
from .commands.wire import wire
from .commands.verify import verify
from .commands.cleanup import cleanup
from .commands.list_profiles import list_profiles
from .core.config import ConfigManager

console = Console()

BANNER = """
██████   █████  ██████   █████   ██████  
██   ██ ██   ██ ██   ██ ██   ██ ██    ██ 
██████  ███████ ██████  ███████ ██    ██ 
██   ██ ██   ██ ██      ██   ██ ██    ██ 
██████  ██   ██ ██      ██   ██  ██████  

Developer Environment Sync Engine
"""


@click.group()
@click.version_option()
@click.pass_context
def cli(ctx):
    """BAPAO - Make your entire development environment portable.
    
    Create isolated profiles with Git identity, SSH keys, GPG signing keys,
    and related configuration. Run one command on a new machine to restore
    everything needed to start working immediately.
    """
    ctx.ensure_object(dict)
    ctx.obj['config'] = ConfigManager()


@cli.command()
def banner():
    """Show the BAPAO banner."""
    console.print(Panel(
        Text(BANNER, style="bold cyan"),
        title="[bold green]BAPAO[/bold green]",
        subtitle="Everything you need, neatly wrapped.",
        border_style="bright_blue"
    ))


# Register commands
cli.add_command(init)
cli.add_command(forge)
cli.add_command(wire)
cli.add_command(verify)
cli.add_command(cleanup)
cli.add_command(list_profiles, name="list")
cli.add_command(banner)


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()