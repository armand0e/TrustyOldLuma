# 🌙 Luna Gaming Tool - Complete Setup Guide

## Overview

Luna is a unified gaming tool that combines DLL injection and DLC unlocking capabilities into a single, comprehensive platform. This guide provides detailed installation and configuration instructions for Luna.

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10 (64-bit) or later
- **Python**: 3.8 or higher (for CLI operations)
- **RAM**: 4 GB minimum, 8 GB recommended
- **Storage**: 500 MB free space for Luna installation
- **Administrator Access**: Required for initial setup and security exclusions

### Supported Platforms
- Steam (Primary support)
- Epic Games Store
- Origin/EA Desktop
- Ubisoft Connect

## Installation Methods

### Method 1: Automated Setup (Recommended)

1. **Download Luna**
   - Download the latest Luna release from the official repository
   - Extract the zip file to a temporary location

2. **Run Setup Script**
   ```batch
   # Right-click setup.bat and select "Run as administrator"
   setup.bat
   ```

3. **Follow Setup Wizard**
   - The setup wizard will guide you through the installation process
   - Luna will automatically detect and migrate existing GreenLuma/Koalageddon installations
   - Choose installation directory (default: `%USERPROFILE%\Documents\Luna`)
   - Configure Windows Defender exclusions
   - Set up desktop shortcuts

4. **Verify Installation**
   - Launch Luna from the desktop shortcut
   - Check that all components are properly initialized
   - Verify platform detection and configuration

### Method 2: Manual Installation

1. **Create Luna Directory**
   ```batch
   mkdir "%USERPROFILE%\Documents\Luna"
   cd "%USERPROFILE%\Documents\Luna"
   ```

2. **Extract Luna Files**
   - Copy all Luna files to the Luna directory
   - Ensure proper directory structure is maintained

3. **Configure Windows Defender**
   - Add Luna directory to Windows Defender exclusions
   - Include all subdirectories and executable files

4. **Install Python Dependencies**
   ```batch
   pip install -r requirements.txt
   ```

5. **Run Initial Configuration**
   ```batch
   python luna.py --setup --verbose
   ```

### Method 3: Development Installation

For developers or advanced users:

1. **Clone Repository**
   ```batch
   git clone https://github.com/armand0e/TrustyOldLuna.git
   cd TrustyOldLuna
   ```

2. **Install Development Dependencies**
   ```batch
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Run in Development Mode**
   ```batch
   python luna.py --dev --verbose
   ```

## Configuration

### Luna Configuration File

Luna uses a unified configuration file (`luna_config.jsonc`) that combines settings for all components:

```json
{
  "luna": {
    "version": "1.0.0",
    "core": {
      "injector_enabled": true,
      "unlocker_enabled": true,
      "auto_start": false,
      "stealth_mode": true,
      "monitoring_interval": 5000
    },
    "platforms": {
      "steam": {
        "enabled": true,
        "priority": 1,
        "process_name": "steam.exe",
        "unlock_dlc": true,
        "unlock_shared_library": true
      },
      "epic": {
        "enabled": true,
        "priority": 2,
        "process_name": "EpicGamesLauncher.exe",
        "unlock_dlc": true
      }
    },
    "paths": {
      "core_directory": "%DOCUMENTS%/Luna",
      "config_directory": "%APPDATA%/Luna",
      "temp_directory": "%TEMP%/Luna",
      "logs_directory": "%DOCUMENTS%/Luna/logs"
    },
    "security": {
      "auto_exclusions": true,
      "stealth_injection": true,
      "process_protection": true
    }
  }
}
```

### Platform-Specific Configuration

Each gaming platform can be configured individually:

#### Steam Configuration
```json
{
  "steam": {
    "enabled": true,
    "priority": 1,
    "injection_method": "dll",
    "dll_path": "core/injector/luna_core_x64.dll",
    "process_monitoring": true,
    "family_sharing": true,
    "unlock_dlc": true,
    "unlock_shared_library": true,
    "app_blacklist": [],
    "process_blacklist": ["steamwebhelper.exe"]
  }
}
```

#### Epic Games Configuration
```json
{
  "epic": {
    "enabled": true,
    "priority": 2,
    "injection_method": "process",
    "target_processes": ["EpicGamesLauncher.exe", "UnrealEngine.exe"],
    "unlock_dlc": true,
    "auto_detection": true
  }
}
```

## Advanced Setup Options

### Command Line Options

Luna provides extensive command-line options for advanced configuration:

```batch
# Basic setup
python luna.py --setup

