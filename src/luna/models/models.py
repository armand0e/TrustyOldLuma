"""
Data models for the Gaming Setup Tool.

This module contains dataclasses and configuration models used throughout
the application for managing setup configuration, results, and shortcuts.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from urllib.parse import urlparse


@dataclass
class LunaConfig:
    """Configuration for the Luna setup process with path resolution and environment detection."""
    
    # Core paths
    luna_core_path: Path
    luna_config_path: Path
    
    # Download configuration
    download_url: str
    app_id: str
    
    # Legacy migration paths
    legacy_greenluma_path: Optional[Path] = None
    legacy_koalageddon_path: Optional[Path] = None
    
    # Application settings
    verbose_logging: bool = False
    timeout: int = 300
    
    # Additional configuration
    documents_path: Path = field(default_factory=lambda: Path.home() / "Documents")
    temp_dir: Path = field(default_factory=lambda: Path.cwd() / "temp")
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_paths()
        self._validate_url()
        self._validate_app_id()
    
    def _validate_paths(self) -> None:
        """Validate that all Luna paths are properly configured."""
        if not self.luna_core_path.is_absolute():
            raise ValueError("Luna core path must be absolute")
        if not self.luna_config_path.is_absolute():
            raise ValueError("Luna config path must be absolute")
        if self.legacy_greenluma_path is not None and not self.legacy_greenluma_path.is_absolute():
            raise ValueError("Legacy GreenLuma path must be absolute")
        if self.legacy_koalageddon_path is not None and not self.legacy_koalageddon_path.is_absolute():
            raise ValueError("Legacy Koalageddon path must be absolute")
    
    def _validate_url(self) -> None:
        """Validate the download URL format."""
        parsed = urlparse(self.download_url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid download URL format")
    
    def _validate_app_id(self) -> None:
        """Validate the app ID format."""
        if not self.app_id or not self.app_id.isdigit():
            raise ValueError("App ID must be a non-empty numeric string")
    
    @classmethod
    def from_environment(cls, verbose_logging: bool = False, luna_core_path: Optional[Path] = None,
                        app_id: str = "480", download_url: Optional[str] = None, 
                        timeout: int = 300, **overrides) -> 'LunaConfig':
        """Create Luna configuration from environment variables and defaults.
        
        Args:
            verbose_logging: Enable verbose logging mode
            luna_core_path: Custom path for Luna core installation
            app_id: Steam App ID for Luna AppList
            download_url: Custom download URL for Luna installer
            timeout: Network timeout in seconds
            **overrides: Additional parameter overrides
            
        Returns:
            LunaConfig instance with environment-based configuration
        """
        # Detect platform and set appropriate paths
        documents_path = Path.home() / "Documents"
        
        # Use custom paths if provided, otherwise use defaults
        if luna_core_path is None:
            luna_core_path = documents_path / "Luna"
        
        luna_config_path = luna_core_path / "config"
        
        # Environment variable overrides
        if env_luna := os.getenv('LUNA_PATH'):
            luna_core_path = Path(env_luna)
        if env_documents := os.getenv('DOCUMENTS_PATH'):
            documents_path = Path(env_documents)
        
        # Default configuration
        config_data = {
            'luna_core_path': luna_core_path,
            'luna_config_path': luna_config_path,
            'download_url': download_url or os.getenv('LUNA_DOWNLOAD_URL', 
                                    'https://github.com/acidicoala/Koalageddon/releases/latest/download/Koalageddon.exe'),
            'app_id': app_id or os.getenv('DEFAULT_APP_ID', '480'),
            'verbose_logging': verbose_logging or os.getenv('VERBOSE_LOGGING', '').lower() in ('true', '1', 'yes'),
            'documents_path': documents_path,
            'temp_dir': Path(os.getenv('TEMP_DIR', str(Path.cwd() / "temp"))),
            'timeout': timeout
        }
        
        # Apply any overrides
        config_data.update(overrides)
        
        return cls(**config_data)
    
    @classmethod
    def from_legacy_configs(cls, greenluma_path: Optional[Path] = None, 
                           koalageddon_path: Optional[Path] = None,
                           verbose_logging: bool = False, **overrides) -> 'LunaConfig':
        """Create Luna configuration from legacy GreenLuma and Koalageddon configurations.
        
        Args:
            greenluma_path: Path to existing GreenLuma installation
            koalageddon_path: Path to existing Koalageddon installation
            verbose_logging: Enable verbose logging mode
            **overrides: Additional parameter overrides
            
        Returns:
            LunaConfig instance with migrated configuration
        """
        documents_path = Path.home() / "Documents"
        luna_core_path = documents_path / "Luna"
        luna_config_path = luna_core_path / "config"
        
        # Default configuration for migration
        config_data = {
            'luna_core_path': luna_core_path,
            'luna_config_path': luna_config_path,
            'legacy_greenluma_path': greenluma_path,
            'legacy_koalageddon_path': koalageddon_path,
            'download_url': os.getenv('LUNA_DOWNLOAD_URL', 
                                    'https://github.com/acidicoala/Koalageddon/releases/latest/download/Koalageddon.exe'),
            'app_id': os.getenv('DEFAULT_APP_ID', '480'),
            'verbose_logging': verbose_logging or os.getenv('VERBOSE_LOGGING', '').lower() in ('true', '1', 'yes'),
            'documents_path': documents_path,
            'temp_dir': Path(os.getenv('TEMP_DIR', str(Path.cwd() / "temp"))),
            'timeout': 300
        }
        
        # Apply any overrides
        config_data.update(overrides)
        
        return cls(**config_data)
    
    def resolve_relative_paths(self, base_path: Optional[Path] = None) -> None:
        """Resolve any relative Luna paths to absolute paths.
        
        Args:
            base_path: Base path for resolving relative paths (defaults to cwd)
        """
        if base_path is None:
            base_path = Path.cwd()
        
        # Resolve Luna paths that might be relative
        if not self.luna_core_path.is_absolute():
            self.luna_core_path = (base_path / self.luna_core_path).resolve()
        if not self.luna_config_path.is_absolute():
            self.luna_config_path = (base_path / self.luna_config_path).resolve()
        if not self.temp_dir.is_absolute():
            self.temp_dir = (base_path / self.temp_dir).resolve()
        
        # Resolve legacy paths if they exist
        if self.legacy_greenluma_path is not None and not self.legacy_greenluma_path.is_absolute():
            self.legacy_greenluma_path = (base_path / self.legacy_greenluma_path).resolve()
        if self.legacy_koalageddon_path is not None and not self.legacy_koalageddon_path.is_absolute():
            self.legacy_koalageddon_path = (base_path / self.legacy_koalageddon_path).resolve()
    
    def get_luna_security_exclusion_paths(self) -> List[Path]:
        """Get list of Luna paths that should be added to security exclusions.
        
        Returns:
            List of Luna paths for security exclusions
        """
        paths = [
            self.luna_core_path,
            self.temp_dir
        ]
        
        # Include legacy paths if they exist for migration
        if self.legacy_greenluma_path:
            paths.append(self.legacy_greenluma_path)
        if self.legacy_koalageddon_path:
            paths.append(self.legacy_koalageddon_path)
            
        return paths


@dataclass
class LunaResults:
    """Results of the Luna setup process with enhanced tracking and success rate calculation."""
    
    # Migration-specific results
    legacy_installations_found: List[str] = field(default_factory=list)
    configurations_migrated: List[Tuple[str, bool]] = field(default_factory=list)
    luna_shortcuts_updated: List[Tuple[str, bool]] = field(default_factory=list)
    
    # Luna component installation tracking
    luna_components_installed: List[Tuple[str, bool]] = field(default_factory=list)
    luna_injector_configured: bool = False
    luna_unlocker_configured: bool = False
    
    # Operation results
    directories_created: List[Path] = field(default_factory=list)
    exclusions_added: List[Tuple[Path, bool]] = field(default_factory=list)
    files_extracted: bool = False
    files_downloaded: List[Tuple[str, bool]] = field(default_factory=list)
    configs_updated: List[Tuple[str, bool]] = field(default_factory=list)
    shortcuts_created: List[Tuple[str, bool]] = field(default_factory=list)
    
    # Error tracking
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Metadata
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    @property
    def luna_success_rate(self) -> float:
        """Calculate overall Luna setup success rate as a percentage.
        
        Returns:
            Success rate as a float between 0.0 and 1.0
        """
        total_operations = 0
        successful_operations = 0
        
        # Count migration operations
        total_operations += len(self.configurations_migrated)
        successful_operations += sum(1 for _, success in self.configurations_migrated if success)
        
        # Count Luna component installation operations
        total_operations += len(self.luna_components_installed)
        successful_operations += sum(1 for _, success in self.luna_components_installed if success)
        
        # Count Luna configuration operations
        if hasattr(self, '_luna_injector_attempted'):
            total_operations += 1
            if self.luna_injector_configured:
                successful_operations += 1
        
        if hasattr(self, '_luna_unlocker_attempted'):
            total_operations += 1
            if self.luna_unlocker_configured:
                successful_operations += 1
        
        # Count directory creation operations
        total_operations += len(self.directories_created)
        successful_operations += len(self.directories_created)  # All listed directories were created
        
        # Count security exclusion operations
        total_operations += len(self.exclusions_added)
        successful_operations += sum(1 for _, success in self.exclusions_added if success)
        
        # Count file extraction (single operation)
        if hasattr(self, '_extraction_attempted'):
            total_operations += 1
            if self.files_extracted:
                successful_operations += 1
        
        # Count download operations
        total_operations += len(self.files_downloaded)
        successful_operations += sum(1 for _, success in self.files_downloaded if success)
        
        # Count configuration update operations
        total_operations += len(self.configs_updated)
        successful_operations += sum(1 for _, success in self.configs_updated if success)
        
        # Count Luna shortcut operations
        total_operations += len(self.shortcuts_created)
        successful_operations += sum(1 for _, success in self.shortcuts_created if success)
        
        total_operations += len(self.luna_shortcuts_updated)
        successful_operations += sum(1 for _, success in self.luna_shortcuts_updated if success)
        
        # Calculate Luna success rate
        if total_operations == 0:
            return 1.0  # No operations means 100% success
        
        return successful_operations / total_operations
    
    @property
    def luna_duration(self) -> Optional[float]:
        """Get the duration of the Luna setup process in seconds.
        
        Returns:
            Duration in seconds, or None if timing not recorded
        """
        if self.start_time is not None and self.end_time is not None:
            return self.end_time - self.start_time
        return None
    
    @property
    def has_luna_errors(self) -> bool:
        """Check if any errors occurred during Luna setup.
        
        Returns:
            True if errors occurred, False otherwise
        """
        return len(self.errors) > 0
    
    @property
    def has_luna_warnings(self) -> bool:
        """Check if any warnings occurred during Luna setup.
        
        Returns:
            True if warnings occurred, False otherwise
        """
        return len(self.warnings) > 0
    
    # Compatibility aliases for legacy code
    @property
    def has_errors(self) -> bool:
        """Check if any errors occurred (compatibility alias for has_luna_errors)."""
        return self.has_luna_errors
    
    @property
    def has_warnings(self) -> bool:
        """Check if any warnings occurred (compatibility alias for has_luna_warnings)."""
        return self.has_luna_warnings
    
    @property
    def success_rate(self) -> float:
        """Get success rate (compatibility alias for luna_success_rate)."""
        return self.luna_success_rate
    
    @property
    def duration(self) -> Optional[float]:
        """Get duration (compatibility alias for luna_duration)."""
        return self.luna_duration
    
    def add_luna_error(self, error: str) -> None:
        """Add an error message to the Luna results.
        
        Args:
            error: Error message to add
        """
        self.errors.append(error)
    
    def add_luna_warning(self, warning: str) -> None:
        """Add a warning message to the Luna results.
        
        Args:
            warning: Warning message to add
        """
        self.warnings.append(warning)
    
    # Compatibility aliases for legacy code
    def add_error(self, error: str) -> None:
        """Add an error message (compatibility alias for add_luna_error)."""
        self.add_luna_error(error)
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message (compatibility alias for add_luna_warning)."""
        self.add_luna_warning(warning)
    
    def mark_luna_extraction_attempted(self) -> None:
        """Mark that Luna file extraction was attempted (for success rate calculation)."""
        self._extraction_attempted = True
    
    def mark_luna_injector_attempted(self) -> None:
        """Mark that Luna injector configuration was attempted."""
        self._luna_injector_attempted = True
    
    def mark_luna_unlocker_attempted(self) -> None:
        """Mark that Luna unlocker configuration was attempted."""
        self._luna_unlocker_attempted = True
    
    def get_luna_summary(self) -> Dict[str, Any]:
        """Get a summary of the Luna setup results.
        
        Returns:
            Dictionary containing Luna setup summary information
        """
        return {
            'luna_success_rate': self.luna_success_rate,
            'luna_duration': self.luna_duration,
            'legacy_installations_found': len(self.legacy_installations_found),
            'configurations_migrated_successful': sum(1 for _, success in self.configurations_migrated if success),
            'configurations_migrated_total': len(self.configurations_migrated),
            'luna_components_successful': sum(1 for _, success in self.luna_components_installed if success),
            'luna_components_total': len(self.luna_components_installed),
            'luna_injector_configured': self.luna_injector_configured,
            'luna_unlocker_configured': self.luna_unlocker_configured,
            'directories_created': len(self.directories_created),
            'exclusions_successful': sum(1 for _, success in self.exclusions_added if success),
            'exclusions_total': len(self.exclusions_added),
            'files_extracted': self.files_extracted,
            'downloads_successful': sum(1 for _, success in self.files_downloaded if success),
            'downloads_total': len(self.files_downloaded),
            'configs_successful': sum(1 for _, success in self.configs_updated if success),
            'configs_total': len(self.configs_updated),
            'shortcuts_successful': sum(1 for _, success in self.shortcuts_created if success),
            'shortcuts_total': len(self.shortcuts_created),
            'luna_shortcuts_successful': sum(1 for _, success in self.luna_shortcuts_updated if success),
            'luna_shortcuts_total': len(self.luna_shortcuts_updated),
            'error_count': len(self.errors),
            'warning_count': len(self.warnings)
        }


