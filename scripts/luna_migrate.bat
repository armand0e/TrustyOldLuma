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
echo ^|                 LUNA MIGRATION TOOL                         ^|
echo +-------------------------------------------------------------+
echo.
echo   This tool will migrate your existing GreenLuma and
echo   Koalageddon installations to the unified Luna system.
echo.
echo   A backup will be created before any changes are made.
echo.
pause

:: Initialize variables
set "lunaPath=%USERPROFILE%\Documents\Luna"
set "greenLumaPath=%USERPROFILE%\Documents\GreenLuma"
set "koalageddonPath=%USERPROFILE%\AppData\Local\Programs\Koalageddon"
set "koalageddonConfigPath=%ProgramData%\acidicoala\Koalageddon"
set "backupPath=%USERPROFILE%\Documents\Luna_Migration_Backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "backupPath=!backupPath: =0!"
set "foundLegacy=false"

echo.
echo +-------------------------------------------------------------+
echo ^|                  DETECTING INSTALLATIONS                    ^|
echo +-------------------------------------------------------------+
echo.

:: Detect existing GreenLuma installation
if exist "!greenLumaPath!" (
    echo   [FOUND] GreenLuma installation detected at: !greenLumaPath!
    set "foundLegacy=true"
    set "hasGreenLuma=true"
) else (
    echo   [INFO] No GreenLuma installation found.
    set "hasGreenLuma=false"
)

:: Detect existing Koalageddon installation
if exist "!koalageddonPath!" (
    echo   [FOUND] Koalageddon installation detected at: !koalageddonPath!
    set "foundLegacy=true"
    set "hasKoalageddon=true"
) else (
    echo   [INFO] No Koalageddon installation found.
    set "hasKoalageddon=false"
)

:: Check for Koalageddon configuration
if exist "!koalageddonConfigPath!" (
    echo   [FOUND] Koalageddon configuration detected at: !koalageddonConfigPath!
    set "foundLegacy=true"
    set "hasKoalageddonConfig=true"
) else (
    echo   [INFO] No Koalageddon configuration found.
    set "hasKoalageddonConfig=false"
)

if "!foundLegacy!"=="false" (
    echo.
    echo   [INFO] No legacy installations found. Nothing to migrate.
    echo   [INFO] You can proceed with a fresh Luna installation.
    echo.
    pause
    exit /b 0
)

echo.
echo +-------------------------------------------------------------+
echo ^|                    CREATING BACKUP                          ^|
echo +-------------------------------------------------------------+
echo.

:: Create backup directory
if not exist "!backupPath!" (
    mkdir "!backupPath!"
    echo   [OK] Created backup directory: !backupPath!
) else (
    echo   [WARNING] Backup directory already exists: !backupPath!
)

:: Backup GreenLuma if it exists
if "!hasGreenLuma!"=="true" (
    echo   [BACKUP] Backing up GreenLuma installation...
    xcopy "!greenLumaPath!" "!backupPath!\GreenLuma\" /E /I /H /Y >nul 2>&1
    if %errorLevel% equ 0 (
        echo   [OK] GreenLuma backup completed.
    ) else (
        echo   [ERROR] Failed to backup GreenLuma installation.
        pause
        exit /b 1
    )
)

:: Backup Koalageddon if it exists
if "!hasKoalageddon!"=="true" (
    echo   [BACKUP] Backing up Koalageddon installation...
    xcopy "!koalageddonPath!" "!backupPath!\Koalageddon\" /E /I /H /Y >nul 2>&1
    if %errorLevel% equ 0 (
        echo   [OK] Koalageddon backup completed.
    ) else (
        echo   [ERROR] Failed to backup Koalageddon installation.
        pause
        exit /b 1
    )
)

:: Backup Koalageddon configuration if it exists
if "!hasKoalageddonConfig!"=="true" (
    echo   [BACKUP] Backing up Koalageddon configuration...
    xcopy "!koalageddonConfigPath!" "!backupPath!\KoalageddonConfig\" /E /I /H /Y >nul 2>&1
    if %errorLevel% equ 0 (
        echo   [OK] Koalageddon configuration backup completed.
    ) else (
        echo   [ERROR] Failed to backup Koalageddon configuration.
        pause
        exit /b 1
    )
)

echo.
echo +-------------------------------------------------------------+
echo ^|                   MIGRATING TO LUNA                         ^|
echo +-------------------------------------------------------------+
echo.

