# Design Document

## Overview

The Gaming Setup Tool is a modern Python application that replaces a legacy batch script for setting up gaming tools (GreenLuma and Koalageddon). The application leverages the Rich library to provide an exceptional user experience with beautiful progress indicators, styled panels, and comprehensive error handling. The design emphasizes robustness, user feedback, and cross-platform compatibility while maintaining all functionality of the original script.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Gaming Setup Tool                        │
├─────────────────────────────────────────────────────────────┤
│  UI Layer (Rich Console Interface)                          │
│  ├── Progress Displays                                      │
│  ├── Status Indicators                                      │
│  ├── Error Panels                                          │
│  └── User Prompts                                          │
├─────────────────────────────────────────────────────────────┤
│  Business Logic Layer                                       │
│  ├── Setup Orchestrator                                     │
│  ├── Task Managers                                         │
│  └── Configuration Handlers                                │
├─────────────────────────────────────────────────────────────┤
│  Platform Services Layer                                    │
│  ├── Admin Privilege Manager                               │
│  ├── File Operations Manager                               │
│  ├── Security Configuration Manager                        │
│  └── Download Manager                                      │
├─────────────────────────────────────────────────────────────┤
│  System Interface Layer                                     │
│  ├── Windows API Wrappers                                  │
│  ├── PowerShell Execution                                  │
│  ├── Registry Operations                                    │
│  └── Process Management                                     │
└─────────────────────────────────────────────────────────────┘
```

### Core Design Principles

1. **Rich User Experience**: Every operation provides visual feedback through progress bars, spinners, and styled panels
2. **Robust Error Handling**: Comprehensive error catching with user-friendly messages and recovery suggestions
3. **Modular Design**: Each major functionality is encapsulated in dedicated managers/handlers
4. **Platform Awareness**: Windows-specific operations with graceful degradation on other platforms
5. **Logging and Debugging**: Comprehensive logging with optional verbose mode

## Components and Interfaces

### 1. Main Application Controller

```python
class GamingSetupTool:
    """Main application controller orchestrating the setup process."""
    
    def __init__(self):
        self.console: Console
        self.config: SetupConfig
        self.logger: Logger
        
    async def run(self) -> None:
        """Main entry point for the setup process."""
        
    def display_welcome(self) -> None:
        """Display welcome screen with Rich panels."""
        
    def display_completion(self, results: SetupResults) -> None:
        """Display completion summary and next steps."""
```

### 2. Admin Privilege Manager

```python
class AdminPrivilegeManager:
    """Handles administrator privilege detection and elevation."""
    
    @staticmethod
    def is_admin() -> bool:
        """Check if running with administrator privileges."""
        
    @staticmethod
    def elevate_privileges() -> bool:
        """Attempt to restart with elevated privileges."""
        
    def ensure_admin_privileges(self) -> None:
        """Ensure admin privileges or exit gracefully."""
```

### 3. File Operations Manager

```python
class FileOperationsManager:
    """Manages file and directory operations with progress tracking."""
    
    def __init__(self, console: Console):
        self.console = console
        
    async def create_directories(self, paths: List[Path]) -> None:
        """Create required directories with progress indication."""
        
    async def extract_archive(self, archive_path: Path, destination: Path) -> None:
        """Extract archive with progress bar and flattening."""
        
    async def download_file(self, url: str, destination: Path) -> None:
        """Download file with progress bar and retry logic."""
```

### 4. Security Configuration Manager

```python
class SecurityConfigManager:
    """Manages Windows Defender exclusions and security settings."""
    
    def __init__(self, console: Console):
        self.console = console
        
    async def add_defender_exclusions(self, paths: List[Path]) -> List[bool]:
        """Add Windows Defender exclusions for specified paths."""
        
    async def verify_antivirus_protection(self, greenluma_path: Path) -> bool:
        """Review GreenLuma folder contents to ensure antivirus didn't remove files."""
        
    def _execute_powershell_command(self, command: str) -> Tuple[bool, str]:
        """Execute PowerShell command and return result."""
        
    def _provide_manual_exclusion_instructions(self, paths: List[Path]) -> None:
        """Display manual instructions for adding security exclusions."""
