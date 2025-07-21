/**
 * Injector Component for Luna Gaming Tool
 * 
 * This component manages the injector configuration and operations.
 */

class InjectorComponent {
  constructor() {
    this.form = document.getElementById('injector-form');
    this.enabledCheckbox = document.getElementById('injector-enabled');
    this.autoInjectCheckbox = document.getElementById('auto-inject');
    this.appListTextarea = document.getElementById('app-list');
    this.saveConfigBtn = document.getElementById('save-injector-config');
    this.runInjectorBtn = document.getElementById('run-injector');
    
    this.initialize();
  }
  
  initialize() {
    // Set up event listeners
    this.saveConfigBtn.addEventListener('click', this.handleSaveConfig.bind(this));
    this.runInjectorBtn.addEventListener('click', this.handleRunInjector.bind(this));
    
    // Load configuration
    this.loadConfig();
  }
  
  async loadConfig() {
    try {
      const config = await window.lunaAPI.getConfig();
      
      if (config) {
        this.enabledCheckbox.checked = config.injector_enabled;
        this.autoInjectCheckbox.checked = config.auto_inject;
        
        if (config.app_list && Array.isArray(config.app_list)) {
          this.appListTextarea.value = config.app_list.join('\n');
        }
      }
    } catch (error) {
      console.error('Error loading injector configuration:', error);
      showToast('Error', 'Failed to load injector configuration', 'error');
    }
  }
  
  getConfig() {
    const appListText = this.appListTextarea.value;
    const appList = appListText
      .split('\n')
      .map(line => line.trim())
      .filter(line => line.length > 0);
    
    return {
      injector_enabled: this.enabledCheckbox.checked,
      auto_inject: this.autoInjectCheckbox.checked,
      app_list: appList
    };
  }
  
  async handleSaveConfig() {
    try {
      const config = this.getConfig();
      await window.lunaAPI.updateConfig(config);
      showToast('Success', 'Injector configuration saved', 'success');
    } catch (error) {
      console.error('Error saving injector configuration:', error);
      showToast('Error', 'Failed to save injector configuration', 'error');
    }
  }
  
  async handleRunInjector() {
    try {
      const config = this.getConfig();
      
      // Save configuration first
      await window.lunaAPI.updateConfig(config);
      
      // Start injector
      await window.lunaAPI.startInjector(config);
    } catch (error) {
      console.error('Error running injector:', error);
      showToast('Error', 'Failed to run injector', 'error');
    }
  }
  
  updateStatus(status) {
    // Update button state based on injector status
    if (status === 'Active' || status === 'Running') {
      this.runInjectorBtn.innerHTML = '<span class="material-icons">stop</span>Stop Injector';
      this.runInjectorBtn.classList.add('danger');
      this.runInjectorBtn.classList.remove('primary');
    } else {
      this.runInjectorBtn.innerHTML = '<span class="material-icons">play_arrow</span>Run Injector';
      this.runInjectorBtn.classList.add('primary');
      this.runInjectorBtn.classList.remove('danger');
    }
  }
}

// Export the component
window.InjectorComponent = InjectorComponent;