@echo off
REM Build script for TrustyOldLuma Setup
REM Provides options for development and release builds

setlocal enabledelayedexpansion

echo.
echo ========================================
echo  TrustyOldLuma Setup - Build Script
echo ========================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo ERROR: PyInstaller is not installed.
    echo Please install it with: pip install pyinstaller
    echo.
    pause
    exit /b 1
)

REM Check if Rich is installed
python -c "import rich" 2>nul
if errorlevel 1 (
    echo ERROR: Rich library is not installed.
    echo Please install dependencies with: pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Parse command line arguments
set BUILD_TYPE=release
if "%1"=="dev" set BUILD_TYPE=dev
if "%1"=="development" set BUILD_TYPE=dev
if "%1"=="release" set BUILD_TYPE=release
if "%1"=="clean" goto :clean

echo Build Type: %BUILD_TYPE%
echo.

REM Clean previous builds
if exist "dist" (
    echo Cleaning previous builds...
    rmdir /s /q "dist" 2>nul
)
if exist "build" (
    rmdir /s /q "build" 2>nul
)

REM Create assets directory and icon if they don't exist
if not exist "assets" mkdir "assets"
if not exist "assets\icon.ico" (
    echo Creating application icon...
    python assets\create_icon.py
)

echo.
echo Building %BUILD_TYPE% version...
echo.

if "%BUILD_TYPE%"=="dev" (
    REM Development build - faster, directory-based
    echo Running development build...
    pyinstaller --clean --noconfirm setup-dev.spec
    
    if errorlevel 1 (
        echo.
        echo ERROR: Development build failed!
        pause
        exit /b 1
    )
    
    echo.
    echo ========================================
    echo  Development Build Complete!
    echo ========================================
    echo.
    echo Executable location: dist\TrustyOldLuma-Setup-Dev\TrustyOldLuma-Setup-Dev.exe
    echo.
    echo To test the build:
    echo   cd dist\TrustyOldLuma-Setup-Dev
    echo   TrustyOldLuma-Setup-Dev.exe
    echo.
    
) else (
    REM Release build - optimized, single file
    echo Running release build with optimizations...
    pyinstaller --clean --noconfirm setup.spec
    
    if errorlevel 1 (
        echo.
        echo ERROR: Release build failed!
        pause
        exit /b 1
    )
    
    echo.
    echo ========================================
    echo  Release Build Complete!
    echo ========================================
    echo.
    echo Executable location: dist\TrustyOldLuma-Setup.exe
    echo File size: 
    for %%A in ("dist\TrustyOldLuma-Setup.exe") do echo   %%~zA bytes
    echo.
    echo To test the build:
    echo   dist\TrustyOldLuma-Setup.exe
    echo.
)

echo Build completed successfully!
echo.
pause
exit /b 0

:clean
echo Cleaning build artifacts...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "__pycache__" rmdir /s /q "__pycache__"
if exist "src\__pycache__" rmdir /s /q "src\__pycache__"
echo Clean completed.
echo.
pause
exit /b 0