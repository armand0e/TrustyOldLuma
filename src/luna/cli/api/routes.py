"""
Luna API Routes

This module defines the API routes for the Luna CLI backend.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

from aiohttp import web
import socketio

logger = logging.getLogger("luna.api.routes")

def register_routes(app, routes, sio, api_server):
    """Register API routes.
    
    Args:
        app: AIOHTTP application
        routes: Route table
        sio: Socket.IO server
        api_server: Luna API server instance
    """
    # Injector routes
    @routes.post('/api/injector/start')
    async def start_injector(request):
        """Start the Luna injector.
        
        Request body:
            {
                "injector_enabled": true,
                "auto_inject": false,
                "app_list": ["123456", "789012"]
            }
        """
        try:
            data = await request.json()
            
            # Update status
            await api_server.update_status({"injector_status": "Starting"})
            
            # Start injector (if Luna core is registered)
            if api_server.luna_core:
                result = await api_server.luna_core.start_injector(data)
                
                if result.get('success', False):
                    await api_server.update_status({"injector_status": "Active"})
                    await api_server.emit_event('injector_event', {
                        "status": "Active",
                        "message": "Injector started successfully"
                    })
                    return web.json_response({"success": True, "message": "Injector started successfully"})
                else:
                    await api_server.update_status({"injector_status": "Error"})
                    await api_server.emit_event('injector_event', {
                        "status": "Error",
                        "message": result.get('message', 'Failed to start injector')
                    })
                    return web.json_response({
                        "success": False,
                        "message": result.get('message', 'Failed to start injector')
                    }, status=500)
            else:
                # Mock response for testing
                await asyncio.sleep(1)  # Simulate processing
                await api_server.update_status({"injector_status": "Active"})
                await api_server.emit_event('injector_event', {
                    "status": "Active",
                    "message": "Injector started successfully (mock)"
                })
                return web.json_response({"success": True, "message": "Injector started successfully (mock)"})
        
        except Exception as e:
            logger.error(f"Error starting injector: {str(e)}")
            await api_server.update_status({"injector_status": "Error"})
            await api_server.emit_event('error_event', {
                "message": f"Error starting injector: {str(e)}"
            })
            return web.json_response({"success": False, "message": str(e)}, status=500)
    
    @routes.post('/api/injector/stop')
    async def stop_injector(request):
        """Stop the Luna injector."""
        try:
            # Update status
            await api_server.update_status({"injector_status": "Stopping"})
            
            # Stop injector (if Luna core is registered)
            if api_server.luna_core:
                result = await api_server.luna_core.stop_injector()
                
                if result.get('success', False):
                    await api_server.update_status({"injector_status": "Inactive"})
                    await api_server.emit_event('injector_event', {
                        "status": "Inactive",
                        "message": "Injector stopped successfully"
                    })
                    return web.json_response({"success": True, "message": "Injector stopped successfully"})
                else:
                    await api_server.update_status({"injector_status": "Error"})
                    await api_server.emit_event('injector_event', {
                        "status": "Error",
                        "message": result.get('message', 'Failed to stop injector')
                    })
                    return web.json_response({
                        "success": False,
                        "message": result.get('message', 'Failed to stop injector')
                    }, status=500)
            else:
                # Mock response for testing
                await asyncio.sleep(1)  # Simulate processing
                await api_server.update_status({"injector_status": "Inactive"})
                await api_server.emit_event('injector_event', {
                    "status": "Inactive",
                    "message": "Injector stopped successfully (mock)"
                })
                return web.json_response({"success": True, "message": "Injector stopped successfully (mock)"})
        
        except Exception as e:
            logger.error(f"Error stopping injector: {str(e)}")
            await api_server.emit_event('error_event', {
                "message": f"Error stopping injector: {str(e)}"
            })
            return web.json_response({"success": False, "message": str(e)}, status=500)
    
    # Unlocker routes
    @routes.post('/api/unlocker/start')
    async def start_unlocker(request):
        """Start the Luna unlocker.
        
        Request body:
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
        """
        try:
            data = await request.json()
            
            # Update status
            await api_server.update_status({"unlocker_status": "Starting"})
            
            # Start unlocker (if Luna core is registered)
            if api_server.luna_core:
                result = await api_server.luna_core.start_unlocker(data)
                
                if result.get('success', False):
                    await api_server.update_status({"unlocker_status": "Active"})
                    await api_server.emit_event('unlocker_event', {
                        "status": "Active",
                        "message": "Unlocker started successfully"
                    })
                    return web.json_response({"success": True, "message": "Unlocker started successfully"})
                else:
                    await api_server.update_status({"unlocker_status": "Error"})
                    await api_server.emit_event('unlocker_event', {
                        "status": "Error",
                        "message": result.get('message', 'Failed to start unlocker')
                    })
                    return web.json_response({
                        "success": False,
                        "message": result.get('message', 'Failed to start unlocker')
                    }, status=500)
            else:
                # Mock response for testing
                await asyncio.sleep(1)  # Simulate processing
                await api_server.update_status({"unlocker_status": "Active"})
                await api_server.emit_event('unlocker_event', {
                    "status": "Active",
                    "message": "Unlocker started successfully (mock)"
                })
                return web.json_response({"success": True, "message": "Unlocker started successfully (mock)"})
        
        except Exception as e:
            logger.error(f"Error starting unlocker: {str(e)}")
            await api_server.update_status({"unlocker_status": "Error"})
            await api_server.emit_event('error_event', {
                "message": f"Error starting unlocker: {str(e)}"
            })
            return web.json_response({"success": False, "message": str(e)}, status=500)
    
    @routes.post('/api/unlocker/stop')
    async def stop_unlocker(request):
        """Stop the Luna unlocker."""
        try:
            # Update status
            await api_server.update_status({"unlocker_status": "Stopping"})
            
            # Stop unlocker (if Luna core is registered)
            if api_server.luna_core:
                result = await api_server.luna_core.stop_unlocker()
                
                if result.get('success', False):
                    await api_server.update_status({"unlocker_status": "Inactive"})
                    await api_server.emit_event('unlocker_event', {
                        "status": "Inactive",
                        "message": "Unlocker stopped successfully"
                    })
                    return web.json_response({"success": True, "message": "Unlocker stopped successfully"})
                else:
                    await api_server.update_status({"unlocker_status": "Error"})
                    await api_server.emit_event('unlocker_event', {
                        "status": "Error",
                        "message": result.get('message', 'Failed to stop unlocker')
                    })
                    return web.json_response({
                        "success": False,
                        "message": result.get('message', 'Failed to stop unlocker')
                    }, status=500)
            else:
                # Mock response for testing
                await asyncio.sleep(1)  # Simulate processing
                await api_server.update_status({"unlocker_status": "Inactive"})
                await api_server.emit_event('unlocker_event', {
                    "status": "Inactive",
                    "message": "Unlocker stopped successfully (mock)"
                })
                return web.json_response({"success": True, "message": "Unlocker stopped successfully (mock)"})
        
        except Exception as e:
            logger.error(f"Error stopping unlocker: {str(e)}")
            await api_server.emit_event('error_event', {
                "message": f"Error stopping unlocker: {str(e)}"
            })
            return web.json_response({"success": False, "message": str(e)}, status=500)
    
    # Configuration routes
    @routes.get('/api/config')
    async def get_config(request):
        """Get the Luna configuration."""
        try:
            # Get configuration (if Luna core is registered)
            if api_server.luna_core:
                config = await api_server.luna_core.get_config()
                return web.json_response(config)
            else:
                # Mock response for testing
                return web.json_response({
                    "injector_enabled": True,
                    "auto_inject": False,
                    "app_list": ["123456", "789012"],
                    "unlocker_enabled": True,
                    "unlock_dlc": True,
                    "unlock_shared": False,
                    "platforms": {
                        "steam": {"enabled": True},
                        "epic": {"enabled": False},
                        "origin": {"enabled": False},
                        "uplay": {"enabled": False}
                    },
                    "auto_start": False,
                    "minimize_to_tray": True,
                    "api_port": 5000
                })
        
        except Exception as e:
            logger.error(f"Error getting configuration: {str(e)}")
            await api_server.emit_event('error_event', {
                "message": f"Error getting configuration: {str(e)}"
            })
            return web.json_response({"success": False, "message": str(e)}, status=500)
    
    @routes.put('/api/config')
    async def update_config(request):
        """Update the Luna configuration.
        
        Request body: Configuration object
        """
        try:
            data = await request.json()
            
            # Update configuration (if Luna core is registered)
            if api_server.luna_core:
                result = await api_server.luna_core.update_config(data)
                
                if result.get('success', False):
                    await api_server.emit_event('config_event', {
                        "message": "Configuration updated successfully"
                    })
                    return web.json_response({"success": True, "message": "Configuration updated successfully"})
                else:
                    await api_server.emit_event('error_event', {
                        "message": result.get('message', 'Failed to update configuration')
                    })
                    return web.json_response({
                        "success": False,
                        "message": result.get('message', 'Failed to update configuration')
                    }, status=500)
            else:
                # Mock response for testing
                await asyncio.sleep(1)  # Simulate processing
                await api_server.emit_event('config_event', {
                    "message": "Configuration updated successfully (mock)"
                })
                return web.json_response({"success": True, "message": "Configuration updated successfully (mock)"})
        
        except Exception as e:
            logger.error(f"Error updating configuration: {str(e)}")
            await api_server.emit_event('error_event', {
                "message": f"Error updating configuration: {str(e)}"
            })
            return web.json_response({"success": False, "message": str(e)}, status=500)
    
    @routes.post('/api/config/migrate')
    async def migrate_config(request):
        """Migrate legacy configurations."""
        try:
            # Migrate configuration (if Luna core is registered)
            if api_server.luna_core:
                result = await api_server.luna_core.migrate_config()
                
                if result.get('success', False):
                    await api_server.emit_event('config_event', {
                        "message": "Legacy configurations migrated successfully"
                    })
                    return web.json_response({"success": True, "message": "Legacy configurations migrated successfully"})
                else:
                    await api_server.emit_event('error_event', {
                        "message": result.get('message', 'Failed to migrate configurations')
                    })
                    return web.json_response({
                        "success": False,
                        "message": result.get('message', 'Failed to migrate configurations')
                    }, status=500)
            else:
                # Mock response for testing
                await asyncio.sleep(1)  # Simulate processing
                await api_server.emit_event('config_event', {
                    "message": "Legacy configurations migrated successfully (mock)"
                })
                return web.json_response({"success": True, "message": "Legacy configurations migrated successfully (mock)"})
        
        except Exception as e:
            logger.error(f"Error migrating configurations: {str(e)}")
            await api_server.emit_event('error_event', {
                "message": f"Error migrating configurations: {str(e)}"
            })
            return web.json_response({"success": False, "message": str(e)}, status=500)
    
    # System routes
    @routes.post('/api/system/shortcuts')
    async def create_shortcuts(request):
        """Create Luna desktop shortcuts."""
        try:
            # Create shortcuts (if Luna core is registered)
            if api_server.luna_core:
                result = await api_server.luna_core.create_shortcuts()
                
                if result.get('success', False):
                    await api_server.emit_event('system_event', {
                        "message": "Shortcuts created successfully"
                    })
                    return web.json_response({"success": True, "message": "Shortcuts created successfully"})
                else:
                    await api_server.emit_event('error_event', {
                        "message": result.get('message', 'Failed to create shortcuts')
                    })
                    return web.json_response({
                        "success": False,
                        "message": result.get('message', 'Failed to create shortcuts')
                    }, status=500)
            else:
                # Mock response for testing
                await asyncio.sleep(1)  # Simulate processing
                await api_server.emit_event('system_event', {
                    "message": "Shortcuts created successfully (mock)"
                })
                return web.json_response({"success": True, "message": "Shortcuts created successfully (mock)"})
        
        except Exception as e:
            logger.error(f"Error creating shortcuts: {str(e)}")
            await api_server.emit_event('error_event', {
                "message": f"Error creating shortcuts: {str(e)}"
            })
            return web.json_response({"success": False, "message": str(e)}, status=500)
    
    @routes.post('/api/system/security')
    async def setup_security_exclusions(request):
        """Set up security exclusions for Luna."""
        try:
            # Set up security exclusions (if Luna core is registered)
            if api_server.luna_core:
                result = await api_server.luna_core.setup_security_exclusions()
                
                if result.get('success', False):
                    await api_server.emit_event('system_event', {
                        "message": "Security exclusions set up successfully"
                    })
                    return web.json_response({"success": True, "message": "Security exclusions set up successfully"})
                else:
                    await api_server.emit_event('error_event', {
                        "message": result.get('message', 'Failed to set up security exclusions')
                    })
                    return web.json_response({
                        "success": False,
                        "message": result.get('message', 'Failed to set up security exclusions')
                    }, status=500)
            else:
                # Mock response for testing
                await asyncio.sleep(1)  # Simulate processing
                await api_server.emit_event('system_event', {
                    "message": "Security exclusions set up successfully (mock)"
                })
                return web.json_response({"success": True, "message": "Security exclusions set up successfully (mock)"})
        
        except Exception as e:
            logger.error(f"Error setting up security exclusions: {str(e)}")
            await api_server.emit_event('error_event', {
                "message": f"Error setting up security exclusions: {str(e)}"
            })
            return web.json_response({"success": False, "message": str(e)}, status=500)
    
    @routes.get('/api/system/compatibility')
    async def check_system_compatibility(request):
        """Check system compatibility for Luna."""
        try:
            # Check system compatibility (if command handler is registered)
            if api_server.command_handler:
                result = await api_server.command_handler.check_system_compatibility()
                return web.json_response(result)
            elif api_server.luna_core:
                # Fallback to Luna core if available
                result = await api_server.luna_core.check_system_compatibility()
                return web.json_response(result)
            else:
                # Mock response for testing
                import platform
                return web.json_response({
                    "success": True,
                    "compatibility": {
                        "system": {
                            "name": platform.system(),
                            "release": platform.release(),
                            "version": platform.version(),
                            "architecture": platform.architecture()[0],
                            "processor": platform.processor()
                        },
                        "requirements": {
                            "windows": {"required": True, "satisfied": platform.system().lower() == "windows"},
                            "windows_10": {"required": True, "satisfied": platform.system().lower() == "windows" and int(platform.release()) >= 10},
                            "64bit": {"required": True, "satisfied": "64" in platform.architecture()[0]},
                            "admin": {"required": True, "satisfied": True},
                            "dotnet": {"required": True, "satisfied": True}
                        },
                        "is_compatible": platform.system().lower() == "windows" and int(platform.release()) >= 10 and "64" in platform.architecture()[0],
                        "needs_admin": False
                    }
                })
        
        except Exception as e:
            logger.error(f"Error checking system compatibility: {str(e)}")
            await api_server.emit_event('error_event', {
                "message": f"Error checking system compatibility: {str(e)}"
            })
            return web.json_response({"success": False, "message": str(e)}, status=500)
    
    # Service management routes
    @routes.get('/api/service/status')
    async def get_service_status(request):
        """Get Luna service status."""
        try:
            # Get service status
            import os
            import time
            
            return web.json_response({
                "success": True,
                "service": {
                    "running": True,
                    "pid": os.getpid(),
                    "uptime": time.time() - os.path.getctime('/proc/self') if os.path.exists('/proc/self') else 0,
                    "api_port": api_server.port
                }
            })
        
        except Exception as e:
            logger.error(f"Error getting service status: {str(e)}")
            return web.json_response({"success": False, "message": str(e)}, status=500)
    
    # Logging routes
    @routes.get('/api/logs')
    async def get_logs(request):
        """Get Luna logs."""
        try:
            # Get log file path
            log_file = Path.home() / "AppData" / "Roaming" / "Luna" / "logs" / "luna_cli.log"
            
            # Check if log file exists
            if not log_file.exists():
                return web.json_response({
                    "success": False,
                    "message": "Log file not found"
                }, status=404)
            
            # Read log file (last 100 lines)
            with open(log_file, 'r') as f:
                lines = f.readlines()
                logs = lines[-100:] if len(lines) > 100 else lines
            
            return web.json_response({
                "success": True,
                "logs": logs
            })
        
        except Exception as e:
            logger.error(f"Error getting logs: {str(e)}")
            return web.json_response({"success": False, "message": str(e)}, status=500)
    
    # Add routes to app
    app.add_routes(routes)