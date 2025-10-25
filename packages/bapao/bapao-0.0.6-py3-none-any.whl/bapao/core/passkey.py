"""
Passkey generation and management for BAPAO.
Generates cryptographically secure 64-character passphrases for SSH and GPG keys.
"""

import secrets
import string
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.text import Text

console = Console()


class PasskeyGenerator:
    """Handles secure passkey generation and display."""
    
    @staticmethod
    def generate_passkey(length: int = 64) -> str:
        """Generate a cryptographically secure passkey.
        
        Args:
            length: Length of the passkey (default: 64)
            
        Returns:
            Secure random passkey string
        """
        # Use a mix of letters, digits, and safe special characters
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*+-=?"
        passkey = ''.join(secrets.choice(alphabet) for _ in range(length))
        return passkey
    
    @staticmethod
    def display_passkey_securely(passkey: str, profile_name: str) -> bool:
        """Display passkey securely and wait for user confirmation.
        
        Args:
            passkey: The generated passkey to display
            profile_name: Name of the profile this passkey is for
            
        Returns:
            True if user confirmed they saved it, False otherwise
        """
        console.print()
        console.print("🔐 [bold yellow]Generated 64-character passkey for SSH and GPG keys:[/bold yellow]")
        console.print()
        
        # Display passkey in a secure, highlighted box
        passkey_text = Text(passkey, style="bold green on black")
        passkey_panel = Panel(
            passkey_text,
            title=f"[bold red]🔑 PASSKEY FOR PROFILE: {profile_name.upper()}[/bold red]",
            title_align="center",
            border_style="red",
            padding=(1, 2)
        )
        console.print(passkey_panel)
        
        console.print()
        console.print("⚠️  [bold red]CRITICAL SECURITY INSTRUCTIONS:[/bold red]")
        console.print("   1. [yellow]SAVE THIS PASSKEY TO YOUR PASSWORD MANAGER IMMEDIATELY![/yellow]")
        console.print("   2. [yellow]Use the suggested title for easy identification[/yellow]")
        console.print("   3. [yellow]This passkey will NOT be stored anywhere in BAPAO[/yellow]")
        console.print("   4. [yellow]Without this passkey, your keys are completely useless[/yellow]")
        console.print()
        
        # Confirmation prompt
        saved = Confirm.ask(
            "[bold cyan]Have you securely saved this passkey to your password manager?[/bold cyan]"
        )
        
        if saved:
            console.print("✅ [green]Passkey confirmed saved! Continuing with key generation...[/green]")
            console.print()
            return True
        else:
            console.print("❌ [red]Please save the passkey before continuing.[/red]")
            return False
    
    @staticmethod
    def get_passkey_hint(profile_name: str) -> str:
        """Generate a helpful hint for storing passkeys in password managers."""
        return f"Store in your password manager as 'BAPAO-{profile_name}'"
    
    @staticmethod
    def prompt_for_passkey_usage(profile_name: str) -> None:
        """Show information about using the passkey.
        
        Args:
            profile_name: Name of the profile
        """
        console.print(f"🔐 [yellow]This profile uses a passkey for SSH and GPG operations.[/yellow]")
        console.print(f"📝 [dim]Passkey hint: {PasskeyGenerator.get_passkey_hint(profile_name)}[/dim]")
        console.print("💡 [dim]When prompted for SSH key or GPG passphrase, use your saved passkey.[/dim]")
        console.print()