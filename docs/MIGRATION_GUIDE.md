# 🔄 Luna Migration Guide - Upgrading from Legacy Tools

## Overview

This guide helps users migrate from existing GreenLuma and Koalageddon installations to the unified Luna gaming tool. Luna provides automatic migration capabilities while preserving all your existing configurations and functionality.

## Migration Benefits

### Why Migrate to Luna?

- **Unified Interface**: Single application for both injection and DLC unlocking
- **Enhanced Performance**: Optimized code with better resource management
- **Modern UI**: Rich console interface with progress indicators and status updates
- **Better Integration**: Seamless platform detection and management
- **Improved Security**: Enhanced Windows Defender integration and stealth features
- **Active Development**: Regular updates and new features
- **Comprehensive Logging**: Better troubleshooting and monitoring capabilities

## Pre-Migration Checklist

### Before You Begin

1. **Backup Current Setup**
   - Create a backup of your GreenLuma folder
   - Export Koalageddon settings if possible
   - Note down any custom configurations

2. **Close All Gaming Applications**
   - Exit Steam completely
   - Close Epic Games Launcher
   - Exit any other gaming platforms
   - End any running GreenLuma or Koalageddon processes

3. **Verify System Requirements**
   - Windows 10 (64-bit) or later
   - Administrator access
   - Python 3.8+ (for CLI operations)
   - At least 500 MB free disk space

4. **Document Current Configuration**
   - List of games in your AppList
   - Custom DLL injection settings
   - Koalageddon platform configurations
   - Any custom shortcuts or scripts

## Automatic Migration

### Luna's Auto-Migration Process

Luna automatically detects and migrates existing installations during setup:

1. **Detection Phase**
   - Scans common installation directories
   - Identifies GreenLuma installations
   - Locates Koalageddon configurations
   - Detects custom installation paths

2. **Analysis Phase**
   - Analyzes existing configurations
   - Identifies compatible settings
   - Plans migration strategy
   - Validates data integrity

3. **Migration Phase**
   - Creates Luna directory structure
   - Migrates AppList configurations
   - Converts injection settings
   - Transfers DLC unlock configurations
   - Updates desktop shortcuts
   - Preserves custom settings

### Running Automatic Migration

1. **Download Luna**
   ```batch
   # Download latest Luna release
   # Extract to temporary location
   ```

2. **Run Setup with Migration**
   ```batch
   # Right-click setup.bat and select "Run as administrator"
   setup.bat
   ```

3. **Follow Migration Wizard**
   - Luna will detect existing installations
   - Review detected configurations
   - Confirm migration settings
   - Monitor migration progress

4. **Verify Migration Results**
   - Check Luna configuration
   - Verify game lists
   - Test functionality

## Manual Migration

### When Manual Migration is Needed

- Automatic migration fails or is incomplete
- Custom installation paths not detected
- Complex configuration setups
- Partial migration requirements

### Step-by-Step Manual Migration

#### 1. Prepare Luna Installation

```batch
# Create Luna directory
mkdir "%USERPROFILE%\Documents\Luna"
cd "%USERPROFILE%\Documents\Luna"

# Extract Luna files
# Copy all Luna files to this directory
```

#### 2. Migrate GreenLuma Configuration

**Locate GreenLuma Installation**
```batch
# Common locations:
# %USERPROFILE%\Documents\GreenLuma
# %USERPROFILE%\Documents\GreenLuma_2020
# C:\GreenLuma
```

**Migrate AppList Files**
```batch
# Copy AppList directory
xcopy "%USERPROFILE%\Documents\GreenLuma\AppList" "%USERPROFILE%\Documents\Luna\AppList" /E /I

# Or manually copy individual files:
# 0.txt, 1.txt, etc. containing App IDs
```

**Convert DLL Injection Settings**
```batch
# Run Luna migration utility
python luna.py --migrate-greenluma --source "C:\path\to\GreenLuma"
```

#### 3. Migrate Koalageddon Configuration

**Locate Koalageddon Installation**
```batch
# Common locations:
# %PROGRAMFILES%\Koalageddon
# %LOCALAPPDATA%\Koalageddon
# Custom installation directory
```

**Export Koalageddon Settings**
1. Launch Koalageddon
2. Go to Settings
3. Export configuration (if available)
4. Note platform-specific settings

**Import to Luna**
```batch
# Run Luna Koalageddon migration
python luna.py --migrate-koalageddon --source "C:\path\to\Koalageddon"
```

#### 4. Update Configuration Files

**Edit luna_config.jsonc**
```json
{
  "luna": {
    "migration": {
      "greenluma_migrated": true,
      "koalageddon_migrated": true,
      "migration_date": "2024-01-01T00:00:00Z"
    },
    "platforms": {
      "steam": {
        "enabled": true,
        "app_list_path": "AppList",
        "unlock_dlc": true,
        "unlock_shared_library": true
      }
    }
  }
}
```

#### 5. Create Desktop Shortcuts

```batch
# Run Luna shortcut creation
python luna.py --create-shortcuts

# Or manually create shortcuts pointing to:
# Luna Injector: %DOCUMENTS%\Luna\luna.exe --inject
# Luna Manager: %DOCUMENTS%\Luna\luna.exe --gui
```

## Migration Scenarios

### Scenario 1: Standard GreenLuma + Koalageddon Setup

**Typical Configuration:**
- GreenLuma in Documents folder
- Koalageddon installed in Program Files
- Standard Steam Family Sharing setup

**Migration Steps:**
1. Run Luna setup with automatic migration
2. Verify AppList migration
3. Test Steam injection
4. Verify DLC unlocking

### Scenario 2: Custom Installation Paths

