/**
 * API communication for Luna Gaming Tool
 */

class LunaAPI {
  constructor() {
    this.connected = false;
    this.socket = null;
    this.activityLog = [];
    this.statusUpdateInterval = null;
  }
  
  /**
   * Initialize API connection
   * @param {number} port - API port number
   * @returns {Promise<boolean>} - Connection success
   */
  async initialize(port = 5000) {
    try {
      // Connect to Luna API
      const result = await window.electron.lunaAPI.connect(port);
      
      if (result.success) {
        this.connected = true;
        this.logActivity('Connected to Luna API');
        
        // Set up WebSocket for real-time updates
        this.setupWebSocket(port);
        
        // Start status polling
        this.startStatusPolling();
        
        // Update UI
        this.updateConnectionStatus(true);
        
        return true;
      } else {
        this.logActivity(`Failed to connect to Luna API: ${result.message}`);
        this.updateConnectionStatus(false);
        return false;
      }
    } catch (error) {
      this.logActivity(`API connection error: ${error.message}`);
      this.updateConnectionStatus(false);
      return false;
    }
  }
  
  /**
   * Set up WebSocket connection for real-time updates
   * @param {number} port - WebSocket port
   */
  setupWebSocket(port) {
    this.socket = window.electron.lunaAPI.connectWebSocket(port);
    
    if (this.socket) {
      // Listen for status updates
      this.socket.on('status_update', (data) => {
        this.handleStatusUpdate(data);
      });
      
      // Listen for injector events
      this.socket.on('injector_event', (data) => {
        this.logActivity(`Injector: ${data.message}`);
        this.updateInjectorStatus(data.status);
      });
      
      // Listen for unlocker events
      this.socket.on('unlocker_event', (data) => {
        this.logActivity(`Unlocker: ${data.message}`);
        this.updateUnlockerStatus(data.status);
      });
      
      // Listen for error events
      this.socket.on('error_event', (data) => {
        this.logActivity(`Error: ${data.message}`, 'error');
        showToast('Error', data.message, 'error');
      });
    }
  }
  
  /**
   * Start polling for status updates
   */
  startStatusPolling() {
    // Clear any existing interval
    if (this.statusUpdateInterval) {
      clearInterval(this.statusUpdateInterval);
    }
    
    // Poll every 5 seconds
    this.statusUpdateInterval = setInterval(async () => {
      if (this.connected) {
        try {
          const status = await window.electron.lunaAPI.system.getStatus();
          this.handleStatusUpdate(status);
        } catch (error) {
          console.error('Status polling error:', error);
        }
      }
    }, 5000);
  }
  
  /**
   * Handle status update from API
   * @param {Object} data - Status data
   */
  handleStatusUpdate(data) {
    if (data) {
      // Update connection status
      this.updateConnectionStatus(data.api_connected);
      
      // Update component statuses
      this.updateInjectorStatus(data.injector_status);
      this.updateUnlockerStatus(data.unlocker_status);
    }
  }
  
  /**
   * Update API connection status in UI
   * @param {boolean} connected - Whether API is connected
   */
  updateConnectionStatus(connected) {
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');
    const apiStatus = document.getElementById('api-status');
    
    if (connected) {
      statusDot.classList.remove('offline');
      statusDot.classList.add('online');
      statusText.textContent = 'Online';
      apiStatus.textContent = 'Connected';
      apiStatus.classList.add('connected');
    } else {
      statusDot.classList.remove('online');
      statusDot.classList.add('offline');
      statusText.textContent = 'Offline';
      apiStatus.textContent = 'Disconnected';
      apiStatus.classList.remove('connected');
    }
  }
  
  /**
   * Update injector status in UI
   * @param {string} status - Injector status
   */
  updateInjectorStatus(status) {
    const injectorStatus = document.getElementById('injector-status');
    
    if (injectorStatus) {
      injectorStatus.textContent = status || 'Unknown';
      
      // Update class based on status
      injectorStatus.className = 'value';
      if (status === 'Active' || status === 'Running') {
        injectorStatus.classList.add('active');
      } else if (status === 'Error') {
        injectorStatus.classList.add('error');
      }
    }
  }
  
