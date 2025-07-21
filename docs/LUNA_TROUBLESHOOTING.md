# 🔧 Luna Gaming Tool - Troubleshooting Guide

## Overview

This comprehensive troubleshooting guide helps resolve common issues with Luna Gaming Tool. Luna combines DLL injection and DLC unlocking capabilities, which can sometimes lead to complex interaction issues.

## Quick Diagnostic Commands

Before diving into specific issues, run these diagnostic commands:

```batch
# System compatibility check
python luna.py --check-system

# Component status check
python luna.py --check-components

# Configuration validation
python luna.py --validate-config

# Generate diagnostic report
python luna.py --diagnostic --output luna_diagnostic.txt
```

## Installation and Setup Issues

### Luna Setup Script Won't Run

**Symptoms:**
- Setup.bat fails to execute
- Permission denied errors
- Script terminates unexpectedly

**Solutions:**

1. **Administrator Privileges**
   ```batch
   # Right-click setup.bat and select "Run as administrator"
   # Or run from elevated command prompt:
   setup.bat
   ```

2. **Antivirus Interference**
   - Temporarily disable real-time protection
   - Add Luna directory to antivirus exclusions before setup
   - Use Windows Defender instead of third-party antivirus if possible

3. **Windows UAC Issues**
   - Lower UAC settings temporarily
   - Run setup from Administrator command prompt
   - Check Windows event logs for UAC-related errors

4. **Python/Dependency Issues**
   ```batch
   # Verify Python installation
   python --version
   
   # Update pip
   python -m pip install --upgrade pip
   
   # Install dependencies manually
   pip install -r requirements.txt
   ```

### Luna Components Not Installing

**Symptoms:**
- Missing Luna directories
- Incomplete file extraction
- Component initialization failures

**Solutions:**

1. **Manual Directory Creation**
   ```batch
   mkdir "%USERPROFILE%\Documents\Luna"
   mkdir "%USERPROFILE%\Documents\Luna\core"
   mkdir "%USERPROFILE%\Documents\Luna\config"
   mkdir "%USERPROFILE%\Documents\Luna\logs"
   ```

2. **File Permission Issues**
   ```batch
   # Fix permissions on Luna directory
   icacls "%USERPROFILE%\Documents\Luna" /grant %USERNAME%:F /T
   ```

3. **Disk Space Issues**
   - Verify at least 500 MB free space
   - Clean temporary files
   - Check disk health

### Windows Defender Exclusion Problems

**Symptoms:**
- Luna components being quarantined
- Injection failures due to antivirus blocking
- Performance issues from real-time scanning

**Solutions:**

1. **Manual Exclusion Setup**
   ```batch
   # Add exclusions via PowerShell (run as Administrator)
   Add-MpPreference -ExclusionPath "%USERPROFILE%\Documents\Luna"
   Add-MpPreference -ExclusionPath "%APPDATA%\Luna"
   Add-MpPreference -ExclusionPath "%TEMP%\Luna"
   ```

2. **Verify Exclusions**
   ```batch
   # Check current exclusions
   Get-MpPreference | Select-Object -ExpandProperty ExclusionPath
   ```

3. **Third-Party Antivirus**
   - Add Luna directory to exclusions
   - Whitelist Luna executables
   - Disable real-time scanning for Luna processes

## Runtime and Operation Issues

### Luna Won't Launch

**Symptoms:**
- Luna executable doesn't start
- Immediate crash on startup
- No response from Luna commands

**Solutions:**

1. **Check System Requirements**
   ```batch
   # Verify Python version
   python --version  # Should be 3.8+
   
   # Check system architecture
   wmic os get osarchitecture  # Should be 64-bit
   ```

2. **Dependency Issues**
   ```batch
   # Reinstall dependencies
   pip uninstall -r requirements.txt -y
   pip install -r requirements.txt
   ```

3. **Configuration Problems**
   ```batch
   # Reset Luna configuration
   python luna.py --reset-config
   
   # Validate configuration
   python luna.py --validate-config
   ```

4. **Log Analysis**
   ```batch
   # Check startup logs
   type "%USERPROFILE%\Documents\Luna\logs\startup.log"
   
   # Check error logs
   type "%USERPROFILE%\Documents\Luna\logs\error.log"
   ```

### Game Injection Failures

**Symptoms:**
- Games launch without Luna injection
- Steam games don't show shared library
- Injection process fails silently

**Solutions:**

1. **Process Timing Issues**
   ```json
   // Adjust injection timing in luna_config.jsonc
   {
     "luna": {
       "injection": {
         "delay_before_injection": 5000,
         "retry_attempts": 3,
         "retry_delay": 2000
       }
     }
   }
   ```

2. **Steam Process Detection**
   ```batch
   # Test Steam process detection
   python luna.py --detect-steam
   
   # Monitor Steam processes
   python luna.py --monitor-steam --verbose
   ```

3. **DLL Path Issues**
   ```batch
   # Verify DLL files exist
   dir "%USERPROFILE%\Documents\Luna\core\injector\*.dll"
   
   # Test DLL loading
   python luna.py --test-dll-loading
   ```

