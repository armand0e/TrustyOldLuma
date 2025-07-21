const { contextBridge, ipcRenderer } = require('electron');
const axios = require('axios');
const io = require('socket.io-client');

// Default API configuration
const API_BASE_URL = 'http://localhost:5000/api';
let socket = null;

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electron', {
  // App info
  appInfo: {
    getVersion: () => ipcRenderer.invoke('get-app-version'),
    getAppPath: () => ipcRenderer.invoke('get-app-path')
  },
  
  // Theme management
  theme: {
    getDarkMode: () => ipcRenderer.invoke('get-theme'),
    setDarkMode: (isDarkMode) => ipcRenderer.invoke('set-theme', isDarkMode)
  },
  
  // IPC communication
  ipc: {
    on: (channel, callback) => {
      // Whitelist valid channels
      const validChannels = ['start-injector', 'start-unlocker', 'status-update'];
      if (validChannels.includes(channel)) {
        const subscription = (event, ...args) => callback(...args);
        ipcRenderer.on(channel, subscription);
        
        // Return a function to remove the event listener
        return () => {
          ipcRenderer.removeListener(channel, subscription);
        };
      }
    }
  },
  
  // Luna API communication
  lunaAPI: {
    // Connection management
    connect: async (port = 5000) => {
      try {
        // Update base URL if port changes
        const newBaseUrl = `http://localhost:${port}/api`;
        
        // Test connection
        const response = await axios.get(`${newBaseUrl}/status`);
        if (response.status === 200) {
          // Update API base URL on successful connection
          window.electron.lunaAPI.baseUrl = newBaseUrl;
          return { success: true, message: 'Connected to Luna API' };
        }
        return { success: false, message: 'Failed to connect to Luna API' };
      } catch (error) {
        return { 
          success: false, 
          message: `Connection error: ${error.message}`,
          error
        };
      }
    },
    
    // WebSocket connection for real-time updates
    connectWebSocket: (port = 5000) => {
      try {
        if (socket) {
          socket.disconnect();
        }
        
        socket = io(`http://localhost:${port}`);
        
        socket.on('connect', () => {
          console.log('WebSocket connected');
        });
        
        socket.on('disconnect', () => {
          console.log('WebSocket disconnected');
        });
        
        socket.on('error', (error) => {
          console.error('WebSocket error:', error);
        });
        
        return {
          on: (event, callback) => {
            socket.on(event, callback);
          },
          off: (event, callback) => {
            socket.off(event, callback);
          },
          disconnect: () => {
            socket.disconnect();
            socket = null;
          }
        };
      } catch (error) {
        console.error('WebSocket connection error:', error);
        return null;
      }
    },
    
    // Core Luna operations
    operations: {
      // Injector operations
      startInjector: async (config) => {
        try {
          const response = await axios.post(`${API_BASE_URL}/injector/start`, config);
          return response.data;
        } catch (error) {
          handleApiError(error);
        }
      },
      
      stopInjector: async () => {
        try {
          const response = await axios.post(`${API_BASE_URL}/injector/stop`);
          return response.data;
        } catch (error) {
          handleApiError(error);
        }
      },
      
      // Unlocker operations
      startUnlocker: async (config) => {
        try {
          const response = await axios.post(`${API_BASE_URL}/unlocker/start`, config);
          return response.data;
        } catch (error) {
          handleApiError(error);
        }
      },
      
      stopUnlocker: async () => {
        try {
          const response = await axios.post(`${API_BASE_URL}/unlocker/stop`);
          return response.data;
        } catch (error) {
          handleApiError(error);
        }
      }
    },
    
    // Configuration management
    config: {
      getConfig: async () => {
        try {
          const response = await axios.get(`${API_BASE_URL}/config`);
          return response.data;
        } catch (error) {
          handleApiError(error);
        }
      },
      
      updateConfig: async (config) => {
        try {
          const response = await axios.put(`${API_BASE_URL}/config`, config);
          return response.data;
        } catch (error) {
          handleApiError(error);
        }
      },
      
      migrateConfig: async () => {
        try {
          const response = await axios.post(`${API_BASE_URL}/config/migrate`);
          return response.data;
        } catch (error) {
          handleApiError(error);
        }
      }
    },
    
    // System operations
    system: {
      getStatus: async () => {
        try {
          const response = await axios.get(`${API_BASE_URL}/status`);
          return response.data;
        } catch (error) {
          handleApiError(error);
        }
      },
      
      createShortcuts: async () => {
        try {
          const response = await axios.post(`${API_BASE_URL}/system/shortcuts`);
          return response.data;
        } catch (error) {
          handleApiError(error);
        }
      },
      
      setupSecurityExclusions: async () => {
        try {
          const response = await axios.post(`${API_BASE_URL}/system/security`);
          return response.data;
        } catch (error) {
          handleApiError(error);
        }
      }
    }
  }
});

// Helper function to handle API errors
function handleApiError(error) {
  if (error.response) {
    // The request was made and the server responded with a status code
    // that falls out of the range of 2xx
    console.error('API Error Response:', error.response.data);
    return {
      success: false,
      status: error.response.status,
      message: error.response.data.message || 'API error',
      error: error.response.data
    };
  } else if (error.request) {
    // The request was made but no response was received
    console.error('API No Response:', error.request);
    return {
      success: false,
      message: 'No response from Luna API server',
      error: { type: 'no_response' }
    };
  } else {
    // Something happened in setting up the request that triggered an Error
    console.error('API Request Error:', error.message);
    return {
      success: false,
      message: `Request error: ${error.message}`,
      error: { type: 'request_setup', message: error.message }
    };
  }
}