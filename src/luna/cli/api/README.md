# Luna API Documentation

This document provides information about the Luna API endpoints for GUI-CLI communication.

## Base URL

All API endpoints are relative to the base URL: `http://localhost:5000`

## Authentication

Currently, the API does not require authentication as it is designed for local communication between the GUI and CLI backend.

## API Endpoints

### Status

#### Get API Status

```
GET /api/status
```

Returns the current status of the Luna API.

**Response:**

```json
{
  "api_connected": true,
  "injector_status": "Active",
  "unlocker_status": "Inactive",
  "last_update": "2025-07-20T12:34:56.789Z"
}
```

### Injector

#### Start Injector

```
POST /api/injector/start
```

Start the Luna injector.

**Request Body:**

```json
{
  "injector_enabled": true,
  "auto_inject": false,
  "app_list": ["123456", "789012"]
}
```

**Response:**

```json
{
  "success": true,
  "message": "Injector started successfully"
}
```

#### Stop Injector

```
POST /api/injector/stop
```

Stop the Luna injector.

**Response:**

```json
{
  "success": true,
  "message": "Injector stopped successfully"
}
```

### Unlocker

#### Start Unlocker

```
POST /api/unlocker/start
```

Start the Luna unlocker.

**Request Body:**

```json
{
  "unlocker_enabled": true,
  "unlock_dlc": true,
  "unlock_shared": false,
  "platforms": {
    "steam": {"enabled": true},
    "epic": {"enabled": false},
    "origin": {"enabled": false},
    "uplay": {"enabled": false}
  }
}
```

**Response:**

```json
{
  "success": true,
  "message": "Unlocker started successfully"
}
```

#### Stop Unlocker

```
POST /api/unlocker/stop
```

Stop the Luna unlocker.

**Response:**

```json
{
  "success": true,
  "message": "Unlocker stopped successfully"
}
```

### Configuration

#### Get Configuration

```
GET /api/config
```

Get the Luna configuration.

**Response:**

```json
{
  "injector_enabled": true,
  "auto_inject": false,
  "app_list": ["123456", "789012"],
  "unlocker_enabled": true,
  "unlock_dlc": true,
  "unlock_shared": false,
  "platforms": {
    "steam": {"enabled": true},
    "epic": {"enabled": false},
    "origin": {"enabled": false},
    "uplay": {"enabled": false}
  },
  "auto_start": false,
  "minimize_to_tray": true,
  "api_port": 5000
}
```

#### Update Configuration

```
PUT /api/config
```

Update the Luna configuration.

**Request Body:**

Configuration object with fields to update.

**Response:**

```json
{
  "success": true,
  "message": "Configuration updated successfully"
}
```

#### Migrate Legacy Configurations

```
POST /api/config/migrate
```

Migrate legacy configurations.

**Response:**

```json
{
  "success": true,
  "message": "Legacy configurations migrated successfully"
}
```

#### Get Advanced Configuration

```
GET /api/config/advanced
```

Get advanced configuration options.

**Response:**

```json
{
  "success": true,
  "config": {
    "stealth_mode": true,
    "auto_start": false,
    "minimize_to_tray": true,
    "api_port": 5000,
    "log_level": "INFO"
  }
}
```

#### Update Advanced Configuration

```
PUT /api/config/advanced
```

Update advanced configuration options.

**Request Body:**

```json
{
  "stealth_mode": true,
  "auto_start": false,
  "minimize_to_tray": true,
  "api_port": 5000,
  "log_level": "INFO"
}
```

**Response:**

```json
{
  "success": true,
  "message": "Advanced configuration updated successfully"
}
```

### Apps

#### Get Apps

```
GET /api/apps
```

Get the list of configured apps.

**Response:**

```json
{
  "success": true,
  "apps": [
    {"id": "123456", "name": "Test App 1", "enabled": true},
    {"id": "789012", "name": "Test App 2", "enabled": true}
  ]
}
```

#### Add App

```
POST /api/apps
```

Add an app to the configuration.

**Request Body:**

```json
{
  "app_id": "123456"
}
```

**Response:**

```json
{
  "success": true,
  "message": "App 123456 added successfully"
}
```

#### Remove App

```
DELETE /api/apps/{app_id}
```

Remove an app from the configuration.

**Response:**

```json
{
  "success": true,
  "message": "App 123456 removed successfully"
}
```

### Platforms

#### Get Platforms

```
GET /api/platforms
```

Get the list of configured platforms.

**Response:**

```json
{
  "success": true,
  "platforms": {
    "steam": {"enabled": true, "priority": 1},
    "epic": {"enabled": false, "priority": 2},
    "origin": {"enabled": false, "priority": 3},
    "uplay": {"enabled": false, "priority": 4}
  }
}
```

#### Update Platform

```
PUT /api/platforms/{platform_id}
```

Update a platform configuration.

