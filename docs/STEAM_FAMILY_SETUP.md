# 🏠 Steam Family Setup with Luna Gaming Tool

This guide explains how to set up Steam Family Sharing to work optimally with Luna Gaming Tool. Luna enhances Steam Family Sharing by providing unified game injection and DLC unlocking capabilities.

## Overview

Luna Gaming Tool works seamlessly with Steam Family Sharing to provide:

- Enhanced game library access for family members
- Automatic DLC unlocking for shared games
- Unified injection system for better compatibility
- Streamlined setup and management

## Setting Up Steam Family

### Step 1: Create or Join a Steam Family

1. **Access Family Management**

   - Go to your Steam Account Details on the Store page
   - Click on the "Family Management" section
   - Or visit: [Steam Family Management](https://help.steampowered.com/en/faqs/view/054C-3167-DD7F-49D4)

2. **Create a Family**

   - Click "Create a Family" (or use your existing family)
   - Set up family name and basic settings

3. **Invite Family Members**
   - Invite the account that you wish to share your games with
   - The invited account will receive an alert in their Steam mobile app
   - They can accept the invite through the mobile app or Steam client

### Step 2: Configure Family Sharing Settings

1. **Enable Library Sharing**

   - Go to Steam Settings → Family
   - Enable "Authorize Library Sharing on this computer"
   - Select which family members can access your library

2. **Set Sharing Preferences**
   - Choose which games to share (or share entire library)
   - Configure parental controls if needed
   - Set up purchase authorization settings

## Luna Integration with Steam Family

### Automatic Configuration

Luna automatically detects and configures Steam Family Sharing:

1. **Family Detection**

   - Luna scans for existing Steam Family configurations
   - Identifies shared libraries and family members
   - Configures injection settings for optimal compatibility

2. **Enhanced Sharing**
   - Luna provides DLC unlocking for shared games
   - Automatic injection for family member sessions
   - Improved compatibility with family sharing restrictions

### Manual Luna Configuration

If automatic configuration doesn't work:

1. **Configure Luna for Family Sharing**

   ```json
   {
     "luna": {
       "platforms": {
         "steam": {
           "family_sharing": {
             "enabled": true,
             "auto_detect_family": true,
             "unlock_shared_dlc": true,
             "inject_shared_games": true
           }
         }
       }
     }
   }
   ```

2. **Add Family Member Games**
   - Use Luna's game management interface
   - Add App IDs for games you want to access from family members
   - Configure per-game injection settings

## Troubleshooting Family Sharing Issues

### Common Problems and Solutions

1. **Can't Join Family**

   - **Issue**: Steam restricts family sharing to actual family members
   - **Solution**: Log into both accounts on the same computer to establish "household" connection
   - **Luna Enhancement**: Luna can help bypass some restrictions through advanced injection

2. **Games Not Showing in Shared Library**

   - **Issue**: Games not appearing in family member's library
   - **Solution**:
     - Verify library sharing is enabled
     - Check game sharing permissions
     - Restart Steam clients
   - **Luna Solution**: Use Luna's game detection to manually add shared games

3. **DLC Not Available in Shared Games**

   - **Issue**: DLC doesn't transfer with shared games
   - **Solution**: Luna's DLC unlocking automatically handles this
   - **Configuration**: Ensure Luna's unlocker is enabled for shared games

4. **Injection Conflicts with Family Sharing**
   - **Issue**: Game injection interferes with family sharing
   - **Solution**: Luna's smart injection system avoids conflicts
   - **Configuration**: Use Luna's family sharing mode

### Advanced Troubleshooting

1. **Multiple Account Login Method**

   **For Account Owner:**

   - Log into your Steam account on the shared computer
   - Enable "Remember my login"
   - Authorize the computer for family sharing

   **For Family Member:**

   - Log into their Steam account on the same computer
   - Accept family sharing authorization
   - Switch back to owner account when needed

2. **QR Code Login (Mobile App)**

   - Use Steam mobile app for quick account switching
   - Generate QR codes for easy login
   - Maintain authorization across sessions

3. **Luna-Specific Solutions**

   ```batch
   # Test family sharing configuration
   python luna.py --test-family-sharing

   # Repair family sharing settings
   python luna.py --repair-family-sharing

   # Configure family sharing manually
   python luna.py --setup-family-sharing
   ```

## Best Practices for Luna + Steam Family

### Optimal Configuration

1. **Account Management**

   - Keep the game owner account logged in
   - Use family member accounts for actual gameplay
   - Maintain proper authorization on shared computers

2. **Luna Settings**

   - Enable family sharing mode in Luna configuration
   - Configure automatic DLC unlocking for shared games
   - Use Luna's smart injection to avoid conflicts

3. **Game Management**
   - Add frequently played shared games to Luna's AppList
   - Configure per-game injection settings
   - Use Luna's monitoring to track shared game usage

### Security Considerations

1. **Account Security**

   - Use strong passwords for all accounts
   - Enable Steam Guard on all family accounts
   - Regularly review family sharing permissions

2. **Luna Security**
   - Keep Luna updated to latest version
   - Use Luna's stealth mode for enhanced privacy
   - Configure Windows Defender exclusions properly

## Luna Commands for Family Sharing

### Useful Luna Commands

```batch
# Check family sharing status
python luna.py --family-status

# List shared games
python luna.py --list-shared-games

# Configure family sharing
python luna.py --setup-family-sharing --interactive

# Test shared game injection
python luna.py --test-injection --game-id <APP_ID> --family-mode

# Monitor family sharing activity
python luna.py --monitor --family-sharing

# Repair family sharing configuration
python luna.py --repair-family-sharing --verbose
```

### Configuration Examples

**Basic Family Sharing Configuration:**

```json
{
  "steam": {
    "family_sharing": {
      "enabled": true,
      "owner_account": "primary_account",
      "shared_accounts": ["family_member_1", "family_member_2"],
      "auto_inject_shared": true,
      "unlock_shared_dlc": true
    }
  }
}
```

**Advanced Family Sharing Configuration:**

```json
{
  "steam": {
    "family_sharing": {
      "enabled": true,
      "detection_mode": "automatic",
      "injection_priority": "family_first",
      "dlc_unlocking": {
        "shared_games": true,
        "owned_games": true,
        "family_dlc": true
      },
      "monitoring": {
        "track_usage": true,
        "log_sessions": true,
        "alert_conflicts": true
      }
    }
  }
}
```

## Additional Resources

- [Official Steam Family Sharing Guide](https://help.steampowered.com/en/faqs/view/054C-3167-DD7F-49D4)
- [Luna Gaming Tool Documentation](README.md)
- [Luna Migration Guide](MIGRATION_GUIDE.md)
- [Luna Setup Guide](LUNA_SETUP.md)

## Support

If you encounter issues with Steam Family Sharing and Luna:

1. Check Luna logs for family sharing errors
2. Verify Steam Family configuration
3. Test with Luna's diagnostic tools
4. Report issues on the Luna GitHub repository

For Steam-specific family sharing issues, consult the official Steam support documentation.
