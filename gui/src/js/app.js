/**
 * Main application logic for Luna Gaming Tool
 */

// Component instances
let dashboard;
let injector;
let unlocker;
let settings;

document.addEventListener('DOMContentLoaded', async () => {
  // Initialize API connection
  await window.lunaAPI.initialize();
  
  // Log startup
  window.lunaAPI.logActivity('Luna GUI started');
  
  // Initialize components
  initializeComponents();
  
  // Set up IPC listeners
  setupIPCListeners();
  
  // Add script tags for components
  loadComponentScripts();
});

/**
 * Load component scripts
 */
function loadComponentScripts() {
  const componentScripts = [
    'components/dashboard.js',
    'components/injector.js',
    'components/unlocker.js',
    'components/settings.js'
  ];
  
  componentScripts.forEach(src => {
    const script = document.createElement('script');
    script.src = src;
    script.onload = () => {
      console.log(`Loaded component: ${src}`);
      initializeComponentsWhenReady();
    };
    document.body.appendChild(script);
  });
}

/**
 * Initialize components when all scripts are loaded
 */
function initializeComponentsWhenReady() {
  // Check if all component classes are available
  if (
    window.DashboardComponent &&
    window.InjectorComponent &&
    window.UnlockerComponent &&
    window.SettingsComponent &&
    !dashboard // Only initialize once
  ) {
    dashboard = new window.DashboardComponent();
    injector = new window.InjectorComponent();
    unlocker = new window.UnlockerComponent();
    settings = new window.SettingsComponent();
    
    console.log('All components initialized');
  }
}

/**
 * Initialize components
 */
function initializeComponents() {
  // This will be called immediately, but the actual component initialization
  // will happen after the scripts are loaded
  console.log('Setting up component initialization');
}

/**
 * Set up IPC listeners for main process communication
 */
function setupIPCListeners() {
  // Listen for start injector command from main process
  window.electron.ipc.on('start-injector', async () => {
    if (injector) {
      const config = injector.getConfig();
      await window.lunaAPI.startInjector(config);
    }
  });
  
  // Listen for start unlocker command from main process
  window.electron.ipc.on('start-unlocker', async () => {
    if (unlocker) {
      const config = unlocker.getConfig();
      await window.lunaAPI.startUnlocker(config);
    }
  });
  
  // Listen for status updates
  window.electron.ipc.on('status-update', (data) => {
    window.lunaAPI.handleStatusUpdate(data);
    
    // Update component status
    if (dashboard) dashboard.updateStatus();
    if (injector) injector.updateStatus(data.injector_status);
    if (unlocker) unlocker.updateStatus(data.unlocker_status);
  });
}