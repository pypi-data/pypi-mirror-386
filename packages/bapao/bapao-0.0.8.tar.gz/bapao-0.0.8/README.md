# BAPAO — Developer Environment Sync Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

> **"Everything you need, neatly wrapped."**

BAPAO is a CLI tool that makes your entire development environment portable. Create isolated 'profiles' containing your Git identity, SSH keys, GPG signing keys, and related configuration. Run one command on a new machine to restore everything needed to start working immediately with proper Git signing, SSH connectivity, and matching configuration.

## 🎯 What BAPAO Solves

**The Problem**: Developers juggle multiple Git identities (work, personal, clients) and struggle with:
- Manual SSH key management across different services
- Git config confusion and unsigned commits
- Complex setup on new machines
- Profile switching headaches
- Cleanup when leaving projects

**The Solution**: BAPAO automates the entire workflow:
- **One command setup** - `bapao init work` → `bapao forge work` → `bapao wire work`
- **Automatic profile switching** - Directory-based Git identity switching
- **Forensic cleanup** - `bapao cleanup work` removes all traces
- **Cross-machine portability** - Same commands work everywhere

## ✨ Current Capabilities

### ✅ **Implemented (MVP Complete)**
- [x] **Profile Management** - Store multiple development identities
- [x] **🔐 Passkey Protection** - 64-character secure passphrases for all keys
- [x] **SSH Key Generation** - Automatic Ed25519 keypair creation with encryption
- [x] **GPG Key Generation** - Commit signing keys with passphrase protection
- [x] **Git Configuration Wiring** - Directory-based automatic switching via `includeIf`
- [x] **SSH Host Aliases** - `github.com-work` vs `github.com-personal` isolation
- [x] **Verification System** - Health checks with beautiful UI tables
- [x] **Forensic Cleanup** - Complete profile removal ("like it never existed")
- [x] **Rich Terminal UI** - Progress bars, spinners, colored output
- [x] **Idempotent Operations** - Safe to run repeatedly
- [x] **Error Handling** - Graceful failures with helpful messages

### 🔧 **Development Tools** 
- [x] **Distribution Ready** - Wheel packages, PyPI compatible
- [x] **Development Workflow** - `./dev-reload.sh` with test integration
- [x] **Release Automation** - `./release.sh` with git tagging
- [x] **Integration Testing** - Full workflow validation
- [x] **Documentation** - Comprehensive user and developer guides

### 🔐 **Quantum-Safe Security** (NEW!)
- [x] **🛡️ Post-Quantum Cryptography** - Kyber-1024 key encapsulation + Dilithium-5 signatures
- [x] **🔒 Zero-Trust Vault** - AES-256-GCM + Argon2id password-based encryption  
- [x] **⚡ Secure Profile Storage** - Quantum-safe encrypted vault for sensitive data
- [x] **🔑 Master Password Protection** - Single password unlocks entire profile vault
- [x] **💾 Backup & Restore** - Encrypted vault backups with integrity verification
- [x] **🧠 Memory Security** - Automatic sensitive data clearing on vault lock
- [x] **✅ 100% Test Coverage** - 30 comprehensive tests validating all crypto operations

## 🏆 **What BAPAO Achieves**

**Before BAPAO:**
```bash
# Manual, error-prone setup
ssh-keygen -t ed25519 -f ~/.ssh/id_work
gpg --gen-key  # Interactive prompts...
# Edit ~/.ssh/config manually
# Edit ~/.gitconfig manually  
# Remember which key to use where
# Hope you don't mess up commits
```

**After BAPAO:**
```bash
bapao init work --name "Dev" --email "dev@company.com"
bapao forge work && bapao wire work
# Done! Everything works automatically
```

**Key Achievements:**
- ⚡ **10x Faster Setup** - Minutes instead of hours for new environments
- 🛡️ **Zero Config Errors** - Automated wiring eliminates human mistakes  
- 🎯 **Perfect Isolation** - No more cross-contamination between profiles
- 🧹 **Forensic Cleanup** - Complete removal when switching jobs/clients
- 🚀 **Developer Experience** - Beautiful UI that developers actually enjoy using

