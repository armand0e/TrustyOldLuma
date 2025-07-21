# 🌙 Luna Gaming Tool - Unified Steam Gaming Solution

Luna is a comprehensive gaming tool that combines DLL injection and DLC unlocking capabilities into a single, unified platform. Previously known as TrustyOldLuma, Luna provides a seamless experience for Steam game sharing and DLC management.

## 📋 Table of Contents
- [Installation](#-installation)
- [Migration from Legacy Tools](#-migration-from-legacy-tools)
- [Steam Family Sharing](#-steam-family-sharing)
- [Adding Games](#-adding-games)
- [Luna Features](#-luna-features)
- [Troubleshooting](#-troubleshooting)

## 🚀 Installation

### Quick Setup (Recommended)
1. Download the latest Luna version from [here](https://github.com/armand0e/TrustyOldLuna/releases/latest)
2. Extract the zip file to any location
3. Right-click `setup.bat` and select "Run as administrator"
4. Follow the on-screen instructions
5. The Luna setup script will:
   - Create a Luna folder in your Documents
   - Add Windows Security exclusions for Luna components
   - Set up Luna injector and unlocker components
   - Create desktop shortcuts for Luna tools
   - Configure unified Luna settings
   - Automatically migrate existing GreenLuma/Koalageddon installations if found

### Manual Setup (Alternative)
If the automated setup doesn't work, you can follow these steps:

1. Create a folder named "Luna" in your Documents folder
2. Extract all Luna files from the zip into this folder
3. Add the Luna folder to Windows Security exclusions:
   - Open Windows Security
   - Go to Virus & threat protection
   - Click "Manage settings" under Virus & threat protection settings
   - Scroll down to Exclusions
   - Click "Add or remove exclusions"
   - Add the Luna folder and all its subdirectories
4. Run the Luna setup tool manually:
   - Open Command Prompt as Administrator
   - Navigate to the Luna folder
   - Run: `python luna.py --setup`
5. Create desktop shortcuts using Luna's shortcut manager

## 🔄 Migration from Legacy Tools

### Automatic Migration
Luna automatically detects and migrates existing GreenLuma and Koalageddon installations:

1. **Existing GreenLuma**: Luna will detect your GreenLuma folder and migrate:
   - AppList configurations
   - DLL injection settings
   - Custom configurations
   - Desktop shortcuts

2. **Existing Koalageddon**: Luna will detect Koalageddon installations and migrate:
   - DLC unlocking settings
   - Platform configurations
   - User preferences

3. **Migration Process**: During first-time setup, Luna will:
   - Scan for existing installations
   - Backup your current configurations
   - Migrate settings to Luna's unified format
   - Update shortcuts to use Luna branding
   - Preserve all functionality while unifying the interface

### Manual Migration
If automatic migration doesn't work:
1. Run Luna setup with migration flag: `python luna.py --migrate`
2. Follow the migration wizard prompts
3. Verify your games and settings after migration

## 🏠 Steam Family Sharing
Luna works seamlessly with Steam Family Sharing. For detailed instructions on setting up Steam Family Sharing, please refer to the [Steam Families User Guide & FAQ](https://help.steampowered.com/en/faqs/view/054C-3167-DD7F-49D4)

Luna enhances Steam Family Sharing by providing:
- Unified game library management
- Automatic DLC unlocking for shared games
- Streamlined injection process
- Enhanced compatibility across gaming platforms

## 🎮 Adding Games

### Step 1: Find Game IDs
1. Go to [SteamDB](https://steamdb.info/)
2. Search for the game you want to play
3. Copy the number shown as "App ID"

### Step 2: Add Game to Luna
1. Open your Documents folder
2. Go to the Luna folder
3. Open the AppList folder (or use Luna's GUI for easier management)
4. Open `0.txt` (or create a new file if you're adding multiple games)
5. Paste the App ID number you copied
6. Save the file

### Alternative: Using Luna GUI
1. Launch Luna from your desktop shortcut
2. Navigate to the "Game Management" section
3. Click "Add Game"
4. Enter the App ID or search by game name
5. Luna will automatically configure the game for injection and DLC unlocking

## 🌙 Luna Features

Luna combines the best of both worlds, providing:

### Unified Gaming Experience
- **Single Interface**: Manage both injection and DLC unlocking from one application
- **Automatic Detection**: Luna automatically detects supported games and platforms
- **Smart Configuration**: Intelligent configuration management for optimal performance
- **Real-time Monitoring**: Live status updates and process monitoring

### Enhanced Functionality
- **Multi-Platform Support**: Works with Steam, Epic Games, Origin, and Ubisoft Connect
- **Advanced DLC Management**: Comprehensive DLC unlocking with granular control
- **Security Integration**: Automatic Windows Defender exclusion management
- **Backup & Restore**: Built-in configuration backup and restore capabilities

### Modern Interface
- **Rich Console UI**: Beautiful terminal interface with progress indicators
- **GUI Application**: Optional Electron-based GUI for visual management
- **Comprehensive Logging**: Detailed logging for troubleshooting and monitoring
- **Error Recovery**: Intelligent error handling and recovery mechanisms

## 🚀 How to Use

### Step 1: Start Fresh
1. Make sure Steam is completely closed
   - Right-click the Steam icon in your system tray (bottom-right corner)
   - Select "Exit Steam"

### Step 2: Launch with Luna
1. Double-click the Luna shortcut on your desktop
2. Steam will launch automatically with Luna injection enabled
3. Luna will automatically handle DLC unlocking for supported games

### Step 3: Monitor Luna Status
1. Luna runs in the background and provides real-time status updates
2. Check the Luna system tray icon for current status
3. Use Luna GUI for detailed monitoring and configuration

## ❓ Troubleshooting

### Common Issues

1. **Luna Setup Script Won't Run**
   - Make sure you're running the script as Administrator
   - Check if your antivirus is blocking Luna components
   - Try running the manual setup steps
   - Verify Windows Defender exclusions are properly configured

2. **Luna Won't Launch**
   - Ensure Steam is completely closed before launching Luna
   - Verify the game owner's account is still logged in
   - Check that you ran the Luna setup script as Administrator
   - Make sure Luna components are properly installed in the Luna directory
   - Check Luna logs for specific error messages

3. **Games Not Showing Up**
   - Verify the App IDs are correct in your Luna AppList
   - Make sure the AppList files are saved properly in the Luna folder
   - Check that Steam Family Sharing is set up correctly
   - Ensure Luna's DLC unlocking is enabled in configuration
   - Verify platform-specific settings in Luna configuration

4. **Migration Issues**
   - If automatic migration fails, try manual migration: `python luna.py --migrate`
   - Check that legacy GreenLuma/Koalageddon installations are accessible
   - Verify file permissions on legacy installation directories
   - Review migration logs for specific error details

5. **DLC Not Unlocking**
   - Ensure Luna's unlocker component is enabled
   - Check platform-specific DLC settings in Luna configuration
   - Verify the game supports DLC unlocking
   - Check Luna logs for DLC-related error messages

### Luna-Specific Troubleshooting

1. **Component Communication Issues**
   - Restart Luna to reinitialize component communication
   - Check Windows firewall settings for Luna components
   - Verify Luna API service is running properly

2. **Configuration Problems**
   - Reset Luna configuration: `python luna.py --reset-config`
   - Restore from backup: `python luna.py --restore-config`
   - Validate configuration: `python luna.py --validate-config`

### Need More Help?
If you're still having issues:
1. Try running the Luna setup script again
2. Check the [Steam Family Sharing FAQ](https://help.steampowered.com/en/faqs/view/054C-3167-DD7F-49D4)
3. Review Luna logs in the Luna/logs directory
4. Create an issue on the [GitHub repository](https://github.com/armand0e/TrustyOldLuna/issues)
5. Include Luna version, OS version, and relevant log files when reporting issues

### Advanced Troubleshooting
For advanced users:
- Enable verbose logging: `python luna.py --verbose`
- Run Luna in debug mode: `python luna.py --debug`
- Check system compatibility: `python luna.py --check-system`
- Generate diagnostic report: `python luna.py --diagnostic`
