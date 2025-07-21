const { app, BrowserWindow, ipcMain, Menu, Tray } = require('electron');
const path = require('path');
const log = require('electron-log');
const Store = require('electron-store');

// Configure logging
log.transports.file.level = 'info';
log.info('Luna Gaming Tool starting up...');

// Initialize configuration store
const store = new Store({
  name: 'luna-config',
  defaults: {
    windowBounds: { width: 1000, height: 700 },
    isDarkMode: true,
    autoStart: false
  }
});

// Keep a global reference of the window object to avoid garbage collection
let mainWindow;
let tray = null;

function createWindow() {
  const windowBounds = store.get('windowBounds');
  
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: windowBounds.width,
    height: windowBounds.height,
    minWidth: 800,
    minHeight: 600,
    title: 'Luna Gaming Tool',
    icon: path.join(__dirname, 'assets/icons/luna.png'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js')
    },
    show: false // Don't show until ready-to-show
  });

  // Load the index.html file
  mainWindow.loadFile(path.join(__dirname, 'src/index.html'));

  // Open DevTools in development mode
  if (process.argv.includes('--dev')) {
    mainWindow.webContents.openDevTools();
    log.info('Development mode enabled');
  }

  // Save window size when resized
  mainWindow.on('resize', () => {
    const { width, height } = mainWindow.getBounds();
    store.set('windowBounds', { width, height });
  });

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    log.info('Main window displayed');
  });

  // Handle window close
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Create system tray
  createTray();
}

function createTray() {
  tray = new Tray(path.join(__dirname, 'assets/icons/luna-tray.png'));
  const contextMenu = Menu.buildFromTemplate([
    { label: 'Open Luna', click: () => mainWindow.show() },
    { type: 'separator' },
    { label: 'Start Injector', click: () => mainWindow.webContents.send('start-injector') },
    { label: 'Start Unlocker', click: () => mainWindow.webContents.send('start-unlocker') },
    { type: 'separator' },
    { label: 'Quit', click: () => app.quit() }
  ]);
  
  tray.setToolTip('Luna Gaming Tool');
  tray.setContextMenu(contextMenu);
  
  tray.on('click', () => {
    mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
  });
}

// Create window when Electron is ready
app.whenReady().then(() => {
  createWindow();
  
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

// Quit when all windows are closed, except on macOS
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// IPC handlers for communication with renderer process
ipcMain.handle('get-app-version', () => app.getVersion());
ipcMain.handle('get-app-path', () => app.getPath('userData'));
ipcMain.handle('get-theme', () => store.get('isDarkMode'));
ipcMain.handle('set-theme', (event, isDarkMode) => {
  store.set('isDarkMode', isDarkMode);
  return isDarkMode;
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  log.error('Uncaught exception:', error);
});