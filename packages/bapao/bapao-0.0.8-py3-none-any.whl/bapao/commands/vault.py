"""
Vault management commands for BAPAO.
Handles quantum-safe encryption/decryption of all profile data.
"""

import click
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.text import Text

from bapao.core.quantum_crypto import VaultManager, QuantumSafeError, VaultLockedError, InvalidVaultPasswordError

console = Console()


@click.group(name='vault')
def vault_commands():
    """🔐 Quantum-safe vault management commands."""
    pass


@vault_commands.command(name='init')
@click.option('--vault-path', type=click.Path(), help='Custom vault directory path')
def init_vault(vault_path):
    """
    Initialize a new quantum-safe vault for BAPAO.
    
    Creates encrypted storage using Kyber-1024 + Dilithium-5 post-quantum cryptography.
    All profile data will be encrypted at rest and require unlock to access.
    """
    console.print()
    console.print("🔐 [bold blue]BAPAO Quantum-Safe Vault Initialization[/bold blue]")
    console.print("=" * 55)
    console.print()
    
    # Security warning and information
    security_info = Text.assemble(
        ("🛡️  QUANTUM-SAFE SECURITY FEATURES:\n", "bold green"),
        ("• ", "dim"), ("Kyber-1024 post-quantum key encapsulation\n", "green"),
        ("• ", "dim"), ("Dilithium-5 quantum-resistant digital signatures\n", "green"), 
        ("• ", "dim"), ("AES-256-GCM authenticated encryption\n", "green"),
        ("• ", "dim"), ("Argon2id memory-hard password derivation\n", "green"),
        ("• ", "dim"), ("SHA3-512 quantum-resistant hashing\n", "green"),
        ("\n"),
        ("⚠️  SECURITY REQUIREMENTS:\n", "bold yellow"),
        ("• ", "dim"), ("Use a STRONG master password (recommended: 20+ chars)\n", "yellow"),
        ("• ", "dim"), ("Master password cannot be recovered if lost\n", "yellow"),
        ("• ", "dim"), ("All existing profiles will be migrated to vault\n", "yellow"),
        ("• ", "dim"), ("Backup your vault files after initialization\n", "yellow")
    )
    
    security_panel = Panel(
        security_info,
        title="[bold red]🔒 QUANTUM-SAFE VAULT SECURITY[/bold red]",
        border_style="red",
        padding=(1, 2)
    )
    console.print(security_panel)
    console.print()
    
    # Initialize vault manager
    vault_dir = Path(vault_path) if vault_path else None
    vault = VaultManager(vault_dir)
    
    # Check if vault already exists
    if vault.is_vault_initialized():
        console.print("❌ [red]Vault already initialized![/red]")
        console.print(f"📂 Vault location: {vault.vault_dir}")
        console.print("💡 Use 'bapao vault status' to check vault status")
        return
    
    # Get master password
    console.print("🔑 [bold cyan]Create your quantum-safe master password:[/bold cyan]")
    console.print("   [dim]This will be used to encrypt/decrypt your entire vault[/dim]")
    console.print()
    
    while True:
        password1 = Prompt.ask("Enter master password", password=True)
        
        if len(password1) < 12:
            console.print("❌ [red]Password must be at least 12 characters long[/red]")
            continue
        
        password2 = Prompt.ask("Confirm master password", password=True)
        
        if password1 != password2:
            console.print("❌ [red]Passwords do not match[/red]")
            continue
        
        # Password strength check
        strength_score = _calculate_password_strength(password1)
        
        if strength_score < 3:
            console.print(f"⚠️  [yellow]Password strength: {strength_score}/5[/yellow]")
            console.print("💡 [dim]Consider adding numbers, symbols, or making it longer[/dim]")
            
            if not Confirm.ask("Continue with this password?"):
                continue
        else:
            console.print(f"✅ [green]Password strength: {strength_score}/5 - Excellent![/green]")
        
        break
    
    console.print()
    console.print("🔄 [yellow]Initializing quantum-safe vault...[/yellow]")
    
    try:
        # Initialize the vault
        vault.initialize_vault(password1)
        
        console.print()
        console.print("🎉 [bold green]Vault initialized successfully![/bold green]")
        console.print(f"📂 Vault location: {vault.vault_dir}")
        console.print()
        console.print("🔒 [yellow]Vault is now LOCKED by default[/yellow]")
        console.print("💡 Next steps:")
        console.print("   1. Run 'bapao vault unlock' to access your profiles")
        console.print("   2. Create profiles with 'bapao init <profile-name>'")
        console.print("   3. Run 'bapao vault lock' when done to secure everything")
        console.print()
        console.print("🔐 [bold blue]Your data is now quantum-safe and encrypted![/bold blue]")
        
        # Clear password from memory
        password1 = "0" * len(password1)
        password2 = "0" * len(password2)
        
    except QuantumSafeError as e:
        console.print(f"❌ [red]Failed to initialize vault: {e}[/red]")
        raise click.ClickException(f"Vault initialization failed: {e}")