@dataclass
class LunaShortcutConfig:
    """Configuration for creating Luna-branded desktop shortcuts."""
    
    name: str
    component: str  # 'injector', 'unlocker', 'manager', 'settings'
    target_path: Path
    working_directory: Path
    icon_path: Optional[Path] = None
    description: Optional[str] = None
    arguments: Optional[str] = None
    luna_branding: bool = True
    
    def __post_init__(self):
        """Validate shortcut configuration after initialization."""
        self._validate_name()
        self._validate_paths()
    
    def _validate_name(self) -> None:
        """Validate the Luna shortcut name."""
        if not self.name or not self.name.strip():
            raise ValueError("Luna shortcut name cannot be empty")
        
        # Check for invalid characters in shortcut name
        invalid_chars = '<>:"/\\|?*'
        if any(char in self.name for char in invalid_chars):
            raise ValueError(f"Luna shortcut name contains invalid characters: {invalid_chars}")
    
    def _validate_paths(self) -> None:
        """Validate the Luna shortcut paths."""
        if not self.target_path.is_absolute():
            raise ValueError("Luna target path must be absolute")
        if not self.working_directory.is_absolute():
            raise ValueError("Luna working directory must be absolute")
        if self.icon_path is not None and not self.icon_path.is_absolute():
            raise ValueError("Luna icon path must be absolute")
    
    @property
    def display_name(self) -> str:
        """Get display name with Luna branding.
        
        Returns:
            Display name for the Luna shortcut
        """
        if self.luna_branding:
            return f"Luna {self.name}"
        return self.name
    
    @property
    def luna_description(self) -> str:
        """Get description with unified Luna branding.
        
        Returns:
            Luna-branded description for the shortcut
        """
        base_desc = self.description or f"Luna {self.component.title()}"
        return f"{base_desc} - Unified Gaming Tool"
    
    @property
    def desktop_path(self) -> Path:
        """Get the desktop path for this Luna-branded shortcut.
        
        Returns:
            Path where the Luna shortcut should be created on desktop
        """
        desktop = Path.home() / "Desktop"
        shortcut_name = self.display_name
        
        if os.name == 'nt':  # Windows
            return desktop / f"{shortcut_name}.lnk"
        else:  # Unix-like systems
            return desktop / f"{shortcut_name}.desktop"
    
    def resolve_relative_paths(self, base_path: Optional[Path] = None) -> None:
        """Resolve any relative Luna paths to absolute paths.
        
        Args:
            base_path: Base path for resolving relative paths (defaults to cwd)
        """
        if base_path is None:
            base_path = Path.cwd()
        
        if not self.target_path.is_absolute():
            self.target_path = (base_path / self.target_path).resolve()
        if not self.working_directory.is_absolute():
            self.working_directory = (base_path / self.working_directory).resolve()
        if self.icon_path is not None and not self.icon_path.is_absolute():
            self.icon_path = (base_path / self.icon_path).resolve()
    
    def to_luna_dict(self) -> Dict[str, Any]:
        """Convert Luna shortcut configuration to dictionary.
        
        Returns:
            Dictionary representation of the Luna shortcut configuration
        """
        return {
            'name': self.name,
            'component': self.component,
            'display_name': self.display_name,
            'target_path': str(self.target_path),
            'working_directory': str(self.working_directory),
            'icon_path': str(self.icon_path) if self.icon_path else None,
            'description': self.description,
            'luna_description': self.luna_description,
            'arguments': self.arguments,
            'luna_branding': self.luna_branding,
            'desktop_path': str(self.desktop_path)
        }
    
    @classmethod
    def from_luna_dict(cls, data: Dict[str, Any]) -> 'LunaShortcutConfig':
        """Create Luna shortcut configuration from dictionary.
        
        Args:
            data: Dictionary containing Luna shortcut configuration
            
        Returns:
            LunaShortcutConfig instance
        """
        return cls(
            name=data['name'],
            component=data.get('component', 'manager'),
            target_path=Path(data['target_path']),
            working_directory=Path(data['working_directory']),
            icon_path=Path(data['icon_path']) if data.get('icon_path') else None,
            description=data.get('description'),
            arguments=data.get('arguments'),
            luna_branding=data.get('luna_branding', True)
        )