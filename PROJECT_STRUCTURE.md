# TrustyOldLuma Setup - Project Structure

This document outlines the Python project structure for the TrustyOldLuma setup application.

## Directory Structure

```
TrustyOldLuma/
├── main.py                     # Main entry point
├── requirements.txt            # Python dependencies
├── Config.jsonc               # Koalageddon configuration
├── PROJECT_STRUCTURE.md       # This file
├── verify_imports.py          # Import verification script
├── src/                       # Source code modules
│   ├── __init__.py           # Package initialization
│   ├── setup_controller.py   # Main setup orchestration
│   ├── ui_manager.py         # Rich-based UI components
│   ├── admin_handler.py      # Windows admin privilege management
│   ├── file_operations.py    # File extraction and operations
│   ├── download_manager.py   # HTTP download with progress
│   ├── configuration_manager.py # Config file updates
│   ├── error_handler.py      # Error handling and display
│   └── data_models.py        # Data structures and models
├── assets/                    # Application assets
│   ├── icon.ico              # Application icon
│   └── create_icon.py        # Icon generation script
├── build/                     # Build artifacts (generated)
├── dist/                      # Distribution files (generated)
├── test_*.py                  # Unit tests
└── .kiro/                     # Kiro IDE configuration
    └── specs/                 # Feature specifications
        └── python-setup-ui/   # This feature spec
```

## Core Dependencies

### Runtime Dependencies
- **Rich (>=13.0.0)**: Terminal UI library for colors, progress bars, and panels
- **PyInstaller (>=5.0.0)**: For creating standalone executables

### Standard Library Modules Used
- `pathlib`: Modern path handling
- `subprocess`: Admin elevation and external processes
- `zipfile`: Archive extraction
- `urllib.request`: HTTP downloads
- `json`: Configuration file parsing
- `ctypes`: Windows API calls
- `configparser`: INI file handling
- `tempfile`: Temporary file operations
- `shutil`: File operations
- `logging`: Error logging and debugging

### Development Dependencies
- **pytest (>=7.0.0)**: Testing framework
- **pytest-cov (>=4.0.0)**: Test coverage reporting

## Module Overview

### `main.py`
- Application entry point
- Handles command-line execution
- Provides graceful error handling and user feedback
- Sets up Python path for src imports

### `src/setup_controller.py`
- Orchestrates the entire setup process
- Coordinates all manager classes
- Implements phase-by-phase execution
- Handles setup flow and error recovery

### `src/ui_manager.py`
- Rich-based terminal interface
- Colorful panels and progress bars
- Status displays and user prompts
- Keyboard interaction handling

### `src/admin_handler.py`
- Windows privilege detection and elevation
- Security exclusion management
- Admin-only directory operations
- PowerShell integration

### `src/file_operations.py`
- File extraction with progress tracking
- Directory structure creation
- Configuration file updates
- Atomic file operations

### `src/download_manager.py`
- HTTP downloads with progress bars
- Resume capability and retry logic
- Speed and ETA calculations
- Network error handling

### `src/configuration_manager.py`
- Koalageddon configuration updates
- Desktop shortcut creation
- INI and JSON file management
- Application integration

### `src/error_handler.py`
- Comprehensive error categorization
- Rich-formatted error displays
- Troubleshooting suggestions
- Error logging for debugging

### `src/data_models.py`
- Configuration data structures
- Operation result models
- Default configuration loading
- Type definitions and validation

## Usage

### Running the Application
```bash
python main.py
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Verifying Installation
```bash
python verify_imports.py
```

### Building Executable
```bash
pyinstaller setup.spec
```

## Development Guidelines

1. **Import Structure**: All modules should import from the `src` package
2. **Error Handling**: Use the ErrorHandler class for consistent error display
3. **UI Components**: Use UIManager for all terminal output
4. **Type Hints**: Include type hints for all function parameters and returns
5. **Documentation**: Document all classes and methods with docstrings
6. **Testing**: Write unit tests for all new functionality

## Requirements Mapping

This project structure addresses the following requirements:
- **6.1**: Self-contained distribution with all dependencies
- **6.2**: Single executable creation capability
- **1.1-1.4**: Rich UI components and colorful interface
- **4.1-4.5**: Comprehensive functionality preservation
- **5.1-5.4**: Enhanced error handling and user guidance