```

### 5. Configuration Handler

```python
class ConfigurationHandler:
    """Handles configuration file updates and management."""
    
    def __init__(self, console: Console):
        self.console = console
        
    async def update_dll_injector_config(self, dll_path: Path, config_path: Path) -> bool:
        """Update DLLInjector.ini with correct DLL path."""
        
    async def replace_koalageddon_config(self, source: Path, destination: Path) -> bool:
        """Replace Koalageddon config with repository version."""
```

### 6. Shortcut Manager

```python
class ShortcutManager:
    """Manages desktop shortcut creation."""
    
    def __init__(self, console: Console):
        self.console = console
        
    async def create_shortcuts(self, shortcuts: List[ShortcutConfig]) -> List[bool]:
        """Create desktop shortcuts with custom icons."""
        
    def _create_windows_shortcut(self, config: ShortcutConfig) -> bool:
        """Create Windows .lnk shortcut file."""
```

### 7. Progress Display Manager

```python
class ProgressDisplayManager:
    """Manages Rich progress displays and status indicators."""
    
    def __init__(self, console: Console):
        self.console = console
        self.current_progress: Optional[Progress] = None
        
    def create_progress_bar(self, description: str, total: int) -> TaskID:
        """Create a new progress bar task."""
        
    def update_progress(self, task_id: TaskID, advance: int) -> None:
        """Update progress bar advancement."""
        
    def show_spinner(self, message: str) -> ContextManager:
        """Show spinner with status message."""
```

### 8. AppList Configuration Manager

```python
class AppListManager:
    """Manages AppList folder creation and initial configuration."""
    
    def __init__(self, console: Console):
        self.console = console
        
    async def setup_applist(self, greenluma_path: Path, app_id: str) -> bool:
        """Create AppList directory and initial configuration file."""
        
    def _create_initial_applist_file(self, applist_path: Path, app_id: str) -> bool:
        """Create initial AppList configuration file with default App ID."""
        
    def _validate_applist_format(self, applist_path: Path) -> bool:
        """Validate AppList file format and content."""
```

### 9. Cleanup Manager

```python
class CleanupManager:
    """Manages cleanup operations and temporary file removal."""
    
    def __init__(self, console: Console):
        self.console = console
        self.temp_files: List[Path] = []
        
    def register_temp_file(self, file_path: Path) -> None:
        """Register a temporary file for cleanup."""
        
    async def cleanup_temp_files(self) -> None:
        """Remove all registered temporary files."""
        
    async def cleanup_failed_installation(self, paths: List[Path]) -> None:
        """Clean up after failed installation attempts."""
```

## Data Models

### Setup Configuration

```python
@dataclass
class SetupConfig:
    """Configuration for the setup process."""
    greenluma_path: Path
    koalageddon_path: Path
    koalageddon_config_path: Path
    download_url: str
    app_id: str
    verbose_logging: bool = False
    
    @classmethod
    def from_environment(cls) -> 'SetupConfig':
        """Create configuration from environment and defaults."""
```

### Setup Results

```python
@dataclass
class SetupResults:
    """Results of the setup process."""
    directories_created: List[Path]
    exclusions_added: List[Tuple[Path, bool]]
    files_extracted: bool
    files_downloaded: List[Tuple[str, bool]]
    configs_updated: List[Tuple[str, bool]]
    shortcuts_created: List[Tuple[str, bool]]
    errors: List[str]
    warnings: List[str]
    
    @property
    def success_rate(self) -> float:
        """Calculate overall success rate."""
```

### Shortcut Configuration

```python
@dataclass
class ShortcutConfig:
    """Configuration for creating shortcuts."""
    name: str
    target_path: Path
    working_directory: Path
    icon_path: Optional[Path] = None
    description: Optional[str] = None
