/**
 * Settings Component for Luna Gaming Tool
 * 
 * This component manages the application settings.
 */

class SettingsComponent {
  constructor() {
    this.form = document.getElementById('settings-form');
    this.autoStartCheckbox = document.getElementById('auto-start');
    this.minimizeToTrayCheckbox = document.getElementById('minimize-to-tray');
    this.apiPortInput = document.getElementById('api-port');
    this.saveSettingsBtn = document.getElementById('save-settings');
    this.securityExclusionsBtn = document.getElementById('security-exclusions');
    this.migrateLegacyBtn = document.getElementById('migrate-legacy');
    this.openConfigBtn = document.getElementById('open-config');
    this.appVersionSpan = document.getElementById('app-version');
    
    this.initialize();
  }
  
  async initialize() {
    // Set up event listeners
    this.saveSettingsBtn.addEventListener('click', this.handleSaveSettings.bind(this));
    this.securityExclusionsBtn.addEventListener('click', this.handleSecurityExclusions.bind(this));
    this.migrateLegacyBtn.addEventListener('click', this.handleMigrateLegacy.bind(this));
    this.openConfigBtn.addEventListener('click', this.handleOpenConfig.bind(this));
    
    // Load app version
    try {
      const version = await window.electron.appInfo.getVersion();
      this.appVersionSpan.textContent = version;
    } catch (error) {
      console.error('Failed to get app version:', error);
    }
    
    // Load configuration
    this.loadConfig();
  }
  
  async loadConfig() {
    try {
      const config = await window.lunaAPI.getConfig();
      
      if (config) {
        this.autoStartCheckbox.checked = config.auto_start || false;
        this.minimizeToTrayCheckbox.checked = config.minimize_to_tray !== false;
        
        if (config.api_port) {
          this.apiPortInput.value = config.api_port;
        }
      }
    } catch (error) {
      console.error('Error loading settings:', error);
      showToast('Error', 'Failed to load settings', 'error');
    }
  }
  
  getConfig() {
    return {
      auto_start: this.autoStartCheckbox.checked,
      minimize_to_tray: this.minimizeToTrayCheckbox.checked,
      api_port: parseInt(this.apiPortInput.value, 10)
    };
  }
  
  async handleSaveSettings() {
    try {
      const config = this.getConfig();
      
      // Validate API port
      if (isNaN(config.api_port) || config.api_port < 1024 || config.api_port > 65535) {
        showToast('Error', 'API port must be a number between 1024 and 65535', 'error');
        return;
      }
      
      await window.lunaAPI.updateConfig(config);
      showToast('Success', 'Settings saved', 'success');
      
      // Show restart notice if API port changed
      const currentConfig = await window.lunaAPI.getConfig();
      if (currentConfig.api_port !== config.api_port) {
        showToast('Info', 'API port change will take effect after restart', 'info', 8000);
      }
    } catch (error) {
      console.error('Error saving settings:', error);
      showToast('Error', 'Failed to save settings', 'error');
    }
  }
  
  async handleSecurityExclusions() {
    try {
      await window.lunaAPI.setupSecurityExclusions();
    } catch (error) {
      console.error('Error setting up security exclusions:', error);
      showToast('Error', 'Failed to set up security exclusions', 'error');
    }
  }
  
  async handleMigrateLegacy() {
    try {
      // Show confirmation dialog
      if (confirm('This will migrate legacy GreenLuma and Koalageddon configurations to Luna. Continue?')) {
        await window.lunaAPI.migrateConfig();
      }
    } catch (error) {
      console.error('Error migrating legacy configurations:', error);
      showToast('Error', 'Failed to migrate legacy configurations', 'error');
    }
  }
  
  async handleOpenConfig() {
    try {
      // This would typically use an Electron API to open the config file
      // For now, we'll just show a toast
      showToast('Info', 'This would open the configuration file in your default editor', 'info');
    } catch (error) {
      console.error('Error opening configuration file:', error);
      showToast('Error', 'Failed to open configuration file', 'error');
    }
  }
}

// Export the component
window.SettingsComponent = SettingsComponent;