## 🚀 Quick Start

### Installation

#### Quick Install (Recommended)

```bash
curl -sSL https://gitlab.com/bapao/bapao-sync/-/raw/main/install.sh | bash
```

#### From PyPI (When Available)

```bash
pip install bapao
```

#### From Source

```bash
git clone https://gitlab.com/bapao/bapao-sync.git
cd bapao-sync
pip install -e .
```

#### Prerequisites

- Python 3.8+
- Git
- GPG (GnuPG)
  - macOS: `brew install gnupg`  
  - Ubuntu/Debian: `sudo apt install gnupg`
  - CentOS/RHEL: `sudo yum install gnupg2`

### Basic Usage

```bash
# 1. Create a new profile
bapao init work --name "Your Name" --email "you@company.com"

# 2. Generate SSH and GPG keys
bapao forge work

# 3. Configure Git and SSH
bapao wire work

# 4. Verify everything is working
bapao verify work

# 5. Start using your profile!
cd ~/code/work
git clone git@github.com-work:org/repo.git
```

## 📖 Commands

### `bapao init <profile>`
Create a new development profile with Git identity and base directory.

**Options:**
- `--name`: Git name for commits
- `--email`: Git email for commits  
- `--base-dir`: Base working directory for this profile
- `--host-alias`: Git host alias (e.g. github.com-work)

### `bapao forge <profile>`
Generate SSH (Ed25519) and GPG keys for the profile.

- Creates `~/.ssh/id_ed25519_<profile>` keypair
- Generates GPG key for commit signing
- Updates profile configuration

### `bapao wire <profile>`
Configure Git and SSH settings for automatic profile switching.

- Creates profile-specific `.gitconfig-<profile>`
- Adds `includeIf` directive to main `.gitconfig`
- Configures SSH host aliases

**Options:**
- `--force`: Overwrite existing configurations

### `bapao verify <profile>`
Verify that the profile is correctly set up.

- Checks SSH key existence and permissions
- Validates GPG key availability
- Verifies Git configuration
- Tests SSH host alias setup

**Options:**
- `--verbose`: Show detailed verification results

### 🔐 **Quantum-Safe Vault Commands** (NEW!)

#### `bapao init-vault`
Initialize a new quantum-safe vault for profile storage.

- Creates encrypted vault using post-quantum cryptography
- Requires master password for vault access
- Generates Kyber-1024 keys and Dilithium-5 signatures
- Sets up secure profile data storage

#### `bapao unlock`
Unlock the quantum vault for profile operations.

```bash
bapao unlock
# Prompts for master password
```

#### `bapao lock`
Lock the vault and clear sensitive data from memory.

```bash
bapao lock
```

#### `bapao vault-status`
Check current vault initialization and lock status.

```bash
bapao vault-status
```

#### `bapao backup-vault <backup-file>`
Create encrypted backup of the entire vault.

```bash
bapao backup-vault ~/backups/vault-backup.tar.gz
```

#### `bapao migrate-vault`
Upgrade vault to newer crypto algorithms (future-proofing).

## 📁 File Structure

BAPAO creates and manages these files:

```
~/.config/bapao/
├── profiles.yaml              # Profile metadata storage (legacy)
├── vault.kyb                  # 🔐 Quantum-encrypted vault data
├── vault.sig                  # 📝 Dilithium-5 digital signature
├── vault.meta                 # ⚙️ Vault metadata (public keys)
├── vault.salt                 # 🧂 Argon2id salt for key derivation
└── .locked                    # 🔒 Vault lock status file

~/.ssh/
├── config                     # SSH host configurations
├── id_ed25519_<profile>       # SSH private key
└── id_ed25519_<profile>.pub   # SSH public key

~/
├── .gitconfig                 # Main Git config with includeIf
└── .gitconfig-<profile>       # Profile-specific Git settings
```

