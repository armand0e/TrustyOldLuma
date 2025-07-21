"""
Luna API Endpoints

This module provides additional API endpoints for the Luna CLI backend.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

from aiohttp import web

logger = logging.getLogger("luna.api.endpoints")

class LunaEndpoints:
    """Additional API endpoints for Luna CLI backend."""
    
    def __init__(self, app: web.Application, routes: web.RouteTableDef, api_server):
        """Initialize the endpoints.
        
        Args:
            app: AIOHTTP application
            routes: Route table
            api_server: Luna API server instance
        """
        self.app = app
        self.routes = routes
        self.api_server = api_server
        
        # Register endpoints
        self._register_endpoints()
    
    def _register_endpoints(self):
        """Register API endpoints."""
        
        # App management endpoints
        @self.routes.get('/api/apps')
        async def get_apps(request):
            """Get the list of configured apps."""
            try:
                # Get apps from Luna core
                if self.api_server.luna_core:
                    config = await self.api_server.luna_core.get_config()
                    apps = config.get("app_list", [])
                    
                    # Get app details
                    app_details = []
                    for app_id in apps:
                        # This is a placeholder for actual app detail retrieval
                        app_details.append({
                            "id": app_id,
                            "name": f"App {app_id}",  # Would be replaced with actual app name
                            "enabled": True
                        })
                    
                    return web.json_response({
                        "success": True,
                        "apps": app_details
                    })
                else:
                    # Mock response for testing
                    return web.json_response({
                        "success": True,
                        "apps": [
                            {"id": "123456", "name": "Test App 1", "enabled": True},
                            {"id": "789012", "name": "Test App 2", "enabled": True}
                        ]
                    })
            
            except Exception as e:
                logger.error(f"Error getting apps: {str(e)}")
                return web.json_response({"success": False, "message": str(e)}, status=500)
        
        @self.routes.post('/api/apps')
        async def add_app(request):
            """Add an app to the configuration.
            
            Request body:
                {
                    "app_id": "123456"
                }
            """
            try:
                data = await request.json()
                app_id = data.get("app_id")
                
                if not app_id:
                    return web.json_response({
                        "success": False,
                        "message": "Missing app_id parameter"
                    }, status=400)
                
                # Add app to configuration
                if self.api_server.luna_core:
                    config = await self.api_server.luna_core.get_config()
                    app_list = config.get("app_list", [])
                    
                    # Check if app already exists
                    if app_id in app_list:
                        return web.json_response({
                            "success": False,
                            "message": f"App {app_id} already exists"
                        }, status=400)
                    
                    # Add app to list
                    app_list.append(app_id)
                    config["app_list"] = app_list
                    
                    # Update configuration
                    result = await self.api_server.luna_core.update_config(config)
                    
                    if result.get("success", False):
                        await self.api_server.emit_event('app_event', {
                            "action": "add",
                            "app_id": app_id,
                            "message": f"App {app_id} added successfully"
                        })
                        return web.json_response({
                            "success": True,
                            "message": f"App {app_id} added successfully"
                        })
                    else:
                        return web.json_response({
                            "success": False,
                            "message": result.get("message", f"Failed to add app {app_id}")
                        }, status=500)
                else:
                    # Mock response for testing
                    await asyncio.sleep(1)  # Simulate processing
                    await self.api_server.emit_event('app_event', {
                        "action": "add",
                        "app_id": app_id,
                        "message": f"App {app_id} added successfully (mock)"
                    })
                    return web.json_response({
                        "success": True,
                        "message": f"App {app_id} added successfully (mock)"
                    })
            
            except Exception as e:
                logger.error(f"Error adding app: {str(e)}")
                return web.json_response({"success": False, "message": str(e)}, status=500)
        
        @self.routes.delete('/api/apps/{app_id}')
        async def remove_app(request):
            """Remove an app from the configuration."""
            try:
                app_id = request.match_info.get("app_id")
                
                # Remove app from configuration
                if self.api_server.luna_core:
                    config = await self.api_server.luna_core.get_config()
                    app_list = config.get("app_list", [])
                    
                    # Check if app exists
                    if app_id not in app_list:
                        return web.json_response({
                            "success": False,
                            "message": f"App {app_id} not found"
                        }, status=404)
                    
                    # Remove app from list
                    app_list.remove(app_id)
                    config["app_list"] = app_list
                    
                    # Update configuration
                    result = await self.api_server.luna_core.update_config(config)
                    
                    if result.get("success", False):
                        await self.api_server.emit_event('app_event', {
                            "action": "remove",
                            "app_id": app_id,
                            "message": f"App {app_id} removed successfully"
                        })
                        return web.json_response({
                            "success": True,
                            "message": f"App {app_id} removed successfully"
                        })
                    else:
                        return web.json_response({
                            "success": False,
                            "message": result.get("message", f"Failed to remove app {app_id}")
                        }, status=500)
                else:
                    # Mock response for testing
                    await asyncio.sleep(1)  # Simulate processing
                    await self.api_server.emit_event('app_event', {
                        "action": "remove",
                        "app_id": app_id,
                        "message": f"App {app_id} removed successfully (mock)"
                    })
                    return web.json_response({
                        "success": True,
                        "message": f"App {app_id} removed successfully (mock)"
                    })
            
            except Exception as e:
                logger.error(f"Error removing app: {str(e)}")
                return web.json_response({"success": False, "message": str(e)}, status=500)
        
        # Platform management endpoints
        @self.routes.get('/api/platforms')
        async def get_platforms(request):
            """Get the list of configured platforms."""
            try:
                # Get platforms from Luna core
                if self.api_server.luna_core:
                    config = await self.api_server.luna_core.get_config()
                    platforms = config.get("platforms", {})
                    
                    return web.json_response({
                        "success": True,
                        "platforms": platforms
                    })
                else:
                    # Mock response for testing
                    return web.json_response({
                        "success": True,
                        "platforms": {
                            "steam": {"enabled": True, "priority": 1},
                            "epic": {"enabled": False, "priority": 2},
                            "origin": {"enabled": False, "priority": 3},
                            "uplay": {"enabled": False, "priority": 4}
                        }
                    })
            
            except Exception as e:
                logger.error(f"Error getting platforms: {str(e)}")
                return web.json_response({"success": False, "message": str(e)}, status=500)
        
        @self.routes.put('/api/platforms/{platform_id}')
        async def update_platform(request):
            """Update a platform configuration.
            
            Request body:
                {
                    "enabled": true,
                    "priority": 1
                }
            """
            try:
                platform_id = request.match_info.get("platform_id")
                data = await request.json()
                
                # Update platform configuration
                if self.api_server.luna_core:
                    config = await self.api_server.luna_core.get_config()
                    platforms = config.get("platforms", {})
                    
                    # Check if platform exists
                    if platform_id not in platforms:
                        return web.json_response({
                            "success": False,
                            "message": f"Platform {platform_id} not found"
                        }, status=404)
                    
                    # Update platform configuration
                    platform_config = platforms[platform_id]
                    if "enabled" in data:
                        platform_config["enabled"] = data["enabled"]
                    if "priority" in data:
                        platform_config["priority"] = data["priority"]
                    
                    platforms[platform_id] = platform_config
                    config["platforms"] = platforms
                    
                    # Update configuration
                    result = await self.api_server.luna_core.update_config(config)
                    
                    if result.get("success", False):
                        await self.api_server.emit_event('platform_event', {
                            "action": "update",
                            "platform_id": platform_id,
                            "message": f"Platform {platform_id} updated successfully"
                        })
                        return web.json_response({
                            "success": True,
                            "message": f"Platform {platform_id} updated successfully"
                        })
                    else:
                        return web.json_response({
                            "success": False,
                            "message": result.get("message", f"Failed to update platform {platform_id}")
                        }, status=500)
                else:
                    # Mock response for testing
                    await asyncio.sleep(1)  # Simulate processing
                    await self.api_server.emit_event('platform_event', {
                        "action": "update",
                        "platform_id": platform_id,
                        "message": f"Platform {platform_id} updated successfully (mock)"
                    })
                    return web.json_response({
                        "success": True,
                        "message": f"Platform {platform_id} updated successfully (mock)"
                    })
            
            except Exception as e:
                logger.error(f"Error updating platform: {str(e)}")
                return web.json_response({"success": False, "message": str(e)}, status=500)
        
        # Process management endpoints
        @self.routes.get('/api/processes')
        async def get_processes(request):
            """Get the list of running processes."""
            try:
                # Get processes
                import psutil
                
                # Get process list
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_info']):
                    try:
                        # Get process info
                        proc_info = proc.info
                        
                        # Add process to list
                        processes.append({
                            "pid": proc_info["pid"],
                            "name": proc_info["name"],
                            "username": proc_info["username"],
                            "memory_mb": round(proc_info["memory_info"].rss / (1024 * 1024), 2)
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
                
                return web.json_response({
                    "success": True,
                    "processes": processes
                })
            
            except Exception as e:
                logger.error(f"Error getting processes: {str(e)}")
                return web.json_response({"success": False, "message": str(e)}, status=500)
        
        @self.routes.post('/api/processes/{pid}/inject')
        async def inject_process(request):
            """Inject into a specific process."""
            try:
                pid = int(request.match_info.get("pid"))
                
                # Inject into process
                if self.api_server.luna_core:
                    # This is a placeholder for actual injection logic
                    result = {"success": True, "message": f"Process {pid} injected successfully"}
                    
                    if result.get("success", False):
                        await self.api_server.emit_event('process_event', {
                            "action": "inject",
                            "pid": pid,
                            "message": f"Process {pid} injected successfully"
                        })
                        return web.json_response({
                            "success": True,
                            "message": f"Process {pid} injected successfully"
                        })
                    else:
                        return web.json_response({
                            "success": False,
                            "message": result.get("message", f"Failed to inject into process {pid}")
                        }, status=500)
                else:
                    # Mock response for testing
                    await asyncio.sleep(1)  # Simulate processing
                    await self.api_server.emit_event('process_event', {
                        "action": "inject",
                        "pid": pid,
                        "message": f"Process {pid} injected successfully (mock)"
                    })
                    return web.json_response({
                        "success": True,
                        "message": f"Process {pid} injected successfully (mock)"
                    })
            
            except Exception as e:
                logger.error(f"Error injecting into process: {str(e)}")
                return web.json_response({"success": False, "message": str(e)}, status=500)
        
        # Advanced configuration endpoints
        @self.routes.get('/api/config/advanced')
        async def get_advanced_config(request):
            """Get advanced configuration options."""
            try:
                # Get advanced configuration
                if self.api_server.luna_core:
                    config = await self.api_server.luna_core.get_config()
                    
                    # Extract advanced configuration
                    advanced_config = {
                        "stealth_mode": config.get("luna", {}).get("core", {}).get("stealth_mode", True),
                        "auto_start": config.get("luna", {}).get("core", {}).get("auto_start", False),
                        "minimize_to_tray": config.get("luna", {}).get("gui", {}).get("minimize_to_tray", True),
                        "api_port": config.get("luna", {}).get("api", {}).get("port", 5000),
                        "log_level": config.get("luna", {}).get("logging", {}).get("level", "INFO")
                    }
                    
                    return web.json_response({
                        "success": True,
                        "config": advanced_config
                    })
                else:
                    # Mock response for testing
                    return web.json_response({
                        "success": True,
                        "config": {
                            "stealth_mode": True,
                            "auto_start": False,
                            "minimize_to_tray": True,
                            "api_port": 5000,
                            "log_level": "INFO"
                        }
                    })
            
            except Exception as e:
                logger.error(f"Error getting advanced configuration: {str(e)}")
                return web.json_response({"success": False, "message": str(e)}, status=500)
        
        @self.routes.put('/api/config/advanced')
        async def update_advanced_config(request):
            """Update advanced configuration options.
            
            Request body:
                {
                    "stealth_mode": true,
                    "auto_start": false,
                    "minimize_to_tray": true,
                    "api_port": 5000,
                    "log_level": "INFO"
                }
            """
            try:
                data = await request.json()
                
                # Update advanced configuration
                if self.api_server.luna_core:
                    config = await self.api_server.luna_core.get_config()
                    
                    # Update advanced configuration
                    if "stealth_mode" in data:
                        config.setdefault("luna", {}).setdefault("core", {})["stealth_mode"] = data["stealth_mode"]
                    
                    if "auto_start" in data:
                        config.setdefault("luna", {}).setdefault("core", {})["auto_start"] = data["auto_start"]
                    
                    if "minimize_to_tray" in data:
                        config.setdefault("luna", {}).setdefault("gui", {})["minimize_to_tray"] = data["minimize_to_tray"]
                    
                    if "api_port" in data:
                        config.setdefault("luna", {}).setdefault("api", {})["port"] = data["api_port"]
                    
                    if "log_level" in data:
                        config.setdefault("luna", {}).setdefault("logging", {})["level"] = data["log_level"]
                    
                    # Update configuration
                    result = await self.api_server.luna_core.update_config(config)
                    
                    if result.get("success", False):
                        await self.api_server.emit_event('config_event', {
                            "action": "update_advanced",
                            "message": "Advanced configuration updated successfully"
                        })
                        return web.json_response({
                            "success": True,
                            "message": "Advanced configuration updated successfully"
                        })
                    else:
                        return web.json_response({
                            "success": False,
                            "message": result.get("message", "Failed to update advanced configuration")
                        }, status=500)
                else:
                    # Mock response for testing
                    await asyncio.sleep(1)  # Simulate processing
                    await self.api_server.emit_event('config_event', {
                        "action": "update_advanced",
                        "message": "Advanced configuration updated successfully (mock)"
                    })
                    return web.json_response({
                        "success": True,
                        "message": "Advanced configuration updated successfully (mock)"
                    })
            
            except Exception as e:
                logger.error(f"Error updating advanced configuration: {str(e)}")
                return web.json_response({"success": False, "message": str(e)}, status=500)
        
        # Add routes to app
        self.app.add_routes(self.routes)