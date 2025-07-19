# Project Structure & Organization

## Root Level Files
- `gaming_setup_tool.py` - Main application entry point and orchestrator
- `config.py` - Application-wide configuration constants
- `models.py` - Data models (SetupConfig, SetupResults, ShortcutConfig)
- `exceptions.py` - Custom exception hierarchy
- `conftest.py` - Pytest fixtures and test configuration

## Manager Modules
Each manager handles a specific domain with consistent patterns:
- `admin_manager.py` - Administrator privilege handling
- `applist_manager.py` - GreenLuma AppList configuration
- `cleanup_manager.py` - Temporary file and directory cleanup
- `configuration_handler.py` - Configuration file updates
- `display_managers.py` - Rich console UI components
- `error_manager.py` - Error categorization and handling
- `file_operations_manager.py` - File system operations
- `security_config_manager.py` - Windows Defender exclusions
- `shortcut_manager.py` - Desktop shortcut creation

## Testing Structure
- `test_*.py` - Unit tests for each module
- `test_*_integration.py` - Integration tests
- `test_complete_workflow_integration.py` - End-to-end workflow tests
- `test_edge_cases.py` - Edge case and error scenario tests
- `test_performance.py` - Performance benchmarks
- `run_tests.py` - Test runner script

## Assets & Configuration
- `assets/` - Binary assets and configuration files
  - `greenluma.zip` - GreenLuma installation archive
  - `Koalageddon-*.zip` - Koalageddon installer archive
  - `*.png` - Documentation images
- `Config.jsonc` - Koalageddon configuration template
- `requirements.txt` - Python dependencies
- `setup.py` - Package configuration
- `setup.bat` - Windows setup script

## Documentation
- `README.md` - User-facing documentation
- `STEAM_FAMILY_SETUP.md` - Steam Family Sharing guide
- `TEST_README.md` - Testing documentation

## Coding Conventions
- **Manager Pattern**: All managers accept `Console` instance as first parameter
- **Async Methods**: All I/O operations use async/await
- **Error Handling**: Use custom exceptions from `exceptions.py`
- **Path Handling**: Use `pathlib.Path` exclusively, not `os.path`
- **Type Hints**: All functions and methods should have type annotations
- **Dataclasses**: Use dataclasses for configuration and result objects
- **Rich Integration**: All output goes through Rich console for consistent styling

## File Naming
- Modules: `snake_case.py`
- Classes: `PascalCase`
- Functions/Methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Test files: `test_module_name.py`