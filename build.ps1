#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Build script for TrustyOldLuma Setup
    
.DESCRIPTION
    Provides options for development and release builds with proper optimization.
    
.PARAMETER BuildType
    Type of build to create: 'dev', 'development', 'release', or 'clean'
    
.EXAMPLE
    .\build.ps1 dev
    .\build.ps1 release
    .\build.ps1 clean
#>

param(
    [Parameter(Position=0)]
    [ValidateSet('dev', 'development', 'release', 'clean')]
    [string]$BuildType = 'release'
)

# Set error action preference
$ErrorActionPreference = 'Stop'

Write-Host ""
Write-Host "========================================"
Write-Host " TrustyOldLuma Setup - Build Script"
Write-Host "========================================"
Write-Host ""

# Handle clean operation
if ($BuildType -eq 'clean') {
    Write-Host "Cleaning build artifacts..."
    
    $pathsToClean = @('dist', 'build', '__pycache__', 'src\__pycache__')
    foreach ($path in $pathsToClean) {
        if (Test-Path $path) {
            Remove-Item -Path $path -Recurse -Force
            Write-Host "Removed: $path"
        }
    }
    
    Write-Host "Clean completed."
    Write-Host ""
    Read-Host "Press Enter to continue"
    exit 0
}

# Normalize build type
if ($BuildType -eq 'development') {
    $BuildType = 'dev'
}

Write-Host "Build Type: $BuildType"
Write-Host ""

# Check dependencies
try {
    python -c "import PyInstaller" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller is not installed"
    }
} catch {
    Write-Error "ERROR: PyInstaller is not installed."
    Write-Host "Please install it with: pip install pyinstaller"
    Write-Host ""
    Read-Host "Press Enter to continue"
    exit 1
}

try {
    python -c "import rich" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Rich library is not installed"
    }
} catch {
    Write-Error "ERROR: Rich library is not installed."
    Write-Host "Please install dependencies with: pip install -r requirements.txt"
    Write-Host ""
    Read-Host "Press Enter to continue"
    exit 1
}

# Clean previous builds
Write-Host "Cleaning previous builds..."
$pathsToClean = @('dist', 'build')
foreach ($path in $pathsToClean) {
    if (Test-Path $path) {
        Remove-Item -Path $path -Recurse -Force
    }
}

# Create assets directory and icon if they don't exist
if (-not (Test-Path "assets")) {
    New-Item -ItemType Directory -Path "assets" | Out-Null
}

if (-not (Test-Path "assets\icon.ico")) {
    Write-Host "Creating application icon..."
    python assets\create_icon.py
}

Write-Host ""
Write-Host "Building $BuildType version..."
Write-Host ""

try {
    if ($BuildType -eq 'dev') {
        # Development build - faster, directory-based
        Write-Host "Running development build..."
        pyinstaller --clean --noconfirm setup-dev.spec
        
        if ($LASTEXITCODE -ne 0) {
            throw "Development build failed"
        }
        
        Write-Host ""
        Write-Host "========================================"
        Write-Host " Development Build Complete!"
        Write-Host "========================================"
        Write-Host ""
        Write-Host "Executable location: dist\TrustyOldLuma-Setup-Dev\TrustyOldLuma-Setup-Dev.exe"
        Write-Host ""
        Write-Host "To test the build:"
        Write-Host "  cd dist\TrustyOldLuma-Setup-Dev"
        Write-Host "  .\TrustyOldLuma-Setup-Dev.exe"
        Write-Host ""
        
    } else {
        # Release build - optimized, single file
        Write-Host "Running release build with optimizations..."
        pyinstaller --clean --noconfirm setup.spec
        
        if ($LASTEXITCODE -ne 0) {
            throw "Release build failed"
        }
        
        Write-Host ""
        Write-Host "========================================"
        Write-Host " Release Build Complete!"
        Write-Host "========================================"
        Write-Host ""
        Write-Host "Executable location: dist\TrustyOldLuma-Setup.exe"
        
        # Get file size
        if (Test-Path "dist\TrustyOldLuma-Setup.exe") {
            $fileSize = (Get-Item "dist\TrustyOldLuma-Setup.exe").Length
            Write-Host "File size: $fileSize bytes ($([math]::Round($fileSize / 1MB, 2)) MB)"
        }
        
        Write-Host ""
        Write-Host "To test the build:"
        Write-Host "  .\dist\TrustyOldLuma-Setup.exe"
        Write-Host ""
    }
    
    Write-Host "Build completed successfully!"
    Write-Host ""
    
} catch {
    Write-Error "ERROR: Build failed - $_"
    Write-Host ""
    Read-Host "Press Enter to continue"
    exit 1
}

Read-Host "Press Enter to continue"