4. **Administrator Privileges**
   - Always run Luna as Administrator
   - Ensure Steam is not running as Administrator (or run Luna with higher privileges)

### DLC Unlocking Not Working

**Symptoms:**
- DLC remains locked in games
- Unlocker component not activating
- Platform-specific DLC issues

**Solutions:**

1. **Component Status Check**
   ```batch
   # Check unlocker component status
   python luna.py --check-unlocker
   
   # Test DLC unlocking capability
   python luna.py --test-dlc-unlock --game-id <APP_ID>
   ```

2. **Platform Configuration**
   ```json
   // Verify platform settings in luna_config.jsonc
   {
     "luna": {
       "platforms": {
         "steam": {
           "unlock_dlc": true,
           "unlock_shared_library": true,
           "dlc_detection_method": "automatic"
         }
       }
     }
   }
   ```

3. **Game-Specific Issues**
   - Some games have DLC protection that can't be bypassed
   - Verify the game supports DLC unlocking
   - Check Luna compatibility list

4. **Timing Issues**
   ```json
   // Adjust DLC unlock timing
   {
     "luna": {
       "dlc_unlocking": {
         "activation_delay": 10000,
         "scan_interval": 5000,
         "retry_failed_unlocks": true
       }
     }
   }
   ```

## Platform-Specific Issues

### Steam Integration Problems

**Symptoms:**
- Steam not detected by Luna
- Family sharing not working
- Steam games not launching with injection

**Solutions:**

1. **Steam Detection Issues**
   ```batch
   # Force Steam detection
   python luna.py --detect-steam --force
   
   # Check Steam installation path
   python luna.py --show-steam-path
   ```

2. **Steam Process Conflicts**
   ```batch
   # Kill all Steam processes
   taskkill /f /im steam.exe
   taskkill /f /im steamwebhelper.exe
   
   # Restart Steam with Luna
   python luna.py --launch-steam
   ```

3. **Family Sharing Issues**
   ```batch
   # Test family sharing configuration
   python luna.py --test-family-sharing
   
   # Repair family sharing settings
   python luna.py --repair-family-sharing
   ```

### Epic Games Store Issues

**Symptoms:**
- Epic Games not detected
- Epic launcher conflicts
- Game injection failures on Epic platform

**Solutions:**

1. **Epic Games Detection**
   ```batch
   # Force Epic Games detection
   python luna.py --detect-epic --force
   
   # Check Epic installation
   python luna.py --show-epic-path
   ```

2. **Launcher Configuration**
   ```json
   // Configure Epic Games in luna_config.jsonc
   {
     "luna": {
       "platforms": {
         "epic": {
           "enabled": true,
           "launcher_path": "auto-detect",
           "injection_method": "process_monitor",
           "unlock_dlc": true
         }
       }
     }
   }
   ```

## Migration Issues

### Automatic Migration Failures

**Symptoms:**
- Legacy installations not detected
- Configuration migration incomplete
- Shortcut migration failures

**Solutions:**

1. **Manual Migration**
   ```batch
   # Force migration with specific paths
   python luna.py --migrate --greenluma-path "C:\Custom\GreenLuma" --koalageddon-path "C:\Custom\Koalageddon"
   
   # Migrate only specific components
   python luna.py --migrate --components applist,shortcuts
   ```

2. **Permission Issues**
   ```batch
   # Fix permissions on legacy directories
   icacls "C:\GreenLuma" /grant %USERNAME%:F /T
   icacls "C:\Koalageddon" /grant %USERNAME%:F /T
   ```

3. **Validation After Migration**
   ```batch
   # Validate migrated configuration
   python luna.py --validate-migration
   
   # Compare before/after settings
   python luna.py --compare-migration
   ```

### Configuration Migration Problems

**Symptoms:**
- Settings not properly converted
- Game lists incomplete after migration
- Custom configurations lost

**Solutions:**

1. **Manual Configuration Transfer**
   ```batch
   # Export legacy configuration
   python luna.py --export-legacy-config --output legacy_config.json
   
   # Import to Luna format
   python luna.py --import-config --input legacy_config.json
   ```

2. **AppList Migration**
   ```batch
   # Manually copy AppList files
   xcopy "C:\GreenLuma\AppList\*" "%USERPROFILE%\Documents\Luna\AppList\" /Y
   
   # Validate AppList files
   python luna.py --validate-applist
   ```

## Performance Issues

### High CPU/Memory Usage

**Symptoms:**
- Luna consuming excessive resources
- System slowdown when Luna is running
- Games performing poorly with Luna

**Solutions:**

1. **Resource Monitoring**
   ```batch
   # Monitor Luna resource usage
   python luna.py --monitor-resources
   
   # Check for memory leaks
   python luna.py --memory-profile
   ```

2. **Configuration Optimization**
   ```json
   // Optimize performance settings
   {
     "luna": {
       "performance": {
         "monitoring_interval": 10000,
         "reduce_background_activity": true,
         "optimize_injection_timing": true,
         "limit_concurrent_operations": 2
       }
     }
   }
   ```