:: Create Luna directory
if not exist "!lunaPath!" (
    mkdir "!lunaPath!"
    echo   [OK] Created Luna directory: !lunaPath!
) else (
    echo   [INFO] Luna directory already exists: !lunaPath!
)

:: Migrate GreenLuma files
if "!hasGreenLuma!"=="true" (
    echo   [MIGRATE] Migrating GreenLuma files to Luna...
    
    :: Copy GreenLuma files to Luna directory
    xcopy "!greenLumaPath!\*" "!lunaPath!\" /E /H /Y >nul 2>&1
    if %errorLevel% equ 0 (
        echo   [OK] GreenLuma files migrated to Luna.
    ) else (
        echo   [ERROR] Failed to migrate GreenLuma files.
        pause
        exit /b 1
    )
    
    :: Rename files to Luna naming convention
    if exist "!lunaPath!\DLLInjector.exe" (
        ren "!lunaPath!\DLLInjector.exe" "luna_injector.exe" >nul 2>&1
        echo   [OK] Renamed DLLInjector.exe to luna_injector.exe
    )
    
    if exist "!lunaPath!\DLLInjector.ini" (
        ren "!lunaPath!\DLLInjector.ini" "luna_injector.ini" >nul 2>&1
        echo   [OK] Renamed DLLInjector.ini to luna_injector.ini
    )
    
    if exist "!lunaPath!\GreenLuma_2020_x64.dll" (
        ren "!lunaPath!\GreenLuma_2020_x64.dll" "luna_core_x64.dll" >nul 2>&1
        echo   [OK] Renamed GreenLuma_2020_x64.dll to luna_core_x64.dll
    )
    
    if exist "!lunaPath!\GreenLuma_2020_x86.dll" (
        ren "!lunaPath!\GreenLuma_2020_x86.dll" "luna_core_x86.dll" >nul 2>&1
        echo   [OK] Renamed GreenLuma_2020_x86.dll to luna_core_x86.dll
    )
    
    if exist "!lunaPath!\GreenLumaSettings_2023.exe" (
        ren "!lunaPath!\GreenLumaSettings_2023.exe" "luna_settings.exe" >nul 2>&1
        echo   [OK] Renamed GreenLumaSettings_2023.exe to luna_settings.exe
    )
    
    :: Update configuration file paths
    if exist "!lunaPath!\luna_injector.ini" (
        powershell -Command "$content = Get-Content '!lunaPath!\luna_injector.ini' -Raw; $content = $content -replace 'GreenLuma_2020_x86\.dll', 'luna_core_x86.dll'; $content = $content -replace 'GreenLuma_2020_x64\.dll', 'luna_core_x64.dll'; Set-Content '!lunaPath!\luna_injector.ini' -Value $content" >nul 2>&1
        echo   [OK] Updated luna_injector.ini with new DLL paths
    )
)

:: Create unified Luna configuration
echo   [CONFIG] Creating unified Luna configuration...
set "lunaConfigFile=!lunaPath!\luna_config.jsonc"

>"%lunaConfigFile%" (
    echo {
    echo   "luna": {
    echo     "version": "1.0.0",
    echo     "migrated_from_legacy": true,
    echo     "migration_date": "%date% %time%",
    echo     "core": {
    echo       "injector_enabled": !hasGreenLuma!,
    echo       "unlocker_enabled": !hasKoalageddon!,
    echo       "auto_start": false,
    echo       "stealth_mode": true
    echo     },
    echo     "platforms": {
    echo       "steam": { "enabled": true, "priority": 1 },
    echo       "epic": { "enabled": true, "priority": 2 },
    echo       "origin": { "enabled": true, "priority": 3 },
    echo       "uplay": { "enabled": true, "priority": 4 }
    echo     },
    echo     "paths": {
    echo       "core_directory": "!lunaPath!",
    echo       "config_directory": "!lunaPath!",
    echo       "temp_directory": "%TEMP%\\Luna"
    echo     },
    echo     "legacy": {
    echo       "greenluma_path": "!greenLumaPath!",
    echo       "koalageddon_path": "!koalageddonPath!",
    echo       "backup_path": "!backupPath!"
    echo     }
    echo   }
    echo }
)
echo   [OK] Created unified Luna configuration file.

echo.
echo +-------------------------------------------------------------+
echo ^|                  UPDATING SHORTCUTS                         ^|
echo +-------------------------------------------------------------+
echo.