@vault_commands.command(name='unlock')  
@click.option('--vault-path', type=click.Path(), help='Custom vault directory path')
def unlock_vault(vault_path):
    """
    Unlock quantum-safe vault for profile access.
    
    Decrypts all profile data using your master password and loads it into memory.
    Allows normal BAPAO operations until vault is locked again.
    """
    console.print()
    console.print("🔓 [bold blue]Unlocking BAPAO Quantum-Safe Vault[/bold blue]")
    console.print("=" * 45)
    console.print()
    
    # Initialize vault manager
    vault_dir = Path(vault_path) if vault_path else None
    vault = VaultManager(vault_dir)
    
    # Check if vault is initialized
    if not vault.is_vault_initialized():
        console.print("❌ [red]Vault not initialized![/red]")
        console.print("💡 Run 'bapao vault init' to create a new vault")
        raise click.ClickException("Vault not initialized")
    
    # Check if already unlocked
    if not vault.is_vault_locked():
        console.print("🔓 [green]Vault is already unlocked![/green]")
        console.print(f"📂 Vault location: {vault.vault_dir}")
        console.print("💡 Use 'bapao vault status' to see vault information")
        return
    
    # Get master password
    console.print("🔑 [cyan]Enter your master password to unlock the vault:[/cyan]")
    
    max_attempts = 3
    for attempt in range(max_attempts):
        password = Prompt.ask("Master password", password=True)
        
        try:
            console.print("🔄 [yellow]Verifying password and unlocking vault...[/yellow]")
            vault.unlock_vault(password)
            
            # Success!
            console.print()
            console.print("🎉 [bold green]Vault unlocked successfully![/bold green]")
            console.print()
            
            # Show vault status
            profiles = vault.get_profiles()
            console.print(f"📊 [blue]Vault contains {len(profiles)} profile(s)[/blue]")
            
            if profiles:
                console.print("📋 Available profiles:")
                for profile_name in profiles.keys():
                    console.print(f"   • {profile_name}")
            
            console.print()
            console.print("✅ [green]You can now use all BAPAO commands normally[/green]")
            console.print("🔒 [yellow]Remember to run 'bapao vault lock' when done[/yellow]")
            
            # Clear password from memory
            password = "0" * len(password)
            return
            
        except InvalidVaultPasswordError:
            attempts_left = max_attempts - attempt - 1
            if attempts_left > 0:
                console.print(f"❌ [red]Invalid password. {attempts_left} attempt(s) remaining.[/red]")
            else:
                console.print("❌ [red]Invalid password. Maximum attempts exceeded.[/red]")
                console.print("🔒 [yellow]Vault remains locked for security.[/yellow]")
                raise click.ClickException("Authentication failed")
        
        except QuantumSafeError as e:
            console.print(f"❌ [red]Vault error: {e}[/red]")
            raise click.ClickException(f"Failed to unlock vault: {e}")
        
        # Clear password attempt from memory
        password = "0" * len(password)


