"""
Test suite for Luna configuration migration utilities.
"""

import pytest
import json
import tempfile
from pathlib import Path
from luna_config_migration import (
    parse_greenluma_config,
    parse_koalageddon_config,
    merge_legacy_configs,
    validate_migrated_config,
    save_luna_config,
    detect_legacy_installations,
    LegacyGreenLumaConfig,
    LegacyKoalageddonConfig
)


class TestGreenLumaConfigParsing:
    """Test GreenLuma configuration parsing."""
    
    def test_parse_valid_greenluma_config(self):
        """Test parsing a valid GreenLuma configuration."""
        # Create a temporary GreenLuma config file
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
            
            assert config is not None
            assert config.exe_path == "C:\\Program Files (x86)\\Steam\\steam.exe"
            assert config.dll_path == "C:\\Users\\test\\Documents\\GreenLuma\\GreenLuma_2020_x86.dll"
            assert config.enable_fake_parent is True
            assert config.fake_parent_process == "explorer.exe"
            assert config.create_files == 2
            assert "NoQuestion.bin" in config.files_to_create
            assert "StealthMode.bin" in config.files_to_create
            assert config.dep is True
            assert config.sehop is True
            
        finally:
            config_path.unlink()
    
    def test_parse_nonexistent_greenluma_config(self):
        """Test parsing a non-existent GreenLuma configuration."""
        config = parse_greenluma_config(Path("nonexistent.ini"))
        assert config is None


class TestKoalageddonConfigParsing:
    """Test Koalageddon configuration parsing."""
    
    def test_parse_valid_koalageddon_config(self):
        """Test parsing a valid Koalageddon configuration."""
        config_content = '''{
    "config_version": 6, // DO NOT EDIT THIS VALUE
    "log_level": "debug",
    "platforms": {
        "Steam": {
            "enabled": true,
            "process": "steam.exe",
            "replicate": true,
            "unlock_dlc": true,
            "blacklist": [
                "22618" // Test blacklist entry
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
            
            assert config is not None
            assert config.config_version == 6
            assert config.log_level == "debug"
            assert "Steam" in config.platforms
            assert config.platforms["Steam"]["enabled"] is True
            assert config.platforms["Steam"]["process"] == "steam.exe"
            assert "22618" in config.platforms["Steam"]["blacklist"]
            assert "steamwebhelper.exe" in config.platforms["Steam"]["ignore"]
            assert "UnrealCEFSubProcess.exe" in config.ignore
            assert "steamerrorreporter.exe" in config.terminate
            
        finally:
            config_path.unlink()
    
    def test_parse_nonexistent_koalageddon_config(self):
        """Test parsing a non-existent Koalageddon configuration."""
        config = parse_koalageddon_config(Path("nonexistent.jsonc"))
        assert config is None


class TestConfigMerging:
    """Test configuration merging functionality."""
    
    def test_merge_both_configs(self):
        """Test merging both GreenLuma and Koalageddon configurations."""
        # Create sample configurations
        greenluma_config = LegacyGreenLumaConfig(
            exe_path="C:\\Program Files (x86)\\Steam\\steam.exe",
            dll_path="C:\\Users\\test\\GreenLuma\\GreenLuma_2020_x86.dll",
            enable_fake_parent=True,
            fake_parent_process="explorer.exe",
            dep=True,
            sehop=True
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
                    "blacklist": ["22618"],
                    "ignore": ["steamwebhelper.exe"]
                }
            },
            ignore=["UnrealCEFSubProcess.exe"],
            terminate=["steamerrorreporter.exe"]
        )
        
        merged_config = merge_legacy_configs(greenluma_config, koalageddon_config)
        
        # Verify merged configuration
        assert merged_config['core']['injector_enabled'] is True
        assert merged_config['core']['unlocker_enabled'] is True
        assert merged_config['core']['stealth_mode'] is True
        
        assert merged_config['injector']['enabled'] is True
        assert merged_config['injector']['injection']['stealth_injection'] is True
        
        assert merged_config['unlocker']['enabled'] is True
        
        assert merged_config['logging']['level'] == "debug"
        
        assert "Steam" in merged_config['platforms']
        assert merged_config['platforms']['Steam']['enabled'] is True
        assert merged_config['platforms']['Steam']['unlock_dlc'] is True
        assert "22618" in merged_config['platforms']['Steam']['blacklist']
        
        assert "UnrealCEFSubProcess.exe" in merged_config['process_management']['ignore']
        assert "steamerrorreporter.exe" in merged_config['process_management']['terminate']
        
        assert merged_config['migration']['migrate_greenluma'] is True
        assert merged_config['migration']['migrate_koalageddon'] is True
    
    def test_merge_greenluma_only(self):
        """Test merging only GreenLuma configuration."""
        greenluma_config = LegacyGreenLumaConfig(
            enable_fake_parent=True,
            dep=True
        )
        
        merged_config = merge_legacy_configs(greenluma_config, None)
        
        assert merged_config['core']['injector_enabled'] is True
        assert merged_config['core']['stealth_mode'] is True
        assert merged_config['migration']['migrate_greenluma'] is True
        assert merged_config['migration']['migrate_koalageddon'] is False
    
    def test_merge_koalageddon_only(self):
        """Test merging only Koalageddon configuration."""
        koalageddon_config = LegacyKoalageddonConfig(
            log_level="info",
            platforms={
                "Steam": {
                    "enabled": True,
                    "unlock_dlc": True
                }
            }
        )
        
        merged_config = merge_legacy_configs(None, koalageddon_config)
        
        assert merged_config['core']['unlocker_enabled'] is True
        assert merged_config['logging']['level'] == "info"
        assert merged_config['migration']['migrate_greenluma'] is False
        assert merged_config['migration']['migrate_koalageddon'] is True


class TestConfigValidation:
    """Test configuration validation functionality."""
    
    def test_validate_complete_config(self):
        """Test validation of a complete Luna configuration."""
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
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_incomplete_config(self):
        """Test validation of an incomplete Luna configuration."""
        config = {
            'luna': {
                'version': '1.0.0'
                # Missing 'name'
            },
            'core': {
                'injector_enabled': True
                # Missing 'unlocker_enabled'
            }
            # Missing other required sections
        }
        
        is_valid, errors = validate_migrated_config(config)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("Missing Luna name information" in error for error in errors)
        assert any("Missing core setting: unlocker_enabled" in error for error in errors)


class TestConfigSaving:
    """Test configuration saving functionality."""
    
    def test_save_luna_config(self):
        """Test saving a Luna configuration to file."""
        config = {
            'luna': {
                'version': '1.0.0',
                'name': 'Luna Gaming Tool'
            },
            'core': {
                'injector_enabled': True,
                'unlocker_enabled': True
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonc', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            success = save_luna_config(config, output_path)
            
            assert success is True
            assert output_path.exists()
            
            # Verify the saved content
            content = output_path.read_text(encoding='utf-8')
            assert 'Luna Gaming Tool - Unified Configuration Schema' in content
            assert 'Generated by Luna Configuration Migration Utilities' in content
            assert '"version": "1.0.0"' in content
            
        finally:
            if output_path.exists():
                output_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])