# Setup with migration
python luna.py --setup --migrate

# Verbose setup with logging
python luna.py --setup --verbose --log-level debug

# Dry run (test without making changes)
python luna.py --setup --dry-run

# Reset configuration
python luna.py --reset-config

# Validate configuration
python luna.py --validate-config

# System compatibility check
python luna.py --check-system

# Generate diagnostic report
python luna.py --diagnostic
```

### Environment Variables

Configure Luna behavior using environment variables:

```batch
# Set Luna home directory
set LUNA_HOME=C:\Games\Luna

# Enable debug mode
set LUNA_DEBUG=1

# Set log level
set LUNA_LOG_LEVEL=DEBUG

# Disable auto-migration
set LUNA_AUTO_MIGRATE=0
```

## Security Configuration

### Windows Defender Exclusions

Luna automatically configures Windows Defender exclusions for optimal performance:

**Automatic Exclusions** (configured by Luna):
- Luna installation directory
- Luna temporary directories
- Luna executable files
- Luna DLL files

**Manual Exclusions** (if automatic setup fails):
1. Open Windows Security
2. Go to "Virus & threat protection"
3. Click "Manage settings" under "Virus & threat protection settings"
4. Scroll to "Exclusions" and click "Add or remove exclusions"
5. Add the following paths:
   - `%USERPROFILE%\Documents\Luna`
   - `%APPDATA%\Luna`
   - `%TEMP%\Luna`

### Firewall Configuration

If you experience connectivity issues:

1. **Windows Firewall**
   - Allow Luna through Windows Firewall
   - Add exceptions for Luna executables

2. **Third-party Antivirus**
   - Add Luna directory to antivirus exclusions
   - Whitelist Luna processes

## Verification and Testing

### Post-Installation Verification

1. **Component Check**
   ```batch
   python luna.py --check-components
   ```

2. **Configuration Validation**
   ```batch
   python luna.py --validate-config
   ```

3. **System Compatibility**
   ```batch
   python luna.py --check-system
   ```

4. **Platform Detection**
   ```batch
   python luna.py --detect-platforms
   ```

### Test Installation

1. **Launch Luna**
   - Use desktop shortcut or command line
   - Verify Luna starts without errors

2. **Test Platform Detection**
   - Launch Steam (or other supported platform)
   - Verify Luna detects the platform

3. **Test Game Injection**
   - Add a test game to Luna's AppList
   - Launch the game through the platform
   - Verify injection occurs successfully

## Troubleshooting Setup Issues

### Common Setup Problems

1. **Permission Denied Errors**
   - Ensure you're running setup as Administrator
   - Check file permissions on Luna directory
   - Verify Windows UAC settings

2. **Antivirus Interference**
   - Temporarily disable real-time protection during setup
   - Add Luna to antivirus exclusions before setup
   - Use Windows Defender instead of third-party antivirus if possible

3. **Python/Dependency Issues**
   - Verify Python 3.8+ is installed
   - Update pip: `python -m pip install --upgrade pip`
   - Install dependencies manually: `pip install -r requirements.txt`

4. **Migration Failures**
   - Check that legacy installations are accessible
   - Verify file permissions on legacy directories
   - Run migration manually: `python luna.py --migrate --verbose`

### Setup Logs

Luna generates detailed setup logs for troubleshooting:

- **Setup Log**: `%DOCUMENTS%\Luna\logs\setup.log`
- **Migration Log**: `%DOCUMENTS%\Luna\logs\migration.log`
- **Error Log**: `%DOCUMENTS%\Luna\logs\error.log`

### Getting Help

If you encounter issues during setup:

1. **Check Logs**: Review setup logs for specific error messages
2. **Run Diagnostics**: `python luna.py --diagnostic`
3. **Community Support**: Check GitHub issues and discussions
4. **Report Issues**: Create detailed issue reports with logs

## Next Steps

After successful installation:

1. **Read Migration Guide**: If upgrading from legacy tools
2. **Configure Platforms**: Set up your preferred gaming platforms
3. **Add Games**: Configure games for injection and DLC unlocking
4. **Explore Features**: Learn about Luna's advanced features

For detailed usage instructions, refer to the main README.md file.