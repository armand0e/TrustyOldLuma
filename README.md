# SETUP INSTRUCTIONS
## Setup Steam Family Sharing
1. Open the steam launcher, and have whoever is sharing their game with you login to their steam account on your computer
> Keep in mind, the steam account must stay logged in on at all times for family sharing to work
2. Once logged into their steam account, open Steam settings 
> Click the Steam icon in the upper left corner of the steam launcher, select Settings*
3. Navigate to the "Family" tab, and enable `Authorize Library Sharing on this device` and enable the account(s) you want to share to
## Windows Security
1. Press the windows key and type `security` to open Windows Security
2. Navigate to `Virus & threat protection` then select `Manage settings` 
> Underneath the "Virus & threat protection settings" subcategory
3. Scroll all the way to the bottom and select `Add or remove exclusions` 
> Underneath the "Exclusions" subcategory
4. Select `Add an exclusion->Folder` 
5. In the pop-up, head to your Documents library and create a new Folder named GreenLuma, select the "GreenLuma" folder you just created, and click `Select Folder`
> To create a new folder right click in the empty space, select New->Folder
## GreenLuma Setup
1. Download [2020.zip](https://github.com/armand0e/TrustyOldLuma/releases/latest)
2. Open the zip and **Extract all in the `Documents->GreenLuma` folder you just created**
> **At this point your GreenLuma folder should contain:**
> - A folder named `AppList`
> - `DLLInjector.exe`
> - `DLLInjector.ini`
> - `GreenLuma_2020_x**.dll` 
> - `GreenLumaSettings_2023.exe`
> 
> *I recommend keeping this folder open in the File explorer for ease of access*
### Copy & Set Paths
**To copy the path of a file: right click the file and select "Copy as path", or select the file and use the keyboard shortcut `Ctrl+Shift+C`**

3. Open a new file explorer window/tab, navigate to your Steam folder, and copy the path of `steam.exe`
> Default: `C:\Program Files (x86)\Steam`
4. Navigate back to the GreenLuma folder in your original file explorer window/tab, and copy the path of `GreenLuma_2020_x86.dll` 
5. Run `GreenLumaSettings_2023.exe`
6. Enter "2" into the terminal 
7. Use the keyboard shortcut `Win+v` to access clipboard history, and paste/enter the paths to `steam.exe` and `GreenLuma_2020_x86.dll` in the order they're prompted for
8. Close `GreenLumaSettings_2023.exe`
### Backup Original Steam Bin
In rare cases, the dll injector could fail to inject properly, and cause your steam launcher bin to corrupt. It could prove useful to save a backup somewhere of the `bin` folder *located in your Steam folder*
## Config
Now comes the real magic of GreenLuma. Normally we aren't able to play games from another account's library while that account is in a game. However, if we were to give GreenLuma the Steam AppID of that game, it can run a script when launching steam to spoof ownership of that game, letting us play a family shared game completely independent of the host account. No need to worry about getting banned either! The best part about GreenLuma is that it's all done locally, which makes it virtually impossible to detect.
1. Find and copy the Steam AppID for the game you want to spoof ownership of 
> Steam AppIDs can be easily found on [SteamDB](https://steamdb.info/)
2. Navigate into `GreenLuma->AppList` 
> - **If adding only 1 game**, open `0.txt` and replace the numbers on the first line with the AppID from your clipboard
> - Otherwise, create a new text file named `1.txt` and paste the AppID into the first line 
> 
> *When adding multiple AppIDs, each ID needs it's own text file (i.e. `0.txt`, `1.txt`, `2.txt`, `3.txt`, etc.)*

## Koalageddon
[Download and set up Koalageddon v1.5.4](https://github.com/acidicoala/Koalageddon/releases/download/v1.5.4/KoalageddonInstaller.exe)
Open the koalageddon app, click on "open config directory" at the bottom
Open the config file and set all the 'false' values at the top to 'true', then save and exit the file
Click install platform integrations for steam, then you're all set!

## Usage
1. Make sure steam is completely closed 
> Open system tray, right click steam icon, select "exit steam"
2. Launch `DLLInjector.exe` from your GreenLuma folder 
> For ease of access make a desktop shortcut or pin to start