```

## Error Handling

### Error Categories

1. **Critical Errors**: Stop execution (missing files, permission failures)
2. **Recoverable Errors**: Continue with warnings (config update failures)
3. **Network Errors**: Retry with exponential backoff
4. **Platform Errors**: Graceful degradation for unsupported operations

### Error Display Strategy

```python
class ErrorDisplayManager:
    """Manages error display with Rich formatting."""
    
    def display_error(self, error: Exception, context: str) -> None:
        """Display error in styled panel with context."""
        
    def display_warning(self, message: str, suggestion: Optional[str] = None) -> None:
        """Display warning with optional suggestion."""
        
    def display_retry_prompt(self, operation: str, attempt: int, max_attempts: int) -> bool:
        """Display retry prompt and get user decision."""
```

### Retry Logic

- Network operations: 3 attempts with exponential backoff
- File operations: 2 attempts with 500ms delay
- PowerShell commands: 2 attempts with 1s delay

## Testing Strategy

### Unit Testing

1. **Mock External Dependencies**: Windows APIs, PowerShell, file system
2. **Test Error Scenarios**: Network failures, permission errors, missing files
3. **Validate Configuration Logic**: Path resolution, config file updates
4. **Progress Display Testing**: Mock console output verification

### Integration Testing

1. **End-to-End Scenarios**: Complete setup process simulation
2. **Platform-Specific Testing**: Windows admin privilege handling
3. **File System Operations**: Archive extraction, directory creation
4. **Network Operations**: Download with various network conditions

### Test Structure

```python
class TestGamingSetupTool:
    """Integration tests for the main setup tool."""
    
    @pytest.fixture
    def mock_console(self) -> Mock:
        """Mock Rich console for testing."""
        
    @pytest.fixture
    def temp_setup_environment(self) -> Path:
        """Create temporary setup environment."""
        
    async def test_complete_setup_success(self):
        """Test successful complete setup process."""
        
    async def test_setup_with_missing_admin_privileges(self):
        """Test setup behavior without admin privileges."""
```

### Visual Testing

- Rich output snapshots for regression testing
- Progress bar behavior verification
- Error panel formatting validation

## Rich UI Design Specifications

### Color Scheme

- **Primary**: Cyan for progress bars and highlights
- **Success**: Green for completed operations
- **Warning**: Yellow for non-critical issues
- **Error**: Red for failures and critical issues
- **Info**: Blue for informational messages

### Panel Styles

```python
PANEL_STYLES = {
    'welcome': Panel.fit(
        title="🎮 Gaming Setup Tool",
        border_style="cyan",
        padding=(1, 2)
    ),
    'error': Panel(
        border_style="red",
        title="❌ Error",
        title_align="left"
    ),
    'success': Panel(
        border_style="green",
        title="✅ Success",
        title_align="left"
    ),
    'completion': Panel(
        border_style="cyan",
        title="🎉 Setup Complete",
        subtitle="Next Steps"
    )
}
```

### Progress Bar Configuration

```python
PROGRESS_COLUMNS = [
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(bar_width=None),
    TaskProgressColumn(),
    TimeRemainingColumn(),
    TimeElapsedColumn(),
]
```

### Status Messages

- Use emojis for visual appeal (🔄 ⬇️ 📁 ⚙️ 🔗 ✅ ❌ ⚠️)
- Consistent message formatting with Rich markup
- Context-aware status updates

## Platform-Specific Considerations

### Windows Implementation

1. **Admin Privilege Detection**: Use `ctypes` to call Windows API
2. **PowerShell Integration**: Subprocess execution with proper encoding
3. **Shortcut Creation**: COM interface or VBScript generation
4. **Registry Operations**: For advanced configuration if needed

### Cross-Platform Graceful Degradation

1. **Admin Privileges**: Skip elevation on non-Windows platforms
2. **Security Exclusions**: Platform-specific antivirus handling
3. **Shortcut Creation**: Desktop entry files on Linux, aliases on macOS
4. **Path Handling**: Use `pathlib` for cross-platform compatibility

## Performance Considerations

### Asynchronous Operations

- File downloads with `aiohttp`
- Concurrent directory creation
- Parallel security exclusion setup
- Non-blocking progress updates

### Resource Management

- Context managers for file operations
- Proper cleanup of temporary files
- Memory-efficient archive extraction
- Connection pooling for downloads

### User Experience Optimizations

- Immediate visual feedback for all operations
- Estimated time remaining for long operations
- Ability to cancel long-running operations
- Responsive UI updates during processing