3. **Process Priority**
   ```batch
   # Set Luna to lower priority
   wmic process where name="luna.exe" CALL setpriority "below normal"
   ```

### Slow Injection/Unlocking

**Symptoms:**
- Long delays before injection occurs
- DLC unlocking takes too long
- Games timeout waiting for Luna

**Solutions:**

1. **Timing Optimization**
   ```json
   // Optimize timing settings
   {
     "luna": {
       "injection": {
         "fast_injection_mode": true,
         "preload_dlls": true,
         "parallel_processing": true
       }
     }
   }
   ```

2. **System Optimization**
   - Disable unnecessary startup programs
   - Increase system virtual memory
   - Defragment hard drive (if using HDD)

## Network and Connectivity Issues

### Luna API Communication Problems

**Symptoms:**
- GUI can't connect to CLI backend
- API timeouts or connection errors
- Real-time updates not working

**Solutions:**

1. **Port Configuration**
   ```json
   // Configure API port in luna_config.jsonc
   {
     "luna": {
       "api": {
         "port": 8080,
         "host": "localhost",
         "timeout": 30000
       }
     }
   }
   ```

2. **Firewall Issues**
   ```batch
   # Add firewall exception for Luna
   netsh advfirewall firewall add rule name="Luna API" dir=in action=allow protocol=TCP localport=8080
   ```

3. **Service Status**
   ```batch
   # Check if Luna API service is running
   python luna.py --check-api-service
   
   # Restart API service
   python luna.py --restart-api-service
   ```

## Advanced Troubleshooting

### Debug Mode and Logging

**Enable Comprehensive Logging:**
```batch
# Enable debug mode
set LUNA_DEBUG=1
set LUNA_LOG_LEVEL=DEBUG

# Run Luna with verbose output
python luna.py --verbose --log-level debug

# Enable component-specific logging
python luna.py --enable-logging injection,dlc,api
```

**Log File Locations:**
- Main Log: `%USERPROFILE%\Documents\Luna\logs\luna.log`
- Error Log: `%USERPROFILE%\Documents\Luna\logs\error.log`
- Injection Log: `%USERPROFILE%\Documents\Luna\logs\injection.log`
- DLC Log: `%USERPROFILE%\Documents\Luna\logs\dlc.log`
- API Log: `%USERPROFILE%\Documents\Luna\logs\api.log`

### System Information Collection

**Generate Diagnostic Report:**
```batch
# Comprehensive system diagnostic
python luna.py --diagnostic --include-system --include-logs --output luna_diagnostic.zip

# Quick diagnostic for specific issue
python luna.py --quick-diagnostic --issue injection_failure
```

**Manual Information Collection:**
```batch
# System information
systeminfo > luna_system_info.txt

# Process information
tasklist /svc > luna_processes.txt

# Network information
netstat -an > luna_network.txt

# Event logs
wevtutil qe Application /f:text > luna_app_events.txt
```

## Getting Help

### Before Requesting Support

1. **Run Diagnostics**
   ```batch
   python luna.py --diagnostic --comprehensive
   ```

2. **Check Logs**
   - Review error logs for specific error messages
   - Check timestamps to correlate issues with actions

3. **Try Safe Mode**
   ```batch
   python luna.py --safe-mode
   ```

4. **Test with Minimal Configuration**
   ```batch
   python luna.py --minimal-config --test
   ```

### Reporting Issues

When reporting issues, include:

1. **Luna Version**: `python luna.py --version`
2. **System Information**: Output from `--diagnostic`
3. **Error Logs**: Relevant log files
4. **Steps to Reproduce**: Detailed reproduction steps
5. **Expected vs Actual Behavior**: Clear description of the issue

### Community Resources

- **GitHub Issues**: Report bugs and feature requests
- **GitHub Discussions**: Community support and questions
- **Documentation**: Comprehensive guides and references
- **Wiki**: Community-maintained troubleshooting tips

## Emergency Recovery

### Complete Luna Reset

If Luna is completely broken:

```batch
# Stop all Luna processes
taskkill /f /im luna.exe
taskkill /f /im luna_gui.exe

# Backup current configuration
xcopy "%USERPROFILE%\Documents\Luna\config" "%USERPROFILE%\Documents\Luna_backup\config" /E /I

# Remove Luna directory
rmdir /s "%USERPROFILE%\Documents\Luna"

# Reinstall Luna
# Download fresh Luna installation and run setup.bat
```

### Restore from Backup

```batch
# Restore configuration from backup
xcopy "%USERPROFILE%\Documents\Luna_backup\config" "%USERPROFILE%\Documents\Luna\config" /E /I

# Restore AppList from backup
xcopy "%USERPROFILE%\Documents\Luna_backup\AppList" "%USERPROFILE%\Documents\Luna\AppList" /E /I

# Validate restored configuration
python luna.py --validate-config
```

This troubleshooting guide covers the most common issues with Luna Gaming Tool. For issues not covered here, please refer to the GitHub repository or create a detailed issue report.