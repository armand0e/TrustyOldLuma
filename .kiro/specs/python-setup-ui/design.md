# Design Document

## Overview

This design transforms the existing batch script setup into a sophisticated Python-based setup application using the Rich library for terminal UI enhancements. The new setup will provide a modern, colorful, and interactive experience while maintaining all existing functionality. The application will be packaged as a standalone executable using PyInstaller, ensuring easy distribution without requiring Python installation on target systems.

## Architecture

### Core Components

1. **Main Setup Controller** - Orchestrates the entire setup process
2. **UI Manager** - Handles all Rich-based terminal interface elements
3. **Admin Handler** - Manages privilege escalation and admin-only operations
4. **File Operations Manager** - Handles file extraction, copying, and configuration
5. **Download Manager** - Manages file downloads with progress tracking
6. **Configuration Manager** - Updates configuration files and creates shortcuts
7. **Error Handler** - Provides comprehensive error handling and user guidance

### Technology Stack

- **Rich Library** - For colorful terminal UI, progress bars, panels, and formatting
- **PyInstaller** - For creating standalone executable
- **Standard Library Modules**:
  - `subprocess` - For admin elevation and external process execution
  - `pathlib` - For modern path handling
  - `zipfile` - For archive extraction
  - `urllib.request` - For file downloads
  - `json` - For configuration file handling
  - `ctypes` - For Windows API calls

## Components and Interfaces

### 1. UI Manager (`ui_manager.py`)

```python
class UIManager:
    def __init__(self):
        self.console = Console()
        
    def show_welcome_screen(self) -> None
    def create_panel(self, content: str, title: str, style: str) -> Panel
    def show_progress_bar(self, description: str, total: int) -> Progress
    def show_status_spinner(self, message: str) -> Status
    def display_error(self, error: str, suggestions: List[str]) -> None
    def display_success(self, message: str) -> None
    def display_warning(self, message: str) -> None
    def show_completion_summary(self, operations: List[str]) -> None
```

**Key Features:**
- Rich console with color support auto-detection
- Styled panels for different phases (admin, extraction, configuration)
- Animated progress bars for file operations
- Status spinners for indeterminate operations
- Color-coded messages (green=success, red=error, yellow=warning, blue=info)

### 2. Setup Controller (`setup_controller.py`)

```python
class SetupController:
    def __init__(self):
        self.ui = UIManager()
        self.admin_handler = AdminHandler()
        self.file_ops = FileOperationsManager()
        self.downloader = DownloadManager()
        self.config_manager = ConfigurationManager()
        
    def run_setup(self) -> int
    def check_prerequisites(self) -> bool
    def handle_admin_phase(self) -> bool
    def perform_file_operations(self) -> bool
    def configure_applications(self) -> bool
    def create_shortcuts(self) -> bool
    def cleanup_and_finalize(self) -> bool
```

### 3. Admin Handler (`admin_handler.py`)

```python
class AdminHandler:
    def is_admin(self) -> bool
    def request_elevation(self, script_path: str) -> int
    def add_security_exclusions(self, paths: List[str]) -> bool
    def create_directories_as_admin(self, paths: List[str]) -> bool
```

**Windows Integration:**
- Uses `ctypes` to check admin privileges via `shell32.IsUserAnAdmin()`
- Launches elevated process using `subprocess` with PowerShell `Start-Process -Verb RunAs`
- Adds Windows Defender exclusions via PowerShell `Add-MpPreference`

### 4. File Operations Manager (`file_operations.py`)

```python
class FileOperationsManager:
    def __init__(self, ui_manager: UIManager):
        self.ui = ui_manager
        
    def extract_archive(self, archive_path: str, destination: str) -> bool
    def create_directory_structure(self, base_path: str) -> bool
    def copy_files(self, source: str, destination: str) -> bool
    def update_config_file(self, config_path: str, updates: Dict) -> bool
```

**Features:**
- Progress tracking for file extraction using Rich progress bars
- Atomic file operations with rollback capability
- Proper error handling with detailed user feedback

### 5. Download Manager (`download_manager.py`)

```python
class DownloadManager:
    def __init__(self, ui_manager: UIManager):
        self.ui = ui_manager
        
    def download_file(self, url: str, destination: str) -> bool
    def get_file_size(self, url: str) -> int
    def download_with_progress(self, url: str, destination: str) -> bool
```

**Features:**
- Rich progress bars showing download speed, ETA, and percentage
- Resume capability for interrupted downloads
- Automatic retry logic with exponential backoff

## Data Models

### Setup Configuration

```python
@dataclass
class SetupConfig:
    greenluma_path: Path
    koalageddon_url: str
    koalageddon_config_path: Path
    desktop_path: Path
    required_exclusions: List[str]
    app_id: str = "252950"
```

### Operation Result

```python
@dataclass
class OperationResult:
    success: bool
    message: str
    details: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)
```

## Error Handling

### Error Categories

1. **Permission Errors** - Admin rights, file access, security software interference
2. **Network Errors** - Download failures, connectivity issues
3. **File System Errors** - Disk space, corrupted archives, path issues
4. **Configuration Errors** - Invalid config files, missing dependencies

### Error Display Strategy

