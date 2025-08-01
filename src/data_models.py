"""Data models and configuration structures for the setup application."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from enum import Enum


class ConfigurationError(Exception):
    """Exception raised for configuration-related errors."""
    pass


@dataclass
class OperationResult:
    """Result of an operation with success status, message, and optional details."""
    success: bool
    message: str
    details: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Ensure suggestions is always a list."""
        if self.suggestions is None:
            self.suggestions = []


@dataclass
class SetupConfig:
    """Configuration for the unified setup process with all necessary paths and settings."""
    
    # Core paths
    greenluma_path: Path
    koalageddon_config_path: Path
    koalageddon_install_path: Path  # New: Installation directory for embedded Koalageddon
    desktop_path: Path
    
    # Embedded binaries settings
    embedded_binaries_path: Path = Path("koalageddon_binaries")
    
    # URLs and downloads (kept for backward compatibility)
    koalageddon_url: str = ""  # Empty by default since we use embedded binaries
    
    # Security and admin settings
    required_exclusions: List[str]
    
    # Application settings
    app_id: str = "252950"
    
    # Platform integration settings
    enable_platform_integration: bool = True
    supported_platforms: List[str] = field(default_factory=lambda: ["Steam", "EpicGames", "Origin", "EADesktop", "UplayR1"])
    
    # Optional configuration file paths
    config_file_path: Optional[Path] = None
    koalageddon_config_file: Optional[Path] = None
    
    @classmethod
    def create_default(cls) -> 'SetupConfig':
        """
        Create default setup configuration based on standard Windows paths.
        
        Returns:
            SetupConfig: Default configuration with standard Windows paths.
        """
        user_profile = Path.home()
        documents = user_profile / "Documents"
        appdata_local = Path(os.environ.get('LOCALAPPDATA', user_profile / "AppData" / "Local"))
        programdata = Path(os.environ.get('PROGRAMDATA', 'C:\\ProgramData'))
        
        greenluma_path = documents / "GreenLuma"
        koalageddon_install_path = appdata_local / "Programs" / "Koalageddon"
        koalageddon_config_path = programdata / "acidicoala" / "Koalageddon"
        desktop_path = user_profile / "Desktop"
        
        return cls(
            greenluma_path=greenluma_path,
            koalageddon_config_path=koalageddon_config_path,
            koalageddon_install_path=koalageddon_install_path,
            desktop_path=desktop_path,
            embedded_binaries_path=Path("koalageddon_binaries"),
            koalageddon_url="",  # Empty since we use embedded binaries
            required_exclusions=[
                str(greenluma_path),
                str(koalageddon_install_path),
                str(koalageddon_config_path),
            ],
            app_id="252950",
            enable_platform_integration=True,
            supported_platforms=["Steam", "EpicGames", "Origin", "EADesktop", "UplayR1"],
            config_file_path=Path("Config.jsonc"),
            koalageddon_config_file=koalageddon_config_path / "Config.jsonc"
        )
    
    @classmethod
    def from_file(cls, config_path: Union[str, Path]) -> 'SetupConfig':
        """
        Load configuration from a JSON or JSONC file.
        
        Args:
            config_path: Path to the configuration file.
            
        Returns:
            SetupConfig: Configuration loaded from file.
            
        Raises:
            ConfigurationError: If file cannot be read or parsed.
        """
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Handle JSONC by removing comments (basic implementation)
            lines = content.split('\n')
            cleaned_lines = []
            for line in lines:
                # Remove single-line comments, but be careful about URLs
                comment_pos = -1
                in_string = False
                escape_next = False
                
                for i, char in enumerate(line):
                    if escape_next:
                        escape_next = False
                        continue
                    if char == '\\':
                        escape_next = True
                        continue
                    if char == '"' and not escape_next:
                        in_string = not in_string
                        continue
                    if not in_string and char == '/' and i + 1 < len(line) and line[i + 1] == '/':
                        comment_pos = i
                        break
                
                if comment_pos >= 0:
                    line = line[:comment_pos]
                cleaned_lines.append(line)
            
            cleaned_content = '\n'.join(cleaned_lines)
            config_data = json.loads(cleaned_content)
            
            # Extract setup-specific configuration
            setup_config = config_data.get('setup', {})
            
            # Create configuration with defaults and override with file values
            default_config = cls.create_default()
            
            # Override with file values if present
            if 'greenluma_path' in setup_config:
                default_config.greenluma_path = Path(setup_config['greenluma_path'])
            if 'koalageddon_config_path' in setup_config:
                default_config.koalageddon_config_path = Path(setup_config['koalageddon_config_path'])
            if 'desktop_path' in setup_config:
                default_config.desktop_path = Path(setup_config['desktop_path'])
            if 'koalageddon_url' in setup_config:
                default_config.koalageddon_url = setup_config['koalageddon_url']
            if 'required_exclusions' in setup_config:
                default_config.required_exclusions = setup_config['required_exclusions']
            if 'app_id' in setup_config:
                default_config.app_id = setup_config['app_id']
                
            default_config.config_file_path = config_path
            
            return default_config
            
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error reading configuration file: {e}")
    
    def validate(self) -> OperationResult:
        """
        Validate the configuration to ensure all required settings are present and valid.
        
        Returns:
            OperationResult: Result of validation with details about any issues.
        """
        errors = []
        warnings = []
        
        # Validate required paths
        if not self.greenluma_path:
            errors.append("GreenLuma path is required")
        
        if not self.koalageddon_config_path:
            errors.append("Koalageddon configuration path is required")
            
        if not self.desktop_path:
            errors.append("Desktop path is required")
        
        # Validate URL
        if not self.koalageddon_url:
            errors.append("Koalageddon URL is required")
        elif not self.koalageddon_url.startswith(('http://', 'https://')):
            errors.append("Koalageddon URL must be a valid HTTP/HTTPS URL")
        
        # Validate app_id
        if not self.app_id:
            errors.append("App ID is required")
        elif not self.app_id.isdigit():
            warnings.append("App ID should be numeric")
        
        # Validate exclusions
        if not self.required_exclusions:
            warnings.append("No security exclusions specified")
        
        # Check if paths are accessible (warnings only)
        try:
            if not self.desktop_path.exists():
                warnings.append(f"Desktop path does not exist: {self.desktop_path}")
        except Exception:
            warnings.append("Cannot access desktop path")
        
        # Prepare result
        if errors:
            return OperationResult(
                success=False,
                message=f"Configuration validation failed with {len(errors)} error(s)",
                details="; ".join(errors),
                suggestions=[
                    "Check the configuration file for missing or invalid values",
                    "Ensure all required paths are specified",
                    "Verify URL format is correct"
                ]
            )
        elif warnings:
            return OperationResult(
                success=True,
                message=f"Configuration valid with {len(warnings)} warning(s)",
                details="; ".join(warnings),
                suggestions=["Review warnings to ensure optimal configuration"]
            )
        else:
            return OperationResult(
                success=True,
                message="Configuration validation successful"
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary format.
        
        Returns:
            Dict[str, Any]: Configuration as dictionary.
        """
        return {
            'greenluma_path': str(self.greenluma_path),
            'koalageddon_config_path': str(self.koalageddon_config_path),
            'desktop_path': str(self.desktop_path),
            'koalageddon_url': self.koalageddon_url,
            'required_exclusions': self.required_exclusions,
            'app_id': self.app_id,
            'config_file_path': str(self.config_file_path) if self.config_file_path else None,
            'koalageddon_config_file': str(self.koalageddon_config_file) if self.koalageddon_config_file else None
        }


@dataclass
class FileOperationConfig:
    """Configuration for file operations."""
    source_path: Path
    destination_path: Path
    operation_type: str  # 'copy', 'extract', 'move'
    create_directories: bool = True
    overwrite_existing: bool = False
    
    def validate(self) -> OperationResult:
        """Validate file operation configuration."""
        if not self.source_path:
            return OperationResult(
                success=False,
                message="Source path is required",
                suggestions=["Specify a valid source path"]
            )
        
        if not self.destination_path:
            return OperationResult(
                success=False,
                message="Destination path is required",
                suggestions=["Specify a valid destination path"]
            )
        
        if self.operation_type not in ['copy', 'extract', 'move']:
            return OperationResult(
                success=False,
                message=f"Invalid operation type: {self.operation_type}",
                suggestions=["Use 'copy', 'extract', or 'move'"]
            )
        
        return OperationResult(success=True, message="File operation configuration valid")


@dataclass
class DownloadConfig:
    """Configuration for download operations."""
    url: str
    destination_path: Path
    filename: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    chunk_size: int = 8192
    
    def validate(self) -> OperationResult:
        """Validate download configuration."""
        if not self.url:
            return OperationResult(
                success=False,
                message="URL is required",
                suggestions=["Specify a valid download URL"]
            )
        
        if not self.url.startswith(('http://', 'https://')):
            return OperationResult(
                success=False,
                message="URL must be HTTP or HTTPS",
                suggestions=["Use a valid HTTP/HTTPS URL"]
            )
        
        if not self.destination_path:
            return OperationResult(
                success=False,
                message="Destination path is required",
                suggestions=["Specify a valid destination path"]
            )
        
        if self.timeout <= 0:
            return OperationResult(
                success=False,
                message="Timeout must be positive",
                suggestions=["Set timeout to a positive number of seconds"]
            )
        
        if self.max_retries < 0:
            return OperationResult(
                success=False,
                message="Max retries cannot be negative",
                suggestions=["Set max_retries to 0 or positive number"]
            )
        
        return OperationResult(success=True, message="Download configuration valid")


@dataclass
class PlatformInfo:
    """Information about a detected gaming platform."""
    name: str
    detected: bool
    executable_paths: List[Path] = field(default_factory=list)
    integration_available: bool = False
    integration_completed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'name': self.name,
            'detected': self.detected,
            'executable_paths': [str(p) for p in self.executable_paths],
            'integration_available': self.integration_available,
            'integration_completed': self.integration_completed
        }


@dataclass
class UnifiedSetupResult:
    """Result of the unified setup process with detailed component information."""
    overall_success: bool
    greenluma_installed: bool = False
    koalageddon_installed: bool = False
    platforms_detected: List[PlatformInfo] = field(default_factory=list)
    shortcuts_created: int = 0
    completed_operations: List[str] = field(default_factory=list)
    errors_encountered: List[str] = field(default_factory=list)
    warnings_encountered: List[str] = field(default_factory=list)
    installation_summary: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for export."""
        return {
            'overall_success': self.overall_success,
            'components': {
                'greenluma_installed': self.greenluma_installed,
                'koalageddon_installed': self.koalageddon_installed
            },
            'platforms_detected': [p.to_dict() for p in self.platforms_detected],
            'shortcuts_created': self.shortcuts_created,
            'completed_operations': self.completed_operations,
            'errors_encountered': self.errors_encountered,
            'warnings_encountered': self.warnings_encountered,
            'installation_summary': self.installation_summary
        }
    
    @property
    def platform_integration_count(self) -> int:
        """Get count of successfully integrated platforms."""
        return sum(1 for p in self.platforms_detected if p.integration_completed)
    
    @property
    def detected_platform_count(self) -> int:
        """Get count of detected platforms."""
        return sum(1 for p in self.platforms_detected if p.detected)


@dataclass
class UnifiedValidationResult:
    """Result of unified setup validation."""
    valid: bool
    greenluma_status: Dict[str, bool] = field(default_factory=dict)
    koalageddon_status: Dict[str, bool] = field(default_factory=dict)
    platform_status: List[PlatformInfo] = field(default_factory=list)
    validation_details: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'valid': self.valid,
            'greenluma_status': self.greenluma_status,
            'koalageddon_status': self.koalageddon_status,
            'platform_status': [p.to_dict() for p in self.platform_status],
            'validation_details': self.validation_details
        }


def load_default_configuration() -> SetupConfig:
    """
    Load default configuration, attempting to read from Config.jsonc if available.
    
    Returns:
        SetupConfig: Default or file-based configuration.
    """
    config_file = Path("Config.jsonc")
    
    if config_file.exists():
        try:
            return SetupConfig.from_file(config_file)
        except ConfigurationError:
            # Fall back to default if file cannot be read
            pass
    
    return SetupConfig.create_default()


def validate_configuration(config: SetupConfig) -> OperationResult:
    """
    Validate a setup configuration.
    
    Args:
        config: Configuration to validate.
        
    Returns:
        OperationResult: Validation result.
    """
    return config.validate()