:: Find desktop directory
set "desktopPath=%USERPROFILE%\Desktop"
if not exist "!desktopPath!" (
    set "desktopPath=%USERPROFILE%\OneDrive\Desktop"
)

if exist "!desktopPath!" (
    :: Update GreenLuma shortcut to Luna Injector
    if exist "!desktopPath!\GreenLuma.lnk" (
        echo   [UPDATE] Updating GreenLuma shortcut to Luna Injector...
        del "!desktopPath!\GreenLuma.lnk" >nul 2>&1
        
        >"%TEMP%\createshortcut.vbs" (
            echo Set oWS = WScript.CreateObject("WScript.Shell"^)
            echo sLinkFile = "!desktopPath!\Luna Injector.lnk"
            echo Set oLink = oWS.CreateShortcut(sLinkFile^)
            echo oLink.TargetPath = "!lunaPath!\luna_injector.exe"
            echo oLink.WorkingDirectory = "!lunaPath!"
            echo oLink.Description = "Luna Gaming Tool - Injector Component"
            echo oLink.Save
        )
        cscript //nologo "%TEMP%\createshortcut.vbs" >nul
        del "%TEMP%\createshortcut.vbs" >nul 2>&1
        echo   [OK] Created Luna Injector shortcut.
    )
    
    :: Update Koalageddon shortcut to Luna Unlocker
    if exist "!desktopPath!\Koalageddon.lnk" (
        echo   [UPDATE] Updating Koalageddon shortcut to Luna Unlocker...
        
        :: Get the target path from the existing shortcut
        for /f "tokens=*" %%i in ('powershell -Command "$sh = New-Object -ComObject WScript.Shell; $lnk = $sh.CreateShortcut('!desktopPath!\Koalageddon.lnk'); $lnk.TargetPath"') do set "koalaTarget=%%i"
        
        del "!desktopPath!\Koalageddon.lnk" >nul 2>&1
        
        >"%TEMP%\createshortcut.vbs" (
            echo Set oWS = WScript.CreateObject("WScript.Shell"^)
            echo sLinkFile = "!desktopPath!\Luna Unlocker.lnk"
            echo Set oLink = oWS.CreateShortcut(sLinkFile^)
            echo oLink.TargetPath = "!koalaTarget!"
            echo oLink.Description = "Luna Gaming Tool - Unlocker Component"
            echo oLink.Save
        )
        cscript //nologo "%TEMP%\createshortcut.vbs" >nul
        del "%TEMP%\createshortcut.vbs" >nul 2>&1
        echo   [OK] Created Luna Unlocker shortcut.
    )
) else (
    echo   [WARNING] Could not find desktop directory. Skipping shortcut updates.
)

echo.
echo +-------------------------------------------------------------+
echo ^|                 UPDATING SECURITY EXCLUSIONS                ^|
echo +-------------------------------------------------------------+
echo.

:: Add Luna security exclusions
echo   [SECURITY] Adding Windows Defender exclusions for Luna...
powershell -Command "Add-MpPreference -ExclusionPath '!lunaPath!'" >nul 2>&1
if %errorLevel% equ 0 (
    echo   [OK] Added exclusion for Luna directory.
) else (
    echo   [WARNING] Could not add exclusion for Luna directory.
)

echo.
echo +-------------------------------------------------------------+
echo ^|                   MIGRATION COMPLETE                        ^|
echo +-------------------------------------------------------------+
echo.
echo   Migration Summary:
if "!hasGreenLuma!"=="true" (
    echo   - GreenLuma installation migrated to Luna Injector
)
if "!hasKoalageddon!"=="true" (
    echo   - Koalageddon installation preserved as Luna Unlocker
)
if "!hasKoalageddonConfig!"=="true" (
    echo   - Koalageddon configuration backed up
)
echo   - Unified Luna configuration created
echo   - Desktop shortcuts updated with Luna branding
echo   - Security exclusions updated
echo.
echo   Backup Location: !backupPath!
echo.
echo   Next Steps:
echo   1. Test Luna Injector functionality
echo   2. Test Luna Unlocker functionality  
echo   3. Verify all games work as expected
echo   4. If everything works, you can safely delete the backup
echo.
echo   Thanks for migrating to Luna Gaming Tool^! Happy gaming^! ^<3
echo.
pause