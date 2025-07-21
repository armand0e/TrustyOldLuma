"""
Luna API Events

This module provides WebSocket event handlers for real-time updates.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, List, Set

import socketio

logger = logging.getLogger("luna.api.events")

class LunaEventHandler:
    """WebSocket event handler for Luna API."""
    
    def __init__(self, sio: socketio.AsyncServer, api_server):
        """Initialize the event handler.
        
        Args:
            sio: Socket.IO server
            api_server: Luna API server instance
        """
        self.sio = sio
        self.api_server = api_server
        self.clients = set()
        self.status_task = None
        
        # Register event handlers
        self._register_handlers()
    
    def _register_handlers(self) -> None:
        """Register Socket.IO event handlers."""
        
        @self.sio.event
        async def connect(sid, environ):
            """Handle client connection."""
            logger.info(f"Client connected: {sid}")
            self.clients.add(sid)
            
            # Send current status on connection
            await self.sio.emit('status_update', self.api_server._status, room=sid)
            
            # Start status update task if not already running
            await self._ensure_status_task()
        
        @self.sio.event
        async def disconnect(sid):
            """Handle client disconnection."""
            logger.info(f"Client disconnected: {sid}")
            self.clients.discard(sid)
            
            # Stop status update task if no clients are connected
            if not self.clients:
                await self._stop_status_task()
        
        @self.sio.event
        async def subscribe(sid, data):
            """Handle subscription to events."""
            logger.debug(f"Client {sid} subscribed to events: {data}")
            
            # Send acknowledgement
            return {"success": True, "message": "Subscribed to events"}
        
        @self.sio.event
        async def unsubscribe(sid, data):
            """Handle unsubscription from events."""
            logger.debug(f"Client {sid} unsubscribed from events: {data}")
            
            # Send acknowledgement
            return {"success": True, "message": "Unsubscribed from events"}
        
        @self.sio.event
        async def command(sid, data):
            """Handle command execution."""
            try:
                command = data.get('command')
                params = data.get('params', {})
                
                if not command:
                    return {"success": False, "message": "Missing command parameter"}
                
                # Execute command if command handler is registered
                if self.api_server.command_handler:
                    result = await self.api_server.command_handler.execute(command, params)
                    return result
                else:
                    return {"success": False, "message": "Command handler not available"}
            
            except Exception as e:
                logger.error(f"Error executing command: {str(e)}")
                return {"success": False, "message": str(e)}
    
    async def _ensure_status_task(self) -> None:
        """Ensure status update task is running."""
        if self.status_task is None or self.status_task.done():
            self.status_task = asyncio.create_task(self._status_update_task())
    
    async def _stop_status_task(self) -> None:
        """Stop status update task."""
        if self.status_task and not self.status_task.done():
            self.status_task.cancel()
            try:
                await self.status_task
            except asyncio.CancelledError:
                pass
            self.status_task = None
    
    async def _status_update_task(self) -> None:
        """Task for periodic status updates."""
        try:
            while self.clients:
                # Get current status
                if self.api_server.luna_core:
                    # Update status with Luna core information
                    status = {
                        "injector_status": "Active" if self.api_server.luna_core.injector_running else "Inactive",
                        "unlocker_status": "Active" if self.api_server.luna_core.unlocker_running else "Inactive",
                        "last_update": self._get_timestamp()
                    }
                    
                    # Update API server status
                    self.api_server._status.update(status)
                
                # Emit status update to all clients
                await self.sio.emit('status_update', self.api_server._status)
                
                # Sleep for a while
                await asyncio.sleep(5)
        
        except asyncio.CancelledError:
            logger.debug("Status update task cancelled")
        
        except Exception as e:
            logger.error(f"Error in status update task: {str(e)}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()