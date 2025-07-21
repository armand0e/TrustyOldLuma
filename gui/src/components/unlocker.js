/**
 * Unlocker Component for Luna Gaming Tool
 * 
 * This component manages the unlocker configuration and operations.
 */

class UnlockerComponent {
  constructor() {
    this.form = document.getElementById('unlocker-form');
    this.enabledCheckbox = document.getElementById('unlocker-enabled');
    this.unlockDlcCheckbox = document.getElementById('unlock-dlc');
    this.unlockSharedCheckbox = document.getElementById('unlock-shared');
    this.platformSteamCheckbox = document.getElementById('platform-steam');
    this.platformEpicCheckbox = document.getElementById('platform-epic');
    this.platformOriginCheckbox = document.getElementById('platform-origin');
    this.platformUplayCheckbox = document.getElementById('platform-uplay');
    this.saveConfigBtn = document.getElementById('save-unlocker-config');
    this.runUnlockerBtn = document.getElementById('run-unlocker');
    
    this.initialize();
  }
  
  initialize() {
    // Set up event listeners
    this.saveConfigBtn.addEventListener('click', this.handleSaveConfig.bind(this));
    this.runUnlockerBtn.addEventListener('click', this.handleRunUnlocker.bind(this));
    
    // Load configuration
    this.loadConfig();
  }
  
  async loadConfig() {
    try {
      const config = await window.lunaAPI.getConfig();
      
      if (config) {
        this.enabledCheckbox.checked = config.unlocker_enabled;
        this.unlockDlcCheckbox.checked = config.unlock_dlc;
        this.unlockSharedCheckbox.checked = config.unlock_shared;
        
        if (config.platforms) {
          this.platformSteamCheckbox.checked = config.platforms.steam?.enabled || false;
          this.platformEpicCheckbox.checked = config.platforms.epic?.enabled || false;
          this.platformOriginCheckbox.checked = config.platforms.origin?.enabled || false;
          this.platformUplayCheckbox.checked = config.platforms.uplay?.enabled || false;
        }
      }
    } catch (error) {
      console.error('Error loading unlocker configuration:', error);
      showToast('Error', 'Failed to load unlocker configuration', 'error');
    }
  }
  
  getConfig() {
    return {
      unlocker_enabled: this.enabledCheckbox.checked,
      unlock_dlc: this.unlockDlcCheckbox.checked,
      unlock_shared: this.unlockSharedCheckbox.checked,
      platforms: {
        steam: {
          enabled: this.platformSteamCheckbox.checked
        },
        epic: {
          enabled: this.platformEpicCheckbox.checked
        },
        origin: {
          enabled: this.platformOriginCheckbox.checked
        },
        uplay: {
          enabled: this.platformUplayCheckbox.checked
        }
      }
    };
  }
  
  async handleSaveConfig() {
    try {
      const config = this.getConfig();
      await window.lunaAPI.updateConfig(config);
      showToast('Success', 'Unlocker configuration saved', 'success');
    } catch (error) {
      console.error('Error saving unlocker configuration:', error);
      showToast('Error', 'Failed to save unlocker configuration', 'error');
    }
  }
  
  async handleRunUnlocker() {
    try {
      const config = this.getConfig();
      
      // Save configuration first
      await window.lunaAPI.updateConfig(config);
      
      // Start unlocker
      await window.lunaAPI.startUnlocker(config);
    } catch (error) {
      console.error('Error running unlocker:', error);
      showToast('Error', 'Failed to run unlocker', 'error');
    }
  }
  
  updateStatus(status) {
    // Update button state based on unlocker status
    if (status === 'Active' || status === 'Running') {
      this.runUnlockerBtn.innerHTML = '<span class="material-icons">stop</span>Stop Unlocker';
      this.runUnlockerBtn.classList.add('danger');
      this.runUnlockerBtn.classList.remove('primary');
    } else {
      this.runUnlockerBtn.innerHTML = '<span class="material-icons">play_arrow</span>Run Unlocker';
      this.runUnlockerBtn.classList.add('primary');
      this.runUnlockerBtn.classList.remove('danger');
    }
  }
}

// Export the component
window.UnlockerComponent = UnlockerComponent;