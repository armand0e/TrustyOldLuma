# Technology Stack & Build System

## Core Technologies
- **Python 3.8+** - Main programming language with async/await support
- **Rich** - Terminal UI library for progress bars, panels, and styled output
- **aiohttp** - Async HTTP client for downloads
- **pathlib** - Modern path handling (prefer over os.path)
- **asyncio** - Async programming for responsive UI

## Dependencies
```
rich>=13.0.0
aiohttp>=3.8.0
```

## Testing Framework
- **pytest** - Primary testing framework with async support
- **pytest-cov** - Code coverage reporting
- **pytest-asyncio** - Async test support
- Coverage reports: HTML, terminal, and XML formats

## Build & Distribution
- **setuptools** - Package building and distribution
- **setup.py** - Package configuration with console entry points
- **setup.bat** - Windows batch script for automated setup
- Entry points: `luna`, `luna-setup`, and `luna-gaming-tool` (aliases)

## Common Commands

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests with coverage
python -m pytest -v --cov=. --cov-report=html

# Run specific test categories
python -m pytest -m unit
python -m pytest -m integration
python -m pytest -m slow

# Run the tool
python gaming_setup_tool.py
python gaming_setup_tool.py --dry-run --verbose
```

### Testing
```bash
# Run all tests
python run_tests.py

# Run with specific markers
pytest -m "unit and not slow"
pytest -m "integration and windows"
```

## Architecture Patterns
- **Manager Pattern** - Separate managers for different concerns (FileOperationsManager, SecurityConfigManager, etc.)
- **Async/Await** - All I/O operations are async for responsive UI
- **Rich Console Integration** - All managers accept Console instance for consistent output
- **Error Categorization** - Custom exception hierarchy with specific error types
- **Configuration Models** - Dataclasses for type-safe configuration management