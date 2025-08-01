# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TrustyOldLuma is a Python-based setup application that automates the installation and configuration of GreenLuma (Steam game sharing tool) and Koalageddon (DLC unlocker). The project transforms a legacy batch script into a sophisticated Python application with Rich terminal UI.

**Core Architecture:**
- **Controller Pattern**: `SetupController` orchestrates the entire setup process through discrete phases
- **Manager Classes**: Specialized managers handle specific concerns (UI, admin, files, downloads, config, errors)
- **Rich Terminal UI**: All user interaction through colorful terminal interface with progress bars and panels
- **Admin Privilege Handling**: Automatic elevation for Windows Security exclusions and protected operations

## Development Commands

### Installation and Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Verify all imports work correctly
python verify_imports.py

# Run the application
python main.py
```

### Testing
```bash
# Run all tests
pytest

# Run specific test files
pytest test_setup_controller.py
pytest test_ui_manager.py

# Run tests with verbose output
pytest -v

# Run integration tests only
pytest test_*_integration.py
```

### Building
```bash
# Development build (faster, directory-based)
build.bat dev

# Release build (optimized, single executable)
build.bat

# Clean build artifacts
build.bat clean

# Manual PyInstaller commands
pyinstaller setup-dev.spec  # Development build
pyinstaller setup.spec      # Release build
```

## Architecture Details

### Setup Flow
1. **Initialization**: SetupController validates environment and dependencies
2. **Admin Phase**: Separate elevated process handles Windows Security exclusions
3. **File Operations**: Extract GreenLuma files and create directory structure
4. **Downloads**: Fetch Koalageddon installer with progress tracking  
5. **Configuration**: Update DLLInjector.ini and Koalageddon config files
6. **Finalization**: Create shortcuts and AppList files

### Key Components
- **Rich UI System**: All terminal output routed through UIManager for consistent styling
- **Error Categorization**: ErrorHandler provides context-aware troubleshooting suggestions
- **Progress Tracking**: Download and file operations show real-time progress
- **Admin Handling**: Graceful privilege elevation with user feedback
- **Configuration Management**: JSON/INI file parsing and updates with error recovery

### Data Flow
```
main.py → SetupController → [AdminHandler, FileOperations, DownloadManager, ConfigurationManager]
                        ↓
                   UIManager (all output)
                        ↓  
                   ErrorHandler (error display)
```

### Testing Strategy
- **Unit Tests**: Individual manager classes with mocked dependencies
- **Integration Tests**: End-to-end scenarios with real file system operations
- **Demo Scripts**: Interactive testing of specific components (demo_*.py files)

## Important Notes

- **Windows-Specific**: Uses ctypes for Windows API calls and PowerShell for admin operations
- **Rich Dependency**: Heavy reliance on Rich library for all UI components
- **PyInstaller Build**: Two spec files for different build types (dev vs release)
- **Admin Requirements**: Setup requires elevation for Windows Defender exclusions
- **Config Files**: Handles both JSON (.jsonc) and INI file formats with comments