  /**
   * Update unlocker status in UI
   * @param {string} status - Unlocker status
   */
  updateUnlockerStatus(status) {
    const unlockerStatus = document.getElementById('unlocker-status');
    
    if (unlockerStatus) {
      unlockerStatus.textContent = status || 'Unknown';
      
      // Update class based on status
      unlockerStatus.className = 'value';
      if (status === 'Active' || status === 'Running') {
        unlockerStatus.classList.add('active');
      } else if (status === 'Error') {
        unlockerStatus.classList.add('error');
      }
    }
  }
  
  /**
   * Log activity to activity list
   * @param {string} message - Activity message
   * @param {string} type - Activity type (info, error, warning)
   */
  logActivity(message, type = 'info') {
    const timestamp = new Date();
    const activity = {
      message,
      type,
      timestamp
    };
    
    // Add to activity log
    this.activityLog.unshift(activity);
    
    // Keep log size reasonable
    if (this.activityLog.length > 100) {
      this.activityLog.pop();
    }
    
    // Update UI
    this.updateActivityList();
  }
  
  /**
   * Update activity list in UI
   */
  updateActivityList() {
    const activityList = document.getElementById('activity-list');
    
    if (activityList) {
      // Clear current list
      activityList.innerHTML = '';
      
      // Add activities
      this.activityLog.forEach(activity => {
        const li = document.createElement('li');
        li.className = `activity-item ${activity.type}`;
        
        const time = document.createElement('span');
        time.className = 'activity-time';
        time.textContent = this.formatTimestamp(activity.timestamp);
        
        const message = document.createElement('span');
        message.className = 'activity-message';
        message.textContent = activity.message;
        
        li.appendChild(time);
        li.appendChild(message);
        activityList.appendChild(li);
      });
    }
  }
  
  /**
   * Format timestamp for display
   * @param {Date} timestamp - Timestamp to format
   * @returns {string} - Formatted timestamp
   */
  formatTimestamp(timestamp) {
    const now = new Date();
    const diff = now - timestamp;
    
    // Less than a minute
    if (diff < 60000) {
      return 'Just now';
    }
    
    // Less than an hour
    if (diff < 3600000) {
      const minutes = Math.floor(diff / 60000);
      return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
    }
    
    // Less than a day
    if (diff < 86400000) {
      const hours = Math.floor(diff / 3600000);
      return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
    }
    
    // Format date
    return timestamp.toLocaleString();
  }
  
  /**
   * Start the injector
   * @param {Object} config - Injector configuration
   * @returns {Promise<Object>} - Operation result
   */
  async startInjector(config) {
    try {
      const result = await window.electron.lunaAPI.operations.startInjector(config);
      
      if (result.success) {
        this.logActivity('Injector started successfully');
        showToast('Success', 'Injector started successfully', 'success');
      } else {
        this.logActivity(`Failed to start injector: ${result.message}`, 'error');
        showToast('Error', `Failed to start injector: ${result.message}`, 'error');
      }
      
      return result;
    } catch (error) {
      this.logActivity(`Injector error: ${error.message}`, 'error');
      showToast('Error', `Injector error: ${error.message}`, 'error');
      return { success: false, message: error.message };
    }
  }
  
  /**
   * Start the unlocker
   * @param {Object} config - Unlocker configuration
   * @returns {Promise<Object>} - Operation result
   */
  async startUnlocker(config) {
    try {
      const result = await window.electron.lunaAPI.operations.startUnlocker(config);
      
      if (result.success) {
        this.logActivity('Unlocker started successfully');
        showToast('Success', 'Unlocker started successfully', 'success');
      } else {
        this.logActivity(`Failed to start unlocker: ${result.message}`, 'error');
        showToast('Error', `Failed to start unlocker: ${result.message}`, 'error');
      }
      
      return result;
    } catch (error) {
      this.logActivity(`Unlocker error: ${error.message}`, 'error');
      showToast('Error', `Unlocker error: ${error.message}`, 'error');
      return { success: false, message: error.message };
    }
  }
  
  /**
   * Get configuration from API
   * @returns {Promise<Object>} - Configuration object
   */
  async getConfig() {
    try {
      return await window.electron.lunaAPI.config.getConfig();
    } catch (error) {
      this.logActivity(`Failed to get configuration: ${error.message}`, 'error');
      return null;
    }
  }
  
