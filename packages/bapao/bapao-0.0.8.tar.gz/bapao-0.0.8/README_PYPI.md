# BAPAO - Developer Environment Sync Engine

**Make your entire development environment portable.**

BAPAO is a command-line tool that manages multiple developer identities and configurations, allowing you to seamlessly switch between different projects, clients, or organizations without configuration conflicts.

## Features

- **Profile Management**: Create isolated developer profiles for different contexts
- **🔐 Passkey Protection**: 64-character secure passphrases for SSH and GPG keys
- **Key Generation**: Automatic SSH (Ed25519) and GPG key generation with encryption
- **Smart Configuration**: Git and SSH configuration with directory-based switching  
- **Host Aliases**: Automatic SSH host alias generation (e.g., `gitlab.com-myprofile`)
- **Health Verification**: Comprehensive profile health checks with security status
- **Interactive Cleanup**: Forensic removal of profiles with zero traces left behind

## Installation

```bash
pip install bapao
```

## 🚀 Recommended Setup (Quantum-Safe)

1. **Initialize Quantum-Safe Vault**
   ```bash
   bapao vault init
   # Creates encrypted vault using post-quantum cryptography
   # Prompts for master password
   ```
2. **Unlock the Vault**
   ```bash
   bapao vault unlock
   # Enter your master password to unlock the vault
   ```
3. **Create a Profile**
   ```bash
   bapao init work --name "John Doe" --email "john@company.com" --base-dir "~/code/work"
   ```
4. **Generate Passkey-Protected Keys**
   ```bash
   bapao forge work
   # Generates 64-character passkey, displays securely for password manager storage
   # Creates SSH and GPG keys protected with the passkey
   ```
5. **Configure Git & SSH**
   ```bash
   bapao wire work
   ```
6. **Verify Everything Works**
   ```bash
   bapao verify work
   ```
7. **Backup Your Vault**
   ```bash
   bapao vault backup ~/backups/vault-backup.tar.gz
   ```
8. **Lock the Vault When Done**
   ```bash
   bapao vault lock
   ```

## 📖 Commands

| Command | Description |
|---------|-------------|
| `bapao vault init` | Initialize a new quantum-safe vault for profile storage |
| `bapao vault unlock` | Unlock the quantum vault for profile operations |
| `bapao vault lock` | Lock the vault and clear sensitive data from memory |
| `bapao vault status` | Check current vault initialization and lock status |
| `bapao vault backup <backup-file>` | Create encrypted backup of the entire vault |
| `bapao vault migrate` | Upgrade vault to newer crypto algorithms |
| `bapao init <profile_name> [options]` | Initialize a new BAPAO profile with Git identity |
| `bapao forge <profile_name>` | Generate SSH Ed25519 and GPG keys for a profile |
| `bapao wire <profile_name> [--force]` | Configure Git and SSH settings for a profile |
| `bapao verify <profile_name>` | Verify profile setup and show health status |
| `bapao list [--verbose]` | List all configured profiles with status |
| `bapao cleanup [profile_name] [options]` | Remove all traces of a profile |
| `bapao banner` | Display the BAPAO ASCII art banner |

## How It Works

### Directory-Based Identity Switching
BAPAO uses Git's `includeIf` feature to automatically switch your identity based on your current directory:

```bash
# Working in ~/code/client-a/ automatically uses client-a profile
cd ~/code/client-a/
git config user.name  # Returns: "Client A Developer"

# Working in ~/code/personal/ automatically uses personal profile  
cd ~/code/personal/
git config user.name  # Returns: "Personal Projects"
```

### SSH Host Aliases
Each profile gets unique SSH host aliases to prevent key conflicts:

```bash
# Instead of: git clone git@gitlab.com:user/repo.git
# Use: git clone git@gitlab.com-myprofile:user/repo.git
```

### Profile Isolation
Each profile maintains:

- 🔐 **Passkey-protected SSH keys** (`~/.ssh/id_ed25519_profilename`)
- 🔐 **Passkey-protected GPG keys** for commit signing
- 📁 **Separate Git configuration** (`~/.gitconfig-profilename`) 
- 🌐 **Isolated SSH host configurations**
- 💾 **Secure passkey hints** (actual passkey stored in your password manager)

## Typical Workflow

1. **Setup**: Create profiles for different contexts (work, personal, clients)
2. **Generate**: Create SSH and GPG keys for each profile
3. **Configure**: Wire up Git and SSH configurations
4. **Work**: Cd into any project directory and your identity switches automatically
5. **Cleanup**: Remove profiles completely when no longer needed

## Example: Multi-Client Setup