```python
def display_error(self, error_type: str, error_msg: str, suggestions: List[str]):
    error_panel = Panel(
        f"[red]Error:[/red] {error_msg}\n\n"
        f"[yellow]Suggestions:[/yellow]\n" + 
        "\n".join(f"• {suggestion}" for suggestion in suggestions),
        title=f"[red]{error_type}[/red]",
        border_style="red"
    )
    self.console.print(error_panel)
```

### Recovery Mechanisms

- Automatic retry for transient failures
- Graceful degradation for non-critical operations
- Clear rollback procedures for failed installations
- Detailed logging for troubleshooting

## Testing Strategy

### Unit Tests

- **UI Components** - Mock Rich console, test panel creation and formatting
- **File Operations** - Test with temporary directories and mock files
- **Admin Handler** - Mock Windows API calls, test privilege detection
- **Download Manager** - Mock HTTP requests, test progress tracking
- **Configuration Manager** - Test JSON/INI file parsing and updates

### Integration Tests

- **End-to-End Setup** - Full setup process in isolated environment
- **Admin Elevation** - Test privilege escalation flow
- **Error Scenarios** - Simulate various failure conditions
- **Cross-Platform** - Test on different Windows versions

### Test Framework

```python
# Using pytest with Rich testing utilities
def test_progress_bar_display():
    console = Console(file=StringIO(), width=80)
    ui = UIManager(console=console)
    
    with ui.show_progress_bar("Testing", 100) as progress:
        task = progress.add_task("Test task", total=100)
        progress.update(task, advance=50)
    
    output = console.file.getvalue()
    assert "Testing" in output
    assert "50%" in output
```

## Packaging and Distribution

### PyInstaller Configuration

```python
# setup.spec
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets/icon.ico', 'assets'),
        ('Config.jsonc', '.'),
    ],
    hiddenimports=['rich', 'rich.console', 'rich.progress', 'rich.panel'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='setup',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico'
)
```

### Build Process

1. **Development Build**: `pyinstaller setup.spec`
2. **Release Build**: `pyinstaller --onefile --windowed setup.spec`
3. **Testing**: Automated tests on clean Windows VMs
4. **Distribution**: Single executable file with embedded assets

## User Experience Flow

### 1. Welcome Screen

```
╭─────────────────────────────────────────────────────────────╮
│                    🎮 TrustyOldLuma Setup                    │
│                                                             │
│  Transforming your Steam game sharing experience with      │
│  modern setup tools and rich visual feedback.              │
│                                                             │
│  This setup will:                                          │
│  • Configure Windows Security exclusions                   │
│  • Extract and setup GreenLuma files                       │
│  • Download and install Koalageddon                        │
│  • Create desktop shortcuts                                │
│  • Configure application settings                          │
╰─────────────────────────────────────────────────────────────╯
```

### 2. Admin Phase Panel

```
╭─────────────────────────────────────────────────────────────╮
│                   🔐 Administrator Setup                    │
│                                                             │
│  ✅ Checking administrator privileges                       │
│  ⏳ Adding Windows Security exclusions...                   │
│     • GreenLuma folder: Documents\GreenLuma                │
│     • Koalageddon folder: AppData\Local\Programs\...       │
│  ⏳ Creating required directories...                        │
╰─────────────────────────────────────────────────────────────╯
```

### 3. Progress Bars

```
Extracting GreenLuma files...
████████████████████████████████████████ 100% 0:00:00

Downloading Koalageddon...
████████████████████████████████████████  85% 0:00:12
📊 Speed: 2.3 MB/s | Downloaded: 8.5 MB / 10.0 MB
```

### 4. Completion Summary

```
╭─────────────────────────────────────────────────────────────╮
│                    ✅ Setup Complete!                       │
│                                                             │
│  Successfully completed:                                    │
│  ✅ Windows Security exclusions added                       │
│  ✅ GreenLuma files extracted and configured                │
│  ✅ Koalageddon downloaded and installed                    │
│  ✅ Desktop shortcuts created                               │
│  ✅ Configuration files updated                             │
│                                                             │
│  Next Steps:                                                │
│  1. Launch Koalageddon and install platform integrations   │
│  2. Double-click GreenLuma shortcut to start gaming!       │
│                                                             │
│  🌟 Don't forget to star us on GitHub!                     │
│     https://github.com/armand0e/TrustyOldLuma              │
╰─────────────────────────────────────────────────────────────╯
```

## Performance Considerations

### Startup Time
- Lazy loading of Rich components
- Minimal imports in main module
- Fast privilege detection

### Memory Usage
- Streaming file operations for large archives
- Progress bar updates in chunks
- Cleanup of temporary objects

### Responsiveness
- Non-blocking UI updates
- Threaded downloads with progress callbacks
- Keyboard interrupt handling (Ctrl+C)

## Security Considerations

### Privilege Escalation
- Clear user consent before elevation
- Minimal admin operations scope
- Secure temporary file handling

### File Operations
- Path traversal protection
- Atomic file operations
- Proper cleanup of temporary files

### Network Operations
- HTTPS-only downloads
- Certificate validation
- Timeout and retry limits

## Backward Compatibility

The new Python setup maintains 100% functional compatibility with the existing batch script:

- Same directory structure creation
- Identical configuration file updates
- Same shortcut creation logic
- Equivalent error handling outcomes
- Preserved command-line behavior patterns