@vault_commands.command(name='lock')
@click.option('--vault-path', type=click.Path(), help='Custom vault directory path')  
def lock_vault(vault_path):
    """
    Lock quantum-safe vault and secure all data.
    
    Clears decrypted profile data from memory and locks the vault.
    All subsequent BAPAO operations will require unlocking the vault first.
    """
    console.print()
    console.print("🔒 [bold blue]Locking BAPAO Quantum-Safe Vault[/bold blue]")
    console.print("=" * 43)
    console.print()
    
    # Initialize vault manager
    vault_dir = Path(vault_path) if vault_path else None
    vault = VaultManager(vault_dir)
    
    # Check if vault is initialized
    if not vault.is_vault_initialized():
        console.print("❌ [red]Vault not initialized![/red]")
        console.print("💡 Run 'bapao vault init' to create a new vault")
        raise click.ClickException("Vault not initialized")
    
    # Check if already locked
    if vault.is_vault_locked():
        console.print("🔒 [yellow]Vault is already locked![/yellow]")
        console.print(f"📂 Vault location: {vault.vault_dir}")
        console.print("💡 Use 'bapao vault unlock' to access your profiles")
        return
    
    try:
        console.print("🔄 [yellow]Securing vault and clearing memory...[/yellow]")
        vault.lock_vault()
        
        console.print()
        console.print("🎉 [bold green]Vault locked successfully![/bold green]")
        console.print()
        console.print("🔒 [blue]All profile data is now encrypted and secured[/blue]")
        console.print("🧹 [dim]Sensitive data cleared from memory[/dim]")
        console.print()
        console.print("💡 To access profiles again:")
        console.print("   Run 'bapao vault unlock' with your master password")
        
    except QuantumSafeError as e:
        console.print(f"❌ [red]Failed to lock vault: {e}[/red]")
        raise click.ClickException(f"Vault locking failed: {e}")