  /**
   * Update configuration
   * @param {Object} config - Configuration object
   * @returns {Promise<Object>} - Operation result
   */
  async updateConfig(config) {
    try {
      const result = await window.electron.lunaAPI.config.updateConfig(config);
      
      if (result.success) {
        this.logActivity('Configuration updated successfully');
        showToast('Success', 'Configuration updated successfully', 'success');
      } else {
        this.logActivity(`Failed to update configuration: ${result.message}`, 'error');
        showToast('Error', `Failed to update configuration: ${result.message}`, 'error');
      }
      
      return result;
    } catch (error) {
      this.logActivity(`Configuration error: ${error.message}`, 'error');
      showToast('Error', `Configuration error: ${error.message}`, 'error');
      return { success: false, message: error.message };
    }
  }
  
  /**
   * Create desktop shortcuts
   * @returns {Promise<Object>} - Operation result
   */
  async createShortcuts() {
    try {
      const result = await window.electron.lunaAPI.system.createShortcuts();
      
      if (result.success) {
        this.logActivity('Shortcuts created successfully');
        showToast('Success', 'Shortcuts created successfully', 'success');
      } else {
        this.logActivity(`Failed to create shortcuts: ${result.message}`, 'error');
        showToast('Error', `Failed to create shortcuts: ${result.message}`, 'error');
      }
      
      return result;
    } catch (error) {
      this.logActivity(`Shortcut error: ${error.message}`, 'error');
      showToast('Error', `Shortcut error: ${error.message}`, 'error');
      return { success: false, message: error.message };
    }
  }
  
  /**
   * Set up security exclusions
   * @returns {Promise<Object>} - Operation result
   */
  async setupSecurityExclusions() {
    try {
      const result = await window.electron.lunaAPI.system.setupSecurityExclusions();
      
      if (result.success) {
        this.logActivity('Security exclusions set up successfully');
        showToast('Success', 'Security exclusions set up successfully', 'success');
      } else {
        this.logActivity(`Failed to set up security exclusions: ${result.message}`, 'error');
        showToast('Error', `Failed to set up security exclusions: ${result.message}`, 'error');
      }
      
      return result;
    } catch (error) {
      this.logActivity(`Security error: ${error.message}`, 'error');
      showToast('Error', `Security error: ${error.message}`, 'error');
      return { success: false, message: error.message };
    }
  }
  
  /**
   * Migrate legacy configurations
   * @returns {Promise<Object>} - Operation result
   */
  async migrateConfig() {
    try {
      const result = await window.electron.lunaAPI.config.migrateConfig();
      
      if (result.success) {
        this.logActivity('Legacy configurations migrated successfully');
        showToast('Success', 'Legacy configurations migrated successfully', 'success');
      } else {
        this.logActivity(`Failed to migrate configurations: ${result.message}`, 'error');
        showToast('Error', `Failed to migrate configurations: ${result.message}`, 'error');
      }
      
      return result;
    } catch (error) {
      this.logActivity(`Migration error: ${error.message}`, 'error');
      showToast('Error', `Migration error: ${error.message}`, 'error');
      return { success: false, message: error.message };
    }
  }
}

/**
 * Show toast notification
 * @param {string} title - Toast title
 * @param {string} message - Toast message
 * @param {string} type - Toast type (success, error, info, warning)
 * @param {number} duration - Duration in milliseconds
 */
function showToast(title, message, type = 'info', duration = 5000) {
  const container = document.getElementById('toast-container');
  
  // Create toast element
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  
  // Create icon based on type
  let icon = 'info';
  if (type === 'success') icon = 'check_circle';
  if (type === 'error') icon = 'error';
  if (type === 'warning') icon = 'warning';
  
  // Create toast content
  toast.innerHTML = `
    <span class="material-icons">${icon}</span>
    <div class="toast-content">
      <div class="toast-title">${title}</div>
      <div class="toast-message">${message}</div>
    </div>
    <span class="material-icons toast-close">close</span>
  `;
  
  // Add to container
  container.appendChild(toast);
  
  // Add close handler
  const closeBtn = toast.querySelector('.toast-close');
  closeBtn.addEventListener('click', () => {
    container.removeChild(toast);
  });
  
  // Auto-remove after duration
  setTimeout(() => {
    if (container.contains(toast)) {
      container.removeChild(toast);
    }
  }, duration);
}

// Create global API instance
window.lunaAPI = new LunaAPI();