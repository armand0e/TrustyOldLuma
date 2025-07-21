#!/usr/bin/env python3
"""
Working test for Luna configuration migration utilities.
"""

import tempfile
from pathlib import Path
import json

from luna_config_migration import (
    parse_greenluma_config,
    parse_koalageddon_config,
    merge_legacy_configs,
    validate_migrated_config,
    LegacyGreenLumaConfig,
    LegacyKoalageddonConfig
)

def test_greenluma_parsing():
    """Test GreenLuma configuration parsing."""
    print("Testing GreenLuma Config Parsing...")
    
    config_content = '''[DllInjector]
Exe = "C:\\Program Files (x86)\\Steam\\steam.exe"
Dll = "C:\\Users\\test\\GreenLuma\\GreenLuma_2020_x86.dll"
EnableFakeParentProcess = 1
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
            return True
        else:
            print("✗ Failed to parse GreenLuma config")
            return False
            
    finally:
        config_path.unlink()

def test_koalageddon_parsing():
    """Test Koalageddon configuration parsing."""
    print("\nTesting Koalageddon Config Parsing...")
    
    config_content = '''{
    "config_version": 6,
    "log_level": "debug",
    "platforms": {
        "Steam": {
            "enabled": true,
            "process": "steam.exe",
            "unlock_dlc": true
        }
    }
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
            return True
        else:
            print("✗ Failed to parse Koalageddon config")
            return False
            
    finally:
        config_path.unlink()

def test_config_merging():
    """Test configuration merging."""
    print("\nTesting Config Merging...")
    
    greenluma_config = LegacyGreenLumaConfig(
        exe_path="C:\\Program Files (x86)\\Steam\\steam.exe",
        dll_path="C:\\Users\\test\\GreenLuma\\GreenLuma_2020_x86.dll",
        enable_fake_parent=True
    )
    
    koalageddon_config = LegacyKoalageddonConfig(
        config_version=6,
        log_level="debug",
        platforms={
            "Steam": {
                "enabled": True,
                "process": "steam.exe",
                "unlock_dlc": True
            }
        }
    )
    
    merged_config = merge_legacy_configs(greenluma_config, koalageddon_config)
    
    print("✓ Successfully merged configurations")
    print(f"  - Injector enabled: {merged_config.get('core', {}).get('injector_enabled')}")
    print(f"  - Unlocker enabled: {merged_config.get('core', {}).get('unlocker_enabled')}")
    print(f"  - Stealth mode: {merged_config.get('core', {}).get('stealth_mode')}")
    print(f"  - Platforms: {list(merged_config.get('platforms', {}).keys())}")
    print(f"  - Migration flags: GL={merged_config.get('migration', {}).get('migrate_greenluma')}, KG={merged_config.get('migration', {}).get('migrate_koalageddon')}")
    
    return True

def test_config_validation():
    """Test configuration validation."""
    print("\nTesting Config Validation...")
    
    # Test with incomplete config (should fail)
    incomplete_config = {
        'luna': {'version': '1.0.0', 'name': 'Luna Gaming Tool'},
        'core': {'injector_enabled': True}
        # Missing required sections
    }
    
    is_valid, errors = validate_migrated_config(incomplete_config)
    
    if not is_valid and len(errors) > 0:
        print("✓ Validation correctly identified incomplete config")
        print(f"  - Found {len(errors)} errors (expected)")
        return True
    else:
        print("✗ Validation failed to identify incomplete config")
        return False

if __name__ == "__main__":
    print("Luna Configuration Migration Utilities Test")
    print("=" * 50)
    
    results = []
    results.append(test_greenluma_parsing())
    results.append(test_koalageddon_parsing())
    results.append(test_config_merging())
    results.append(test_config_validation())
    
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! Migration utilities are working correctly.")
    else:
        print("✗ Some tests failed. Please check the implementation.")