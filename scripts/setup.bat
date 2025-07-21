@echo off


:: Check if running as admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo * This script requires administrator privileges.
    echo * Relaunching as administrator...
    powershell -Command "Start-Process '%~f0' -Verb RunAs -WorkingDirectory '%CD%'"
    exit /b
)

setlocal enabledelayedexpansion

echo.
echo +-------------------------------------------------------------+
echo ^|                 LUNA SETUP INITIALIZED                      ^|
echo +-------------------------------------------------------------+
echo.

echo ^* Creating required folders...
:: Create Luna folder in Documents
set "lunaPath=%USERPROFILE%\Documents\Luna"
if not exist "!lunaPath!" (
    mkdir "!lunaPath!"
    echo   [OK] Luna folder created in Documents.
) else (
    echo   [OK] Luna folder already exists.
)

echo.
echo ^* Configuring Windows Security exclusions...
:: Add Windows Security exclusion using PowerShell (more reliable method)
powershell -Command "Add-MpPreference -ExclusionPath '!lunaPath!'" >nul 2>&1
if %errorLevel% equ 0 (
    echo   [OK] Added exclusion for Luna folder.
) else (
    echo   [WARNING] Could not add exclusion for Luna. Please add it manually.
)

:: Add Windows Security exclusion for Luna Unlocker folder
set "lunaUnlockerPath=%USERPROFILE%\AppData\Local\Programs\Luna"
powershell -Command "Add-MpPreference -ExclusionPath '!lunaUnlockerPath!'" >nul 2>&1
if %errorLevel% equ 0 (
    echo   [OK] Added exclusion for Luna Unlocker folder.
) else (
    echo   [WARNING] Could not add exclusion for Luna Unlocker. Please add it manually.
)

echo.
echo ^* Extracting files...
:: Extract assets\luna\injector.zip to the Luna folder (flattening directory structure)
if exist "%~dp0assets\luna\injector.zip" (
    powershell -Command "$tempPath = Join-Path ([System.IO.Path]::GetTempPath()) ([System.IO.Path]::GetRandomFileName()); New-Item -ItemType Directory -Path $tempPath -Force | Out-Null; Expand-Archive -Path '%~dp0assets\luna\injector.zip' -DestinationPath $tempPath -Force; Get-ChildItem -Path $tempPath -Recurse -File | ForEach-Object { Move-Item $_.FullName -Destination '!lunaPath!' -Force }; Remove-Item -Path $tempPath -Recurse -Force" >nul 2>&1
    if %errorLevel% equ 0 (
        echo   [OK] Extracted Luna Injector files.
    ) else (
        echo   [ERROR] Failed to extract Luna Injector files.
        pause
        exit /b 1
    )
) else (
    echo   [ERROR] assets\luna\injector.zip not found in the script directory.
    pause
    exit /b 1
)

echo.
echo ^* Configuring Luna Injector...
:: Update luna_injector.ini with the correct DLL path
set "dllPath=!lunaPath!\luna_core_x86.dll"
if exist "!dllPath!" (
    powershell -Command "$content = Get-Content '!lunaPath!\luna_injector.ini' -Raw; $content = $content -replace '(?m)^Dll = \".*\"', 'Dll = \"!dllPath!\"'; Set-Content '!lunaPath!\luna_injector.ini' -Value $content" >nul 2>&1
    if %errorLevel% equ 0 (
        echo   [OK] Updated luna_injector.ini with path: !dllPath!
    ) else (
        echo   [WARNING] Could not update luna_injector.ini.
    )
) else (
    echo   [WARNING] Luna core DLL not found at !dllPath!
)

echo.
echo ^* Downloading Luna Unlocker...
:: Download Luna Unlocker installer
echo   Please wait while the installer is downloaded.
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/acidicoala/Koalageddon/releases/download/v1.5.4/KoalageddonInstaller.exe' -OutFile '!lunaPath!\LunaUnlockerInstaller.exe'" >nul 2>&1
if %errorLevel% equ 0 (
    echo   [OK] Downloaded Luna Unlocker installer.
) else (
    echo   [ERROR] Failed to download Luna Unlocker installer.
    pause
    exit /b 1
)

echo.
echo ^* Running Luna Unlocker installer...
:: Run Luna Unlocker installer
echo   The installer will open in a new window.
echo   Please follow the instructions, then close it to continue.
start /wait "" "!lunaPath!\LunaUnlockerInstaller.exe"
echo   [OK] Luna Unlocker installer finished.