**Request Body:**

```json
{
  "enabled": true,
  "priority": 1
}
```

**Response:**

```json
{
  "success": true,
  "message": "Platform steam updated successfully"
}
```

### Processes

#### Get Processes

```
GET /api/processes
```

Get the list of running processes.

**Response:**

```json
{
  "success": true,
  "processes": [
    {"pid": 1234, "name": "steam.exe", "username": "user", "memory_mb": 256.5},
    {"pid": 5678, "name": "game.exe", "username": "user", "memory_mb": 1024.2}
  ]
}
```

#### Inject Process

```
POST /api/processes/{pid}/inject
```

Inject into a specific process.

**Response:**

```json
{
  "success": true,
  "message": "Process 1234 injected successfully"
}
```

### System

#### Create Shortcuts

```
POST /api/system/shortcuts
```

Create Luna desktop shortcuts.

**Response:**

```json
{
  "success": true,
  "message": "Shortcuts created successfully"
}
```

#### Setup Security Exclusions

```
POST /api/system/security
```

Set up security exclusions for Luna.

**Response:**

```json
{
  "success": true,
  "message": "Security exclusions set up successfully"
}
```

#### Check System Compatibility

```
GET /api/system/compatibility
```

Check system compatibility for Luna.

**Response:**

```json
{
  "success": true,
  "compatibility": {
    "system": {
      "name": "Windows",
      "release": "10",
      "version": "10.0.19042",
      "architecture": "64bit",
      "processor": "Intel64 Family 6 Model 158 Stepping 10, GenuineIntel"
    },
    "requirements": {
      "windows": {"required": true, "satisfied": true},
      "windows_10": {"required": true, "satisfied": true},
      "64bit": {"required": true, "satisfied": true},
      "admin": {"required": true, "satisfied": true},
      "dotnet": {"required": true, "satisfied": true}
    },
    "is_compatible": true,
    "needs_admin": false
  }
}
```

### Service

#### Get Service Status

```
GET /api/service/status
```

Get Luna service status.

**Response:**

```json
{
  "success": true,
  "service": {
    "running": true,
    "pid": 1234,
    "uptime": 3600,
    "api_port": 5000
  }
}
```

### Logs

#### Get Logs

```
GET /api/logs
```

Get Luna logs.

**Response:**

```json
{
  "success": true,
  "logs": [
    "2025-07-20 12:34:56 - luna.cli - INFO - Luna CLI started on port 5000",
    "2025-07-20 12:35:00 - luna.api - INFO - Client connected: abc123"
  ]
}
```

### Command Execution

#### Execute Command

```
POST /api/command
```

Execute a command through the command handler.

**Request Body:**

```json
{
  "command": "start_injector",
  "params": {
    "injector_enabled": true,
    "auto_inject": false,
    "app_list": ["123456", "789012"]
  }
}
```

**Response:**

Response depends on the command executed.

## WebSocket Events

The Luna API also provides real-time updates through WebSocket events using Socket.IO.

### Connection

```javascript
const socket = io('http://localhost:5000');

socket.on('connect', () => {
  console.log('Connected to Luna API');
});

socket.on('disconnect', () => {
  console.log('Disconnected from Luna API');
});
```

### Events

#### Status Update

```javascript
socket.on('status_update', (status) => {
  console.log('Status update:', status);
});
```

#### Injector Event

```javascript
socket.on('injector_event', (event) => {
  console.log('Injector event:', event);
});
```

#### Unlocker Event

```javascript
socket.on('unlocker_event', (event) => {
  console.log('Unlocker event:', event);
});
```

#### Config Event

```javascript
socket.on('config_event', (event) => {
  console.log('Config event:', event);
});
```

#### System Event

```javascript
socket.on('system_event', (event) => {
  console.log('System event:', event);
});
```

#### Error Event

```javascript
socket.on('error_event', (event) => {
  console.log('Error event:', event);
});
```

#### App Event

```javascript
socket.on('app_event', (event) => {
  console.log('App event:', event);
});
```

#### Platform Event

```javascript
socket.on('platform_event', (event) => {
  console.log('Platform event:', event);
});
```

#### Process Event

```javascript
socket.on('process_event', (event) => {
  console.log('Process event:', event);
});
```

### Command Execution via WebSocket

```javascript
socket.emit('command', {
  command: 'start_injector',
  params: {
    injector_enabled: true,
    auto_inject: false,
    app_list: ['123456', '789012']
  }
}, (response) => {
  console.log('Command response:', response);
});
```

## Error Handling

All API endpoints return a standard error response format:

```json
{
  "success": false,
  "message": "Error message"
}
```

HTTP status codes are used to indicate the type of error:

- 400: Bad Request - The request was malformed or invalid
- 404: Not Found - The requested resource was not found
- 500: Internal Server Error - An error occurred on the server
- 503: Service Unavailable - The service is not available