@vault_commands.command(name='status')
@click.option('--vault-path', type=click.Path(), help='Custom vault directory path')
def vault_status(vault_path):
    """
    Show quantum-safe vault status and information.
    
    Displays vault initialization status, lock state, and security information
    without requiring vault unlock.
    """
    console.print()
    console.print("📊 [bold blue]BAPAO Quantum-Safe Vault Status[/bold blue]")
    console.print("=" * 42)
    console.print()
    
    # Initialize vault manager
    vault_dir = Path(vault_path) if vault_path else None
    vault = VaultManager(vault_dir)
    
    # Vault location
    console.print(f"📂 [blue]Vault Location:[/blue] {vault.vault_dir}")
    console.print()
    
    # Check initialization status
    if not vault.is_vault_initialized():
        console.print("❌ [red]Vault Status: NOT INITIALIZED[/red]")
        console.print()
        console.print("💡 [yellow]Next Steps:[/yellow]")
        console.print("   Run 'bapao vault init' to create your quantum-safe vault")
        console.print("   This will encrypt all your profile data with post-quantum algorithms")
        return
    
    console.print("✅ [green]Vault Status: INITIALIZED[/green]")
    
    # Lock status
    is_locked = vault.is_vault_locked()
    if is_locked:
        console.print("🔒 [red]Lock Status: LOCKED[/red]")
        console.print("   [dim]All profile data is encrypted and inaccessible[/dim]")
    else:
        console.print("🔓 [green]Lock Status: UNLOCKED[/green]")
        console.print("   [dim]Profile data is decrypted and accessible[/dim]")
        
        # Show profile count if unlocked
        try:
            profiles = vault.get_profiles()
            console.print(f"   [dim]Contains {len(profiles)} profile(s)[/dim]")
        except:
            pass
    
    console.print()
    
    # Vault files status
    console.print("📁 [blue]Vault Files:[/blue]")
    files_status = [
        (vault.vault_file, "Encrypted Data", "vault.kyb"),
        (vault.signature_file, "Digital Signature", "vault.sig"), 
        (vault.metadata_file, "Metadata", "vault.meta"),
        (vault.lock_file, "Lock Status", ".locked")
    ]
    
    for file_path, description, filename in files_status:
        if file_path.exists():
            size = file_path.stat().st_size
            console.print(f"   ✅ {description:<20} ({filename}) - {size:,} bytes")
        else:
            console.print(f"   ❌ {description:<20} ({filename}) - Missing")
    
    console.print()
    
    # Security information
    if vault.metadata_file.exists():
        import json
        metadata = json.loads(vault.metadata_file.read_text())
        
        console.print("🔐 [blue]Security Information:[/blue]")
        console.print(f"   Algorithm: {metadata.get('algorithm', 'Unknown')}")
        console.print(f"   Quantum Safe: {'Yes' if metadata.get('quantum_safe', False) else 'No'}")
        console.print(f"   Post-Quantum Ready: {'Yes' if metadata.get('post_quantum_ready', False) else 'No'}")
        
        created_at = metadata.get('created_at')
        if created_at:
            import datetime
            created_time = datetime.datetime.fromtimestamp(created_at)
            console.print(f"   Created: {created_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    console.print()
    
    # Usage instructions
    console.print("💡 [blue]Available Commands:[/blue]")
    if is_locked:
        console.print("   bapao vault unlock  - Unlock vault with master password")
    else:
        console.print("   bapao vault lock    - Lock vault and secure data")
    
    console.print("   bapao vault backup  - Create encrypted backup")
    console.print("   bapao vault restore - Restore from backup")


@vault_commands.command(name='backup')
@click.option('--vault-path', type=click.Path(), help='Custom vault directory path')
@click.option('--backup-path', type=click.Path(), help='Backup destination path')
def backup_vault(vault_path, backup_path):
    """
    Create encrypted backup of quantum-safe vault.
    
    Creates a portable backup of your entire vault that can be restored
    on another machine or used for disaster recovery.
    """
    console.print()
    console.print("💾 [bold blue]BAPAO Vault Backup[/bold blue]")
    console.print("=" * 25)
    console.print()
    
    # Initialize vault manager
    vault_dir = Path(vault_path) if vault_path else None
    vault = VaultManager(vault_dir)
    
    # Check if vault is initialized
    if not vault.is_vault_initialized():
        console.print("❌ [red]Vault not initialized![/red]")
        console.print("💡 Run 'bapao vault init' to create a vault first")
        raise click.ClickException("Vault not initialized")
    
    # Determine backup path
    if backup_path is None:
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = Path.cwd() / f"bapao_vault_backup_{timestamp}.tar.gz"
    else:
        backup_path = Path(backup_path)
    
    console.print(f"📂 [blue]Source:[/blue] {vault.vault_dir}")
    console.print(f"💾 [blue]Backup:[/blue] {backup_path}")
    console.print()
    
    try:
        import tarfile
        import tempfile
        
        console.print("🔄 [yellow]Creating encrypted backup...[/yellow]")
        
        # Create compressed backup
        with tarfile.open(backup_path, 'w:gz') as tar:
            tar.add(vault.vault_file, arcname='vault.kyb')
            tar.add(vault.signature_file, arcname='vault.sig') 
            tar.add(vault.metadata_file, arcname='vault.meta')
            if vault.lock_file.exists():
                tar.add(vault.lock_file, arcname='.locked')
        
        backup_size = backup_path.stat().st_size
        
        console.print()
        console.print("🎉 [bold green]Backup created successfully![/bold green]")
        console.print(f"💾 Backup file: {backup_path}")
        console.print(f"📊 Backup size: {backup_size:,} bytes")
        console.print()
        console.print("🔐 [blue]Your backup is quantum-safe encrypted[/blue]")
        console.print("💡 Store this backup in a secure location")
        console.print("⚠️  You'll need your master password to restore it")
        
    except Exception as e:
        console.print(f"❌ [red]Backup failed: {e}[/red]")
        raise click.ClickException(f"Backup creation failed: {e}")


@vault_commands.command(name='migrate')
@click.option('--vault-path', type=click.Path(), help='Custom vault directory path')
@click.option('--force', is_flag=True, help='Force migration without confirmation prompts')
def migrate_to_vault(vault_path, force):
    """
    Migrate legacy profile data to quantum-safe vault storage.
    
    This command will:
    - Check for existing legacy profile data
    - Initialize a new quantum-safe vault (if needed)
    - Migrate all profiles to encrypted vault storage
    - Backup legacy data before removal
    
    Migration is safe and reversible - your original data is preserved.
    """
    console.print()
    console.print("🔄 [bold blue]Migrate to Quantum-Safe Vault[/bold blue]")
    console.print("=" * 38)
    console.print()
    
    # Initialize config manager in legacy mode to check for existing data
    from ..core.config import ConfigManager
    config = ConfigManager(use_vault=False)  # Force legacy mode to check for files
    
    # Check for legacy profiles
    if not config.profiles_file.exists():
        console.print("❌ [red]No legacy profile data found![/red]")
        console.print(f"   Looked for: {config.profiles_file}")
        console.print()
        console.print("💡 [yellow]If you have profiles:[/yellow]")
        console.print("   1. Run 'bapao vault init' to create a new vault")
        console.print("   2. Create profiles normally with 'bapao init <name>'")
        return
    
    # Load and display legacy profiles
    try:
        legacy_profiles = config._load_legacy_profiles()
    except Exception as e:
        console.print(f"❌ [red]Failed to read legacy profiles: {e}[/red]")
        raise click.ClickException("Cannot read legacy profile data")
    
    if not legacy_profiles:
        console.print("❌ [yellow]Legacy profile file exists but contains no profiles[/yellow]")
        console.print("💡 No migration needed - you can start fresh with 'bapao vault init'")
        return
    
    console.print(f"📋 [green]Found {len(legacy_profiles)} legacy profile(s) to migrate:[/green]")
    for name, profile in legacy_profiles.items():
        console.print(f"   • {name} ({profile.git_email})")
    console.print()
    
    # Initialize vault manager for migration
    vault_dir = Path(vault_path) if vault_path else None
    vault = VaultManager(vault_dir)
    
    # Check if vault already exists
    vault_exists = vault.is_vault_initialized()
    if vault_exists:
        console.print("🔍 [yellow]Quantum-safe vault already exists[/yellow]")
        console.print(f"📂 Vault location: {vault.vault_dir}")
        
        if not vault.is_vault_unlocked():
            console.print("🔒 [red]Vault is currently locked[/red]")
            console.print("💡 Please unlock the vault first: bapao vault unlock")
            return
            
        # Check for existing profiles in vault
        try:
            vault_profiles = vault.get_profiles()
            if vault_profiles:
                console.print(f"⚠️  [yellow]Vault already contains {len(vault_profiles)} profile(s)[/yellow]")
                if not force:
                    if not Confirm.ask("Merge legacy profiles with existing vault profiles?"):
                        console.print("🚫 Migration cancelled by user")
                        return
        except Exception as e:
            console.print(f"❌ [red]Error accessing vault: {e}[/red]")
            return
    else:
        console.print("🆕 [cyan]No quantum-safe vault found - will create new one[/cyan]")
    
    # Confirm migration
    if not force:
        console.print()
        migration_info = Text()
        migration_info.append("🔄 Migration Process:\n", style="bold blue")
        migration_info.append("  1. ", style="dim")
        migration_info.append("Initialize quantum-safe vault (if needed)\n", style="white")
        migration_info.append("  2. ", style="dim")
        migration_info.append("Encrypt and store all profiles in vault\n", style="white")
        migration_info.append("  3. ", style="dim")
        migration_info.append("Backup legacy file as .legacy\n", style="white")
        migration_info.append("  4. ", style="dim")
        migration_info.append("Remove original legacy file\n", style="white")
        migration_info.append("\n🔐 Security Benefits:\n", style="bold green")
        migration_info.append("  • ", style="dim")
        migration_info.append("Quantum-safe encryption (Kyber-1024 + Dilithium-5)\n", style="green")
        migration_info.append("  • ", style="dim")
        migration_info.append("Zero-trust architecture with vault locking\n", style="green")
        migration_info.append("  • ", style="dim")
        migration_info.append("Protection against future quantum attacks\n", style="green")
        
        migration_panel = Panel(
            migration_info,
            title="[bold yellow]⚡ QUANTUM-SAFE MIGRATION[/bold yellow]",
            border_style="yellow",
            padding=(1, 2)
        )
        console.print(migration_panel)
        console.print()
        
        if not Confirm.ask("🚀 Proceed with quantum-safe migration?"):
            console.print("🚫 Migration cancelled by user")
            return
    
    # Get master password if vault doesn't exist
    master_password = None
    if not vault_exists:
        console.print()
        console.print("🔑 [bold cyan]Create master password for your new vault:[/bold cyan]")
        
        while True:
            password1 = Prompt.ask("Enter master password", password=True)
            
            if len(password1) < 12:
                console.print("❌ [red]Password must be at least 12 characters long[/red]")
                continue
            
            password2 = Prompt.ask("Confirm master password", password=True)
            
            if password1 != password2:
                console.print("❌ [red]Passwords do not match[/red]")
                continue
            
            strength_score = _calculate_password_strength(password1)
            
            if strength_score < 3:
                console.print(f"⚠️  [yellow]Password strength: {strength_score}/5[/yellow]")
                if not force and not Confirm.ask("Continue with this password?"):
                    continue
            
            master_password = password1
            break
    
    # Perform the migration
    console.print()
    console.print("🔄 [yellow]Starting quantum-safe migration...[/yellow]")
    
    try:
        # Initialize vault manager with vault support
        config_with_vault = ConfigManager(use_vault=True)
        
        if master_password:
            # Initialize new vault
            vault.initialize_vault(master_password)
            console.print("✅ [green]New quantum-safe vault created[/green]")
            
            # Unlock for migration
            vault.unlock_vault(master_password)
            console.print("🔓 [green]Vault unlocked for migration[/green]")
        
        # Perform the migration
        migrated = config_with_vault.migrate_to_vault(master_password or "")
        
        if migrated:
            console.print("✅ [green]Profile data migrated successfully[/green]")
            console.print(f"📂 Legacy data backed up to: {config.profiles_file.with_suffix('.yaml.legacy')}")
        else:
            console.print("⚠️  [yellow]No profiles found to migrate[/yellow]")
        
        console.print()
        console.print("🎉 [bold green]Migration completed successfully![/bold green]")
        console.print()
        console.print("✅ [blue]Your profiles are now quantum-safe encrypted![/blue]")
        console.print("🔒 [yellow]Vault is unlocked - remember to lock it when done:[/yellow]")
        console.print("   bapao vault lock")
        console.print()
        console.print("💡 [dim]All future profile operations will use the secure vault[/dim]")
        
        # Clear password from memory
        if master_password:
            master_password = "0" * len(master_password)
        
    except Exception as e:
        console.print(f"❌ [red]Migration failed: {e}[/red]")
        raise click.ClickException(f"Migration error: {e}")


def _calculate_password_strength(password: str) -> int:
    """
    Calculate password strength score (1-5).
    
    Args:
        password: Password to analyze
        
    Returns:
        Strength score from 1 (weak) to 5 (very strong)
    """
    score = 0
    
    # Length bonus
    if len(password) >= 12:
        score += 1
    if len(password) >= 16:
        score += 1
    
    # Character diversity
    if any(c.islower() for c in password):
        score += 1
    if any(c.isupper() for c in password):
        score += 1
    if any(c.isdigit() for c in password):
        score += 1
    if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        score += 1
    
    # Bonus for very long passwords
    if len(password) >= 24:
        score += 1
    
    return min(score, 5)