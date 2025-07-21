/**
 * Dashboard Component for Luna Gaming Tool
 * 
 * This component displays the main dashboard with system status,
 * quick actions, and recent activity.
 */

class DashboardComponent {
  constructor() {
    this.statusCard = document.querySelector('.status-card .card-content');
    this.activityList = document.getElementById('activity-list');
    this.apiStatus = document.getElementById('api-status');
    this.injectorStatus = document.getElementById('injector-status');
    this.unlockerStatus = document.getElementById('unlocker-status');
    
    // Quick action buttons
    this.startInjectorBtn = document.getElementById('start-injector-btn');
    this.startUnlockerBtn = document.getElementById('start-unlocker-btn');
    this.createShortcutsBtn = document.getElementById('create-shortcuts-btn');
    
    this.initialize();
  }
  
  initialize() {
    // Set up event listeners
    this.startInjectorBtn.addEventListener('click', this.handleStartInjector.bind(this));
    this.startUnlockerBtn.addEventListener('click', this.handleStartUnlocker.bind(this));
    this.createShortcutsBtn.addEventListener('click', this.handleCreateShortcuts.bind(this));
    
    // Update status initially
    this.updateStatus();
  }
  
  updateStatus() {
    // This will be called by the main app when status changes
    const status = {
      api: this.apiStatus.textContent,
      injector: this.injectorStatus.textContent,
      unlocker: this.unlockerStatus.textContent
    };
    
    // Update button states based on status
    this.startInjectorBtn.disabled = status.api === 'Disconnected';
    this.startUnlockerBtn.disabled = status.api === 'Disconnected';
    this.createShortcutsBtn.disabled = status.api === 'Disconnected';
    
    // Update button text based on status
    if (status.injector === 'Active' || status.injector === 'Running') {
      this.startInjectorBtn.innerHTML = '<span class="material-icons">stop</span>Stop Injector';
      this.startInjectorBtn.classList.add('danger');
      this.startInjectorBtn.classList.remove('primary');
    } else {
      this.startInjectorBtn.innerHTML = '<span class="material-icons">play_arrow</span>Start Injector';
      this.startInjectorBtn.classList.add('primary');
      this.startInjectorBtn.classList.remove('danger');
    }
    
    if (status.unlocker === 'Active' || status.unlocker === 'Running') {
      this.startUnlockerBtn.innerHTML = '<span class="material-icons">stop</span>Stop Unlocker';
      this.startUnlockerBtn.classList.add('danger');
      this.startUnlockerBtn.classList.remove('primary');
    } else {
      this.startUnlockerBtn.innerHTML = '<span class="material-icons">play_arrow</span>Start Unlocker';
      this.startUnlockerBtn.classList.add('primary');
      this.startUnlockerBtn.classList.remove('danger');
    }
  }
  
  async handleStartInjector() {
    const injectorStatus = this.injectorStatus.textContent;
    
    if (injectorStatus === 'Active' || injectorStatus === 'Running') {
      // Stop injector
      await window.lunaAPI.operations.stopInjector();
    } else {
      // Start injector
      const config = this.getInjectorConfig();
      await window.lunaAPI.operations.startInjector(config);
    }
  }
  
  async handleStartUnlocker() {
    const unlockerStatus = this.unlockerStatus.textContent;
    
    if (unlockerStatus === 'Active' || unlockerStatus === 'Running') {
      // Stop unlocker
      await window.lunaAPI.operations.stopUnlocker();
    } else {
      // Start unlocker
      const config = this.getUnlockerConfig();
      await window.lunaAPI.operations.startUnlocker(config);
    }
  }
  
  async handleCreateShortcuts() {
    await window.lunaAPI.createShortcuts();
  }
  
  getInjectorConfig() {
    // Get injector configuration from settings
    // This is a simplified version - in a real app, we would get this from a settings store
    return {
      injector_enabled: true,
      auto_inject: false,
      app_list: []
    };
  }
  
  getUnlockerConfig() {
    // Get unlocker configuration from settings
    // This is a simplified version - in a real app, we would get this from a settings store
    return {
      unlocker_enabled: true,
      unlock_dlc: true,
      unlock_shared: false,
      platforms: {
        steam: { enabled: true },
        epic: { enabled: false },
        origin: { enabled: false },
        uplay: { enabled: false }
      }
    };
  }
}

// Export the component
window.DashboardComponent = DashboardComponent;