```bash
# Client A setup
bapao init client-a --name "Client A Dev" --email "dev@client-a.com" --base-dir "~/code/client-a"
bapao forge client-a  
bapao wire client-a

# Client B setup  
bapao init client-b --name "Client B Developer" --email "developer@client-b.com" --base-dir "~/code/client-b"
bapao forge client-b
bapao wire client-b

# Personal projects
bapao init personal --name "Your Name" --email "you@personal.com" --base-dir "~/code/personal"
bapao forge personal
bapao wire personal

# List all profiles
bapao list --verbose

# Interactive cleanup when done
bapao cleanup
```

Now when you work in any directory, your Git identity, SSH keys, and GPG signing automatically match the appropriate profile.

## Command Details

### Init Command Options

The `bapao init` command supports several options for customization:

```bash
bapao init <profile_name> [OPTIONS]

Options:
  --name TEXT        Git name for commits
  --email TEXT       Git email for commits  
  --base-dir TEXT    Base working directory for this profile
  --host-alias TEXT  Custom Git host alias (auto-generated if not provided)
```

**Example with all options:**
```bash
bapao init work-gitlab \
  --name "John Doe" \
  --email "john.doe@company.com" \
  --base-dir "~/projects/work" \
  --host-alias "gitlab.company.com-work"
```

### Cleanup Command Features

The `bapao cleanup` command offers flexible profile removal:

```bash
# Interactive selection - shows table of all profiles
bapao cleanup

# Remove specific profile with confirmation
bapao cleanup work-profile

# Force removal without confirmation  
bapao cleanup work-profile --force

# Interactive mode (same as no arguments)
bapao cleanup --interactive
```

**What gets removed:**
- SSH private and public keys
- GPG secret and public keys  
- Git configuration files
- SSH host configuration entries
- Profile entry from `~/.config/bapao/profiles.yaml`
- Empty base directory (if specified and empty)

## Configuration

BAPAO stores profiles in `~/.config/bapao/profiles.yaml`. Each profile contains:
- Base directory path
- SSH key paths  
- Git configuration file path
- GPG key fingerprint
- SSH host alias

## Security Features

- **🔐 Passkey Protection**: 64-character cryptographically secure passphrases
- **Ed25519 SSH Keys**: Modern, secure SSH key generation with encryption
- **GPG Integration**: Automatic GPG key creation and Git signing setup with passphrase
- **Zero Trust**: Keys are useless without the passkey from your password manager
- **Forensic Cleanup**: Complete profile removal with zero traces
- **Key Isolation**: Each profile uses dedicated keys to prevent conflicts

## 🔐 Passkey Security Model

### How It Works
1. **Generate**: BAPAO creates a 64-character cryptographically secure passkey
2. **Display**: Passkey shown once in a secure, highlighted format
3. **Store**: User saves passkey to password manager with suggested label
4. **Protect**: Both SSH and GPG keys encrypted with the same passkey
5. **Use**: When Git operations need keys, user enters saved passkey

### Security Benefits
- ✅ **Zero Trust**: Stolen key files are useless without passkey
- ✅ **Single Passkey**: Same 64-char key protects both SSH and GPG
- ✅ **Never Stored**: BAPAO never stores the actual passkey
- ✅ **Password Manager Integration**: Works with existing secure storage
- ✅ **Cross-Platform**: Same security model on all operating systems

## Platform Support

BAPAO works on **Linux**, **macOS**, and **Windows** with the following requirements:

### All Platforms
- Python 3.8+
- Git 2.13+ (for `includeIf` support)

### Platform-Specific Requirements

**Linux/macOS:**
- OpenSSH client (usually pre-installed)
- GPG/GnuPG (usually pre-installed or available via package manager)

**Windows:**
- Git for Windows (includes SSH client)
- GPG4Win or similar GPG implementation
- Windows Subsystem for Linux (WSL) recommended for best compatibility

### Key Features by Platform

| Feature | Linux | macOS | Windows | Notes |
|---------|-------|-------|---------|--------|
| SSH Key Generation | ✅ | ✅ | ✅ | Uses Python cryptography library |
| GPG Key Generation | ✅ | ✅ | ⚠️ | Requires GPG installation |
| Git Configuration | ✅ | ✅ | ✅ | Cross-platform paths handled |
| SSH Config | ✅ | ✅ | ✅ | Standard SSH config format |
| Directory Switching | ✅ | ✅ | ✅ | Git `includeIf` works everywhere |

**Windows Notes:**
- Use forward slashes (`/`) or double backslashes (`\\`) in paths
- WSL provides the most Unix-like experience
- PowerShell and Command Prompt are supported

## License

Proprietary software - All rights reserved.

## Support

For support, feature requests, or bug reports, please contact the development team directly through PyPI or the package maintainer.