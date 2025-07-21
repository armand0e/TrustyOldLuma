"""
Luna Configuration Migration Utilities.
"""

import json
import configparser
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class LegacyGreenLumaConfig:
    exe_path: str = ""
    dll_path: str = ""
    enable_fake_parent: bool = True

@dataclass  
class LegacyKoalageddonConfig:
    config_version: int = 6
    log_level: str = "debug"
    platforms: Dict[str, Any] = field(default_factory=dict)

def parse_greenluma_config(config_path: Path) -> Optional[LegacyGreenLumaConfig]:
    if not config_path.exists():
        return None
    try:
        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf-8')
        if 'DllInjector' not in config:
            return None
        section = config['DllInjector']
        return LegacyGreenLumaConfig(
            exe_path=section.get('Exe', '').strip('"'),
            dll_path=section.get('Dll', '').strip('"'),
            enable_fake_parent=section.getboolean('EnableFakeParentProcess', True)
        )
    except Exception:
        return None

def parse_koalageddon_config(config_path: Path) -> Optional[LegacyKoalageddonConfig]:
    if not config_path.exists():
        return None
    try:
        content = config_path.read_text(encoding='utf-8')
        lines = [line.split('//')[0] if '//' in line else line for line in content.split('\n')]
        cleaned_content = '\n'.join(lines)
        config_data = json.loads(cleaned_content)
        return LegacyKoalageddonConfig(
            config_version=config_data.get('config_version', 6),
            log_level=config_data.get('log_level', 'debug'),
            platforms=config_data.get('platforms', {})
        )
    except Exception:
        return None

def merge_legacy_configs(greenluma_config, koalageddon_config, luna_config_template=None):
    if luna_config_template is None:
        luna_config_template = {}
    merged_config = luna_config_template.copy()
    
    if greenluma_config:
        if 'core' not in merged_config:
            merged_config['core'] = {}
        merged_config['core']['injector_enabled'] = True
        merged_config['core']['stealth_mode'] = greenluma_config.enable_fake_parent
    
    if koalageddon_config:
        if 'core' not in merged_config:
            merged_config['core'] = {}
        merged_config['core']['unlocker_enabled'] = True
        if 'platforms' not in merged_config:
            merged_config['platforms'] = {}
        for name, config in koalageddon_config.platforms.items():
            merged_config['platforms'][name] = config
    
    if 'migration' not in merged_config:
        merged_config['migration'] = {}
    merged_config['migration']['migrate_greenluma'] = greenluma_config is not None
    merged_config['migration']['migrate_koalageddon'] = koalageddon_config is not None
    
    return merged_config

def validate_migrated_config(config):
    errors = []
    required_sections = ['luna', 'core', 'paths', 'injector', 'unlocker', 'platforms']
    for section in required_sections:
        if section not in config:
            errors.append(f"Missing required section: {section}")
    return len(errors) == 0, errors

print("Luna Configuration Migration Utilities loaded")