## 🎯 How It Works

### Directory-Based Profile Switching

BAPAO uses Git's `includeIf` feature to automatically switch profiles based on your current directory:

```gitconfig
[includeIf "gitdir:~/code/work/"]
    path = ~/.gitconfig-work

[includeIf "gitdir:~/code/personal/"]
    path = ~/.gitconfig-personal
```

### SSH Host Aliases

Each profile gets its own SSH host alias to use the correct key:

```ssh-config
Host github.com-work
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_work
    IdentitiesOnly yes
```

Clone repositories using the alias:
```bash
git clone git@github.com-work:company/repo.git
```

## � Usage Examples

### Multiple Work Environments

```bash
# Work profile
bapao init work --name "John Doe" --email "john@company.com"
bapao forge work && bapao wire work

# Personal profile  
bapao init personal --name "John Doe" --email "john@personal.com"
bapao forge personal && bapao wire personal

# Client project
bapao init client-acme --name "John Doe" --email "contractor@acme.com"
bapao forge client-acme && bapao wire client-acme
```

### Using Profiles

```bash
# Work in company directory - automatically uses work profile
cd ~/code/work
git clone git@github.com-work:company/repo.git
git commit -m "Work commit"  # Signed with work GPG key

# Personal projects - automatically uses personal profile
cd ~/code/personal  
git clone git@github.com-personal:username/project.git
git commit -m "Personal commit"  # Signed with personal GPG key
```

### Profile Management

```bash
# Check profile status
bapao verify work

# Clean up when switching jobs
bapao cleanup old-company -f

# Quick setup on new machine
bapao init current-job --name "Your Name" --email "you@company.com"
bapao forge current-job && bapao wire current-job
```

## �🛠 Development & Contributing

### Quick Development Setup

```bash
# Clone and setup
git clone https://gitlab.com/bapao/bapao-sync.git
cd bapao-sync
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
```

### Development Workflow

```bash
# Daily development (fast, editable install)
./dev-reload.sh --quick

# Before commit (full test with integration tests)  
./dev-reload.sh --test

# Standard rebuild (wheel install like users get)
./dev-reload.sh

# Create release
./release.sh 0.2.0
```

### Development Scripts

- **`./dev-reload.sh --quick`** - Lightning fast editable install for active coding
- **`./dev-reload.sh --test`** - Full rebuild with unit tests + integration test  
- **`./dev-reload.sh`** - Standard wheel build and install
- **`./release.sh <version>`** - Automated release with git tagging
- **`./build.sh`** - Simple package build

### Manual Testing

```bash
# Test complete workflow
bapao init test --name "Test User" --email "test@example.com"
bapao forge test && bapao wire test && bapao verify test
bapao cleanup test -f
```



## � Future Development Roadmap

### 🎯 **High Priority (Next Release)**
- [ ] **Key Upload Integration** - Auto-upload SSH keys to GitHub/GitLab/Bitbucket
- [ ] **Profile Switching** - `bapao switch work` command for quick context changes
- [ ] **Shell Integration** - Show current profile in terminal prompt
- [ ] **Key Rotation** - `bapao rotate work` for security hygiene

### 🌟 **Medium Priority**  
- [ ] **Multi-Platform Git Hosting** - Support GitLab, Bitbucket, self-hosted Git
- [ ] **Encrypted Profile Export/Import** - Cross-machine synchronization
- [ ] **Team Templates** - Shared organizational profile templates
- [ ] **Auto-Detection** - Smart profile selection based on directory/remotes
- [ ] **Backup Management** - Encrypted key bundle backup/restore

### 🔮 **Future Vision**
- [ ] **Hardware Security Keys** - YubiKey integration for ultimate security  
- [ ] **Development Tool Integration** - IDE settings, environment variables per profile
- [ ] **Compliance & Auditing** - Track profile usage for corporate environments
- [ ] **Cloud Sync Service** - Optional encrypted cloud synchronization
- [ ] **Mobile Companion** - QR code setup for quick mobile configuration

