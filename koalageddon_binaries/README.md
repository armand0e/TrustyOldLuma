# Koalageddon Embedded Binaries

This directory should contain the Koalageddon binaries that will be embedded into the TrustyOldLuma installer.

## Required Files

The following files should be placed in this directory before building the installer:

### Core Executables
- `Koalageddon.exe` - Main Koalageddon application
- `IntegrationWizard.exe` - Platform integration utility
- `Injector.exe` - DLL injection utility

### Libraries
- `version.dll` - Integration library for platform hooking
- Any additional DLL dependencies

### Configuration Templates
- `Config.jsonc` - Default configuration template (optional, will use project's Config.jsonc if not present)

## How to Obtain Binaries

1. Download the latest Koalageddon release from: https://github.com/acidicoala/Koalageddon/releases/latest
2. Extract the installer or portable version
3. Copy the required files listed above to this directory
4. Run the build process to create the unified installer

## Build Integration

These binaries will be automatically included in the PyInstaller build process and embedded into the final executable. The `EmbeddedKoalageddonManager` will extract and use these files during installation.

## Legal Note

Ensure you comply with Koalageddon's 0BSD license when distributing these binaries. The license allows for unlimited use and distribution.