echo.
echo ^* Updating configuration files...
:: Update Luna Unlocker config file
set "lunaConfigPath=%ProgramData%\Luna\Unlocker"
set "lunaConfigFile=!lunaConfigPath!\luna_config.jsonc"
set "repoConfigFile=%~dp0luna_config.jsonc"

if exist "!repoConfigFile!" (
    if exist "!lunaConfigPath!" (
        powershell -Command "try { $maxAttempts = 3; $attempt = 0; do { $attempt++; try { Start-Sleep -Milliseconds 500; Copy-Item -Path '!repoConfigFile!' -Destination '!lunaConfigFile!' -Force -ErrorAction Stop; break } catch { if ($attempt -eq $maxAttempts) { throw } } } while ($attempt -lt $maxAttempts); exit 0 } catch { exit 1 }" >nul 2>&1
        if %errorLevel% equ 0 (
            echo   [OK] Replaced Luna Unlocker config with repository version.
        ) else (
            echo   [WARNING] Could not replace Luna Unlocker config file. File may be in use.
        )
    ) else (
        echo   [WARNING] Luna Unlocker config directory not found. Skipping.
    )
) else (
    echo   [WARNING] Repository luna_config.jsonc not found. Skipping.
)

echo.
echo ^* Creating shortcuts and cleaning up...
:: Find desktop directory

set "desktopPath=%USERPROFILE%\Desktop"
if exist "!desktopPath!" (
    set "desktopPath=!desktopPath!"
) else (
    set "desktopPath=%USERPROFILE%\OneDrive\Desktop"
)
if exist "!desktopPath!" (
    set "desktopPath=!desktopPath!"
) else (
    echo   [WARNING] Could not find desktop directory.. skipping shortcut creation.
)

:: Clean up Luna Unlocker installer and copy shortcut
del "!lunaPath!\LunaUnlockerInstaller.exe" >nul 2>&1
if exist "!desktopPath!\Luna Unlocker.lnk" (
    copy "!desktopPath!\Luna Unlocker.lnk" "!lunaPath!\Luna Unlocker.lnk" >nul 2>&1
    echo   [OK] Copied Luna Unlocker shortcut to Luna folder.
)

:: Create Luna Injector shortcut with custom icon
set "iconPath=!lunaPath!\luna_icon.ico"

>"%TEMP%\createshortcut.vbs" (
    echo Set oWS = WScript.CreateObject("WScript.Shell"^)
    echo sLinkFile = "!desktopPath!\Luna Injector.lnk"
    echo Set oLink = oWS.CreateShortcut(sLinkFile^)
    echo oLink.TargetPath = "!lunaPath!\luna_injector.exe"
    echo oLink.WorkingDirectory = "!lunaPath!"
    echo oLink.IconLocation = "!iconPath!"
    echo oLink.Save
)
cscript //nologo "%TEMP%\createshortcut.vbs" >nul
if %errorLevel% equ 0 (
    echo   [OK] Created Luna Injector desktop shortcut.
) else (
    echo   [ERROR] Could not create Luna desktop shortcut.
)
del "%TEMP%\createshortcut.vbs" >nul 2>&1

:: Create AppList folder and initial file
set "appListPath=%lunaPath%\AppList"
if not exist "!appListPath!" (
    mkdir "!appListPath!"
    echo   [OK] Created AppList folder.
)

set "appListFile=%appListPath%\0.txt"
set "appId=252950"
echo !appId! > "!appListFile!"
echo   [OK] Created initial AppList file with App ID: !appId!

echo.
echo +-------------------------------------------------------------+
echo ^|                        NEXT STEPS                           ^|
echo +-------------------------------------------------------------+
echo.
echo   Step 1: Launch Luna Unlocker and click "Install platform integrations"
echo   Step 2: Double-click the Luna Injector shortcut and enjoy gaming!
echo.
echo +-------------------------------------------------------------+
echo ^|                    SHOW SOME LOVE!                          ^|
echo +-------------------------------------------------------------+
echo.
echo   Don't forget to star us on GitHub!
echo     https://github.com/armand0e/Luna
echo.
echo   Thanks for using Luna Gaming Tool^! Happy gaming^! ^<3
echo.
pause 
