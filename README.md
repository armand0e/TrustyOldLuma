# 🎮 TrustyOldLuma - Steam Game Sharing Tool

## 📋 Table of Contents
- [Installation](#-installation)
- [Steam Family Sharing](#-steam-family-sharing)
- [Adding Games](#-adding-games)
- [Troubleshooting](#-troubleshooting)

## 🚀 Installation

### Quick Setup (Recommended)
1. Download the latest version from [here](https://github.com/armand0e/TrustyOldLuma/releases/latest)
2. Extract the zip file to any location
3. Open PowerShell as Administrator:
   - Press `Win + X`
   - Select "Windows PowerShell (Admin)" or "Terminal (Admin)"
4. Navigate to the extracted folder:
   ```powershell
   cd "path\to\extracted\folder"
   ```
5. Run the setup script:
   ```powershell
   .\setup.ps1
   ```
6. Follow the on-screen instructions
7. A GreenLuma shortcut will be created on your desktop

### Manual Setup (Alternative)
If the automated setup doesn't work, you can follow these steps:

1. Create a folder named "GreenLuma" in your Documents folder
2. Extract all files from the zip into this folder
3. Add the GreenLuma folder to Windows Security exclusions:
   - Open Windows Security
   - Go to Virus & threat protection
   - Click "Manage settings" under Virus & threat protection settings
   - Scroll down to Exclusions
   - Click "Add or remove exclusions"
   - Add the GreenLuma folder

## 🏠 Steam Family Sharing
For detailed instructions on setting up Steam Family Sharing, please refer to the [Steam Families User Guide & FAQ](https://help.steampowered.com/en/faqs/view/054C-3167-DD7F-49D4)

## 🎮 Adding Games

### Step 1: Find Game IDs
1. Go to [SteamDB](https://steamdb.info/)
2. Search for the game you want to play
3. Copy the number shown as "App ID"

### Step 2: Add Game to GreenLuma
1. Open your Documents folder
2. Go to the GreenLuma folder
3. Open the AppList folder
4. Open `0.txt` (or create a new file if you're adding multiple games)
5. Paste the App ID number you copied
6. Save the file

## 🚀 How to Use

### Step 1: Start Fresh
1. Make sure Steam is completely closed
   - Right-click the Steam icon in your system tray (bottom-right corner)
   - Select "Exit Steam"

### Step 2: Launch with GreenLuma
1. Double-click the GreenLuma shortcut on your desktop
2. Steam will launch automatically with GreenLuma enabled

## ❓ Troubleshooting

### Common Issues
1. **Setup Script Won't Run**
   - Make sure you're running PowerShell as Administrator
   - Check if your antivirus is blocking the script
   - Try running the manual setup steps

2. **GreenLuma Won't Launch**
   - Ensure Steam is completely closed
   - Verify the game owner's account is still logged in
   - Check that you ran the setup script as Administrator

3. **Games Not Showing Up**
   - Verify the App IDs are correct
   - Make sure the AppList files are saved properly
   - Check that Steam Family Sharing is set up correctly

### Need More Help?
If you're still having issues:
1. Try running the setup script again
2. Check the [Steam Family Sharing FAQ](https://help.steampowered.com/en/faqs/view/054C-3167-DD7F-49D4)
3. Create an issue on the [GitHub repository](https://github.com/armand0e/TrustyOldLuma/issues)