**Complex Configuration:**
- GreenLuma in custom directory
- Modified DLL injection settings
- Custom Koalageddon configuration

**Migration Steps:**
1. Use manual migration commands
2. Specify custom source paths
3. Manually verify configuration files
4. Test all functionality

### Scenario 3: Multiple Gaming Platforms

**Multi-Platform Setup:**
- Steam + Epic Games + Origin
- Platform-specific configurations
- Custom game lists per platform

**Migration Steps:**
1. Migrate each platform separately
2. Consolidate configurations in Luna
3. Test each platform individually
4. Verify cross-platform functionality

## Post-Migration Verification

### Verification Checklist

1. **Configuration Verification**
   ```batch
   # Validate Luna configuration
   python luna.py --validate-config
   
   # Check migrated settings
   python luna.py --show-config
   ```

2. **Game List Verification**
   ```batch
   # List migrated games
   python luna.py --list-games
   
   # Verify AppList files
   dir "%DOCUMENTS%\Luna\AppList"
   ```

3. **Platform Testing**
   ```batch
   # Test platform detection
   python luna.py --detect-platforms
   
   # Test injection capability
   python luna.py --test-injection
   ```

4. **Functionality Testing**
   - Launch Steam with Luna
   - Test game injection
   - Verify DLC unlocking
   - Check all platforms

### Common Post-Migration Issues

1. **Games Not Detected**
   - Verify AppList files are properly migrated
   - Check file permissions
   - Validate App IDs

2. **Injection Failures**
   - Verify DLL paths in configuration
   - Check Windows Defender exclusions
   - Test with administrator privileges

3. **DLC Not Unlocking**
   - Verify Koalageddon settings migration
   - Check platform-specific configurations
   - Test with supported games

## Rollback Procedures

### If Migration Fails

1. **Restore Original Setup**
   ```batch
   # Restore GreenLuma backup
   xcopy "C:\Backup\GreenLuma" "%USERPROFILE%\Documents\GreenLuma" /E /I
   
   # Reinstall Koalageddon from backup
   ```

2. **Clean Luna Installation**
   ```batch
   # Remove Luna directory
   rmdir /s "%USERPROFILE%\Documents\Luna"
   
   # Remove Luna shortcuts
   del "%USERPROFILE%\Desktop\Luna*.lnk"
   ```

3. **Restore Registry Settings**
   - Remove Luna registry entries
   - Restore original antivirus exclusions

## Advanced Migration Options

### Command Line Migration Tools

```batch
# Full migration with verbose output
python luna.py --migrate --verbose --log-level debug

# Migrate only GreenLuma
python luna.py --migrate-greenluma --source "C:\GreenLuma"

# Migrate only Koalageddon
python luna.py --migrate-koalageddon --source "C:\Koalageddon"

# Dry run migration (test without changes)
python luna.py --migrate --dry-run

# Force migration (overwrite existing)
python luna.py --migrate --force

# Selective migration
python luna.py --migrate --include applist,shortcuts --exclude registry
```

### Migration Configuration

Create a migration configuration file (`migration_config.json`):

```json
{
  "migration": {
    "greenluma": {
      "source_path": "C:\\Custom\\GreenLuma",
      "migrate_applist": true,
      "migrate_dll_settings": true,
      "migrate_shortcuts": true
    },
    "koalageddon": {
      "source_path": "C:\\Custom\\Koalageddon",
      "migrate_platform_settings": true,
      "migrate_dlc_settings": true,
      "preserve_original": true
    },
    "options": {
      "backup_original": true,
      "validate_migration": true,
      "create_shortcuts": true,
      "update_registry": true
    }
  }
}
```

## Troubleshooting Migration Issues

### Common Migration Problems

1. **Permission Errors**
   - Run migration as Administrator
   - Check source directory permissions
   - Verify destination directory access

2. **File Not Found Errors**
   - Verify source paths are correct
   - Check for moved or renamed directories
   - Use manual path specification

3. **Configuration Corruption**
   - Validate source configurations
   - Use backup configurations
   - Perform clean migration

4. **Incomplete Migration**
   - Check migration logs
   - Run migration again with --force
   - Perform manual migration steps

### Migration Logs

Luna creates detailed migration logs:

- **Migration Log**: `%DOCUMENTS%\Luna\logs\migration.log`
- **Error Log**: `%DOCUMENTS%\Luna\logs\migration_errors.log`
- **Validation Log**: `%DOCUMENTS%\Luna\logs\migration_validation.log`

### Getting Migration Help

1. **Check Documentation**: Review this guide and Luna documentation
2. **Review Logs**: Check migration logs for specific errors
3. **Community Support**: Ask questions in GitHub discussions
4. **Report Issues**: Create detailed issue reports with logs

## Best Practices

### Migration Best Practices

1. **Always Backup**: Create full backups before migration
2. **Test First**: Use dry-run mode to test migration
3. **Verify Results**: Thoroughly test after migration
4. **Keep Backups**: Maintain backups until Luna is fully validated
5. **Document Changes**: Note any custom configurations
6. **Update Gradually**: Migrate one platform at a time if needed

### Post-Migration Maintenance

1. **Regular Updates**: Keep Luna updated to latest version
2. **Monitor Performance**: Check Luna performance vs. legacy tools
3. **Backup Luna Config**: Regular backups of Luna configuration
4. **Review Logs**: Periodically check Luna logs for issues

## Conclusion

Migration to Luna provides significant benefits while preserving all existing functionality. The automatic migration process handles most scenarios, while manual migration options provide flexibility for complex setups.

For additional help with migration, refer to the main Luna documentation or create an issue on the GitHub repository with detailed information about your specific setup.