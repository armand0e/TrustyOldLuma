#!/usr/bin/env python3
"""
Simple test for Luna configuration migration utilities.
"""

import tempfile
from pathlib import Path
import sys

# Add current directory to path
sys.path.insert(0, '.')

try:
    from luna_config_migration import (
        parse_greenluma_config,
        parse_koalageddon_config,
        merge_legacy_configs,
        validate_migrated_config,
        LegacyGreenLumaConfig,
        LegacyKoalageddonConfig
    )
    print("✓ Successfully imported migration functions")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

def test_greenluma_parsing():
    """Test GreenLuma configuration parsing."""
    print("\n--- Testing GreenLuma Config Parsing ---")
    
    # Create a test GreenLuma config
    config_content = '''[DllInjector]
AllowMultipleInstancesOfDLLInjector = 0
UseFullPathsFromIni = 1

Exe = "C:\\Program Files (x86)\\Steam\\steam.exe"
CommandLine = 

Dll = "C:\\Users\\test\\Documents\\GreenLuma\\GreenLuma_2020_x86.dll"

WaitForProcessTermination = 0
EnableFakeParentProcess = 1
FakeParentProcess = explorer.exe
EnableMitigationsOnChildProcess = 0

DEP = 1
SEHOP = 1
HeapTerminate = 1

CreateFiles = 2
FileToCreate_1 = NoQuestion.bin
FileToCreate_2 = StealthMode.bin

Use4GBPatch = 0
FileToPatch_1 =
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        f.write(config_content)
        config_path = Path(f.name)
    
    try:
        config = parse_greenluma_config(config_path)
        
        if config is not None:
            print("✓ Successfully parsed GreenLuma config")
            print(f"  - Exe path: {config.exe_path}")
            print(f"  - DLL path: {config.dll_path}")
            print(f"  - Stealth mode: {config.enable_fake_parent}")
            print(f"  - Files to create: {config.files_to_create}")
        else:
            print("✗ Failed to parse GreenLuma config")
            
    finally:
        config_path.unlink()

def test_koalageddon_parsing():
    """Test Koalageddon configuration parsing."""
    print("\n--- Testing Koalageddon Config Parsing ---")
    
    config_content = '''{
    "config_version": 6,
    "log_level": "debug",
    "platforms": {
        "Steam": {
            "enabled": true,
            "process": "steam.exe",
            "replicate": true,
            "unlock_dlc": true,
            "blacklist": [
                "22618"
            ],
            "ignore": [
                "steamwebhelper.exe"
            ]
        }
    },
    "ignore": [
        "UnrealCEFSubProcess.exe"
    ],
    "terminate": [
        "steamerrorreporter.exe"
    ]
}'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonc', delete=False) as f:
        f.write(config_content)
        config_path = Path(f.name)
    
    try:
        config = parse_koalageddon_config(config_path)
        
        if config is not None:
            print("✓ Successfully parsed Koalageddon config")
            print(f"  - Config version: {config.config_version}")
            print(f"  - Log level: {config.log_level}")
            print(f"  - Platforms: {list(config.platforms.keys())}")
            print(f"  - Global ignore: {config.ignore}")
        else:
            print("✗ Failed to parse Koalageddon config")
            
    finally:
        config_path.unlink()

def test_config_merging():
    """Test configuration merging."""
    print("\n--- Testing Config Merging ---")
    
    # Create sample configurations
    greenluma_config = LegacyGreenLumaConfig(
        exe_path="C:\\Program Files (x86)\\Steam\\steam.exe",
        dll_path="C:\\Users\\test\\GreenLuma\\GreenLuma_2020_x86.dll",
        enable_fake_parent=True,
        fake_parent_process="explorer.exe"
    )
    
    koalageddon_config = LegacyKoalageddonConfig(
        config_version=6,
        log_level="debug",
        platforms={
            "Steam": {
                "enabled": True,
                "process": "steam.exe",
                "replicate": True,
                "unlock_dlc": True,
                "blacklist": ["22618"]
            }
        },
        ignore=["UnrealCEFSubProcess.exe"],
        terminate=["steamerrorreporter.exe"]
    )
    
    merged_config = merge_legacy_configs(greenluma_config, koalageddon_config)
    
    print("✓ Successfully merged configurations")
    print(f"  - Injector enabled: {merged_config.get('core', {}).get('injector_enabled')}")
    print(f"  - Unlocker enabled: {merged_config.get('core', {}).get('unlocker_enabled')}")
    print(f"  - Stealth mode: {merged_config.get('core', {}).get('stealth_mode')}")
    print(f"  - Platforms: {list(merged_config.get('platforms', {}).keys())}")

def test_config_validation():
    """Test configuration validation."""
    print("\n--- Testing Config Validation ---")
    
    # Test with a minimal valid config
    config = {
        'luna': {
            'version': '1.0.0',
            'name': 'Luna Gaming Tool'
        },
        'core': {
            'injector_enabled': True,
            'unlocker_enabled': True
        },
        'paths': {
            'core_directory': '%DOCUMENTS%/Luna',
            'config_directory': '%DOCUMENTS%/Luna/config',
            'temp_directory': '%TEMP%/Luna'
        },
        'injector': {
            'enabled': True,
            'injection': {
                'delay_ms': 1000,
                'retry_attempts': 3
            }
        },
        'unlocker': {
            'enabled': True
        },
        'platforms': {
            'Steam': {
                'enabled': True,
                'process': 'steam.exe'
            }
        },
        'migration': {
            'auto_detect_legacy': True
        }
    }
    
    is_valid, errors = validate_migrated_config(config)
    
    if is_valid:
        print("✓ Configuration validation passed")
    else:
        print(f"✗ Configuration validation failed with {len(errors)} errors:")
        for error in errors:
            print(f"    - {error}")

if __name__ == "__main__":
    print("Luna Configuration Migration Utilities Test")
    print("=" * 50)
    
    test_greenluma_parsing()
    test_koalageddon_parsing()
    test_config_merging()
    test_config_validation()
    
    print("\n" + "=" * 50)
    print("All tests completed!")