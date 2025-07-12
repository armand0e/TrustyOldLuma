@echo off


:: Check if running as admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    :: Check if already in Windows Terminal (WT_SESSION is set)
    if "%WT_SESSION%"=="" (
        echo * Relaunching in Windows Terminal as administrator...
        :: Launch Windows Terminal as admin, running this script
        start "" wt.exe -w 0 nt -d "%CD%" "Start-Process cmd -ArgumentList '/c \"cd /d \"%CD%\" && \"%~nx0\"\"' -Verb RunAs"
        exit /b
    ) else (
        echo * Relaunching as administrator...
        powershell -Command "Start-Process cmd -ArgumentList '/c \"cd /d \"%CD%\" && \"%~nx0\"\"' -Verb RunAs"
        exit /b
    )
)

setlocal enabledelayedexpansion

echo.
echo +-------------------------------------------------------------+
echo ^|                 SETUP SCRIPT INITIALIZED                    ^|
echo +-------------------------------------------------------------+
echo.

echo ^* Creating required folders...
:: Create GreenLuma folder in Documents
set "greenLumaPath=%USERPROFILE%\Documents\GreenLuma"
if not exist "!greenLumaPath!" (
    mkdir "!greenLumaPath!"
    echo   [OK] GreenLuma folder created in Documents.
) else (
    echo   [OK] GreenLuma folder already exists.
)

echo.
echo ^* Configuring Windows Security exclusions...
:: Add Windows Security exclusion using PowerShell (more reliable method)
powershell -Command "Add-MpPreference -ExclusionPath '!greenLumaPath!'" >nul 2>&1
if %errorLevel% equ 0 (
    echo   [OK] Added exclusion for GreenLuma folder.
) else (
    echo   [WARNING] Could not add exclusion for GreenLuma. Please add it manually.
)

:: Add Windows Security exclusion for Koalageddon folder
set "koalageddonPath=%USERPROFILE%\AppData\Local\Programs\Koalageddon"
powershell -Command "Add-MpPreference -ExclusionPath '!koalageddonPath!'" >nul 2>&1
if %errorLevel% equ 0 (
    echo   [OK] Added exclusion for Koalageddon folder.
) else (
    echo   [WARNING] Could not add exclusion for Koalageddon. Please add it manually.
)

echo.
echo ^* Extracting files...
:: Extract greenluma.zip to the GreenLuma folder (flattening directory structure)
if exist "%~dp0greenluma.zip" (
    powershell -Command "$tempPath = Join-Path ([System.IO.Path]::GetTempPath()) ([System.IO.Path]::GetRandomFileName()); New-Item -ItemType Directory -Path $tempPath -Force | Out-Null; Expand-Archive -Path '%~dp0greenluma.zip' -DestinationPath $tempPath -Force; Get-ChildItem -Path $tempPath -Recurse -File | ForEach-Object { Move-Item $_.FullName -Destination '!greenLumaPath!' -Force }; Remove-Item -Path $tempPath -Recurse -Force" >nul 2>&1
    if %errorLevel% equ 0 (
        echo   [OK] Extracted GreenLuma files.
    ) else (
        echo   [ERROR] Failed to extract GreenLuma files.
        pause
        exit /b 1
    )
) else (
    echo   [ERROR] greenluma.zip not found in the script directory.
    pause
    exit /b 1
)

echo.
echo ^* Configuring GreenLuma...
:: Update DLLInjector.ini with the correct DLL path
set "dllPath=!greenLumaPath!\GreenLuma_2020_x86.dll"
if exist "!dllPath!" (
    powershell -Command "$content = Get-Content '!greenLumaPath!\DLLInjector.ini' -Raw; $content = $content -replace '(?m)^Dll = \".*\"', 'Dll = \"!dllPath!\"'; Set-Content '!greenLumaPath!\DLLInjector.ini' -Value $content" >nul 2>&1
    if %errorLevel% equ 0 (
        echo   [OK] Updated DLLInjector.ini with path: !dllPath!
    ) else (
        echo   [WARNING] Could not update DLLInjector.ini.
    )
) else (
    echo   [WARNING] GreenLuma DLL not found at !dllPath!
)