### 🏗️ **Technical Improvements**
- [ ] **Shell Completion** - Bash/Zsh/Fish auto-completion
- [ ] **Configuration Validation** - Pre-flight checks and suggestions
- [ ] **Performance Optimization** - Faster key generation and switching
- [ ] **Plugin Architecture** - Extensible command system
- [ ] **Advanced Cleanup** - Selective cleanup options and dry-run mode

### 📊 **Metrics & Analytics** (Optional)
- [ ] **Usage Analytics** - Anonymous usage patterns (opt-in)
- [ ] **Health Monitoring** - Profile health checks and warnings
- [ ] **Migration Helpers** - Assist users migrating from other tools
- [ ] Package manager integration (npm, pip, brew)
- [ ] Encrypted profile export/import
- [ ] Cloud sync service

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ❤️ Support

- 🐛 [Report bugs](https://gitlab.com/bapao/bapao-sync/-/issues)
- 💡 [Request features](https://gitlab.com/bapao/bapao-sync/-/issues)
- 📖 [Read the docs](https://gitlab.com/bapao/bapao-sync/-/wikis/home)

---

**BAPAO** - *Everything you need, neatly wrapped.*

## Suggestions for a good README

Every project is different, so consider which of these sections apply to yours. The sections used in the template are suggestions for most open source projects. Also keep in mind that while a README can be too long and detailed, too long is better than too short. If you think your README is too long, consider utilizing another form of documentation rather than cutting out information.

## Name
Choose a self-explaining name for your project.

## Description
Let people know what your project can do specifically. Provide context and add a link to any reference visitors might be unfamiliar with. A list of Features or a Background subsection can also be added here. If there are alternatives to your project, this is a good place to list differentiating factors.

## Badges
On some READMEs, you may see small images that convey metadata, such as whether or not all the tests are passing for the project. You can use Shields to add some to your README. Many services also have instructions for adding a badge.

## Visuals
Depending on what you are making, it can be a good idea to include screenshots or even a video (you'll frequently see GIFs rather than actual videos). Tools like ttygif can help, but check out Asciinema for a more sophisticated method.

## Installation
Within a particular ecosystem, there may be a common way of installing things, such as using Yarn, NuGet, or Homebrew. However, consider the possibility that whoever is reading your README is a novice and would like more guidance. Listing specific steps helps remove ambiguity and gets people to using your project as quickly as possible. If it only runs in a specific context like a particular programming language version or operating system or has dependencies that have to be installed manually, also add a Requirements subsection.

## Usage
Use examples liberally, and show the expected output if you can. It's helpful to have inline the smallest example of usage that you can demonstrate, while providing links to more sophisticated examples if they are too long to reasonably include in the README.

## Support
Tell people where they can go to for help. It can be any combination of an issue tracker, a chat room, an email address, etc.

## Roadmap
If you have ideas for releases in the future, it is a good idea to list them in the README.

## Contributing
State if you are open to contributions and what your requirements are for accepting them.

For people who want to make changes to your project, it's helpful to have some documentation on how to get started. Perhaps there is a script that they should run or some environment variables that they need to set. Make these steps explicit. These instructions could also be useful to your future self.

You can also document commands to lint the code or run tests. These steps help to ensure high code quality and reduce the likelihood that the changes inadvertently break something. Having instructions for running tests is especially helpful if it requires external setup, such as starting a Selenium server for testing in a browser.

## Authors and acknowledgment
Show your appreciation to those who have contributed to the project.

## License
For open source projects, say how it is licensed.

## Project status
If you have run out of energy or time for your project, put a note at the top of the README saying that development has slowed down or stopped completely. Someone may choose to fork your project or volunteer to step in as a maintainer or owner, allowing your project to keep going. You can also make an explicit request for maintainers.
