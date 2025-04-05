@echo off
:: Check if running as admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting administrator privileges...
    powershell -Command "Start-Process -FilePath '%~dpnx0' -Verb RunAs"
    exit /b
)

setlocal enabledelayedexpansion

:: Create GreenLuma folder in Documents
set "greenLumaPath=%USERPROFILE%\Documents\GreenLuma"
if not exist "!greenLumaPath!" (
    mkdir "!greenLumaPath!"
    echo [OK] Created GreenLuma folder in Documents
)

:: Add Windows Security exclusion using PowerShell (more reliable method)
powershell -Command "Add-MpPreference -ExclusionPath '!greenLumaPath!'" >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] Added Windows Security exclusion for GreenLuma folder
) else (
    echo [Warning] Could not add Windows Security exclusion. You may need to add it manually.
)

:: Extract greenluma.zip to the GreenLuma folder
if exist "%~dp0greenluma.zip" (
    powershell -Command "Expand-Archive -Path '%~dp0greenluma.zip' -DestinationPath '!greenLumaPath!' -Force" >nul 2>&1
    if %errorLevel% equ 0 (
        echo [OK] Extracted GreenLuma files
    ) else (
        echo [ERROR] Failed to extract GreenLuma files
        pause
        exit /b 1
    )
) else (
    echo [ERROR] greenluma.zip not found in the script directory
    pause
    exit /b 1
)

:: Update DLLInjector.ini with the correct DLL path
set "dllPath=!greenLumaPath!\GreenLuma_2020_x86.dll"
if exist "!dllPath!" (
    powershell -Command "$content = Get-Content '!greenLumaPath!\DLLInjector.ini' -Raw; $content = $content -replace '(?m)^Dll = \".*\"', 'Dll = \"!dllPath!\"'; Set-Content '!greenLumaPath!\DLLInjector.ini' -Value $content" >nul 2>&1
    if %errorLevel% equ 0 (
        echo [OK] Updated DLLInjector.ini with DLL path: !dllPath!
    ) else (
        echo [WARNING] Could not update DLLInjector.ini
    )
) else (
    echo [WARNING] GreenLuma DLL not found at !dllPath!
)

:: Download Koalageddon installer
echo [INFO] Downloading Koalageddon installer...
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/acidicoala/Koalageddon/releases/download/v1.5.4/KoalageddonInstaller.exe' -OutFile '!greenLumaPath!\KoalageddonInstaller.exe'" >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] Downloaded Koalageddon installer
) else (
    echo [ERROR] Failed to download Koalageddon installer
    pause
    exit /b 1
)

:: Run Koalageddon installer
echo [INFO] Please run the Koalageddon installer when it appears
echo [INFO] After installation is complete, press any key to continue...
start "" "!greenLumaPath!\KoalageddonInstaller.exe"
pause >nul

:: Update Koalageddon config file
set "koalaConfig=C:\ProgramData\acidicoala\Koalageddon\Config.jsonc"
if exist "!koalaConfig!" (
    powershell -Command "$content = Get-Content '!koalaConfig!' -Raw; $content = $content -replace '\"replicate\": false', '\"replicate\": true' -replace '\"unlock_shared_library\": false', '\"unlock_shared_library\": true'; Set-Content '!koalaConfig!' -Value $content" >nul 2>&1
    if %errorLevel% equ 0 (
        echo [OK] Updated Koalageddon config file
    ) else (
        echo [WARNING] Could not update Koalageddon config file
    )
) else (
    echo [WARNING] Koalageddon config file not found at !koalaConfig!
)

:: Clean up Koalageddon installer and copy shortcut
del "!greenLumaPath!\KoalageddonInstaller.exe" >nul 2>&1
if exist "%USERPROFILE%\Desktop\Koalageddon.lnk" (
    copy "%USERPROFILE%\Desktop\Koalageddon.lnk" "!greenLumaPath!\Koalageddon.lnk" >nul 2>&1
    echo [OK] Copied Koalageddon shortcut to GreenLuma folder
)

:: Create GreenLuma shortcut with custom icon
set "iconPath=!greenLumaPath!\res\icon.png"
set "iconIcoPath=!greenLumaPath!\icon.ico"
if exist "!iconPath!" (
    powershell -Command "Add-Type -AssemblyName System.Drawing; [System.Drawing.Bitmap]::FromFile('!iconPath!').Save('!iconIcoPath!', [System.Drawing.Imaging.ImageFormat]::Ico)" >nul 2>&1
    if %errorLevel% neq 0 (
        echo [WARNING] Could not convert icon, using default icon
        set "iconIcoPath=!greenLumaPath!\DLLInjector.exe"
    )
) else (
    set "iconIcoPath=!greenLumaPath!\DLLInjector.exe"
)

>"%TEMP%\createshortcut.vbs" (
    echo Set oWS = WScript.CreateObject("WScript.Shell"^)
    echo sLinkFile = "%USERPROFILE%\Desktop\GreenLuma.lnk"
    echo Set oLink = oWS.CreateShortcut(sLinkFile^)
    echo oLink.TargetPath = "!greenLumaPath!\DLLInjector.exe"
    echo oLink.WorkingDirectory = "!greenLumaPath!"
    echo oLink.IconLocation = "!iconIcoPath!"
    echo oLink.Save
)
cscript //nologo "%TEMP%\createshortcut.vbs" >nul
if %errorLevel% equ 0 (
    echo [OK] Created desktop shortcut
) else (
    echo Error creating desktop shortcut
)
del "%TEMP%\createshortcut.vbs" >nul 2>&1

:: Create AppList folder and initial file
set "appListPath=%greenLumaPath%\AppList"
if not exist "!appListPath!" (
    mkdir "!appListPath!"
    echo [OK] Created AppList folder
)

set "appListFile=%appListPath%\0.txt"
if not exist "!appListFile!" (
    echo. > "!appListFile!"
    echo [OK] Created initial AppList file
)

:: Display completion message
echo.
echo [SUCCESS] Setup completed successfully!
echo.
echo Next steps:
echo   1. Make sure Steam is completely closed
echo   2. Double-click the GreenLuma shortcut on your desktop
echo   3. Steam will launch automatically with GreenLuma enabled
echo   4. To add games, open the AppList folder in Documents\GreenLuma
echo      and add the Steam App IDs to the text files
echo.
pause 