echo.
echo ^* Downloading Koalageddon...
:: Download Koalageddon installer
echo   Please wait while the installer is downloaded.
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/acidicoala/Koalageddon/releases/download/v1.5.4/KoalageddonInstaller.exe' -OutFile '!greenLumaPath!\KoalageddonInstaller.exe'" >nul 2>&1
if %errorLevel% equ 0 (
    echo   [OK] Downloaded Koalageddon installer.
) else (
    echo   [ERROR] Failed to download Koalageddon installer.
    pause
    exit /b 1
)

echo.
echo ^* Running Koalageddon installer...
:: Run Koalageddon installer
echo   The installer will open in a new window.
echo   Please follow the instructions, then close it to continue.
start /wait "" "!greenLumaPath!\KoalageddonInstaller.exe"
echo   [OK] Koalageddon installer finished.

echo.
echo ^* Updating configuration files...
:: Update Koalageddon config file
set "koalaConfigPath=%ProgramData%\acidicoala\Koalageddon"
set "koalaConfigFile=!koalaConfigPath!\Config.jsonc"
set "repoConfigFile=%~dp0Config.jsonc"

if exist "!repoConfigFile!" (
    if exist "!koalaConfigPath!" (
        copy /Y "!repoConfigFile!" "!koalaConfigFile!" >nul 2>&1
        if %errorLevel% equ 0 (
            echo   [OK] Replaced Koalageddon config with repository version.
        ) else (
            echo   [ERROR] Failed to replace Koalageddon config file.
        )
    ) else (
        echo   [WARNING] Koalageddon config directory not found. Skipping.
    )
) else (
    echo   [WARNING] Repository Config.jsonc not found. Skipping.
)

echo.
echo ^* Creating shortcuts and cleaning up...
:: Clean up Koalageddon installer and copy shortcut
del "!greenLumaPath!\KoalageddonInstaller.exe" >nul 2>&1
if exist "%USERPROFILE%\Desktop\Koalageddon.lnk" (
    copy "%USERPROFILE%\Desktop\Koalageddon.lnk" "!greenLumaPath!\Koalageddon.lnk" >nul 2>&1
    echo   [OK] Copied Koalageddon shortcut to GreenLuma folder.
)

:: Create GreenLuma shortcut with custom icon
set "iconPath=!greenLumaPath!\res\icon.ico"

>"%TEMP%\createshortcut.vbs" (
    echo Set oWS = WScript.CreateObject("WScript.Shell"^)
    echo sLinkFile = "%USERPROFILE%\Desktop\GreenLuma.lnk"
    echo Set oLink = oWS.CreateShortcut(sLinkFile^)
    echo oLink.TargetPath = "!greenLumaPath!\DLLInjector.exe"
    echo oLink.WorkingDirectory = "!greenLumaPath!"
    echo oLink.IconLocation = "!iconPath!"
    echo oLink.Save
)
cscript //nologo "%TEMP%\createshortcut.vbs" >nul
if %errorLevel% equ 0 (
    echo   [OK] Created GreenLuma desktop shortcut.
) else (
    echo   [ERROR] Could not create desktop shortcut.
)
del "%TEMP%\createshortcut.vbs" >nul 2>&1

:: Create AppList folder and initial file
set "appListPath=%greenLumaPath%\AppList"
if not exist "!appListPath!" (
    mkdir "!appListPath!"
    echo   [OK] Created AppList folder.
)

set "appListFile=%appListPath%\0.txt"
echo 252950 > "!appListFile!"
echo   [OK] Created initial AppList file with App ID: !appId!

echo.
echo +-------------------------------------------------------------+
echo ^|                        NEXT STEPS                           ^|
echo +-------------------------------------------------------------+
echo.
echo   Step 1: Launch Koalageddon and click "Install platform integrations"
echo   Step 2: Double-click the GreenLuma shortcut and enjoy gaming!
echo.
echo +-------------------------------------------------------------+
echo ^|                    SHOW SOME LOVE!                          ^|
echo +-------------------------------------------------------------+
echo.
echo   Don't forget to star us on GitHub!
echo     https://github.com/armand0e/TrustyOldLuma
echo.
echo   Thanks for using TrustyOldLuma^! Happy gaming^! ^<3
echo.
pause 