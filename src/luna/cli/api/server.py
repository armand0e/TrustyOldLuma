"""
Luna API Server

This module implements the API server for the Luna CLI backend.
"""

import asyncio
import json
import logging
import os
import socket
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Callable, Awaitable

import aiohttp
from aiohttp import web
import socketio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("luna.api")

class LunaAPIServer:
    """Luna API Server for GUI-CLI communication."""
    
    def __init__(self, host: str = "localhost", port: int = 5000):
        """Initialize the API server.
        
        Args:
            host: Host to bind the server to
            port: Port to bind the server to
        """
        self.host = host
        self.port = port
        self.app = web.Application()
        self.routes = web.RouteTableDef()
        self.sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins='*')
        self.sio.attach(self.app)
        self.runner = None
        self.site = None
        self.luna_core = None
        self.command_handler = None
        
        # Status tracking
        self._status = {
            "api_connected": True,
            "injector_status": "Inactive",
            "unlocker_status": "Inactive",
            "last_update": None
        }
        
        # Event handlers
        self.event_handlers = {}
        
        # Setup CORS
        self._setup_cors()
        
        # Setup default routes
        self._setup_default_routes()
        
        # Setup Socket.IO events
        self._setup_socketio_events()
    
    def _setup_cors(self) -> None:
        """Set up CORS for the API server."""
        
        @self.app.on_response_prepare.append
        async def on_prepare(request, response):
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    
    def _setup_default_routes(self) -> None:
        """Set up default routes for the API server."""
        
        @self.routes.get('/api/status')
        async def get_status(request):
            """Get the current status of the Luna API."""
            self._status["last_update"] = self._get_timestamp()
            return web.json_response(self._status)
        
        @self.routes.post('/api/command')
        async def execute_command(request):
            """Execute a command through the command handler.
            
            Request body:
                {
                    "command": "command_name",
                    "params": {
                        "param1": "value1",
                        "param2": "value2"
                    }
                }
            """
            try:
                data = await request.json()
                command = data.get('command')
                params = data.get('params', {})
                
                if not command:
                    return web.json_response({
                        "success": False,
                        "message": "Missing command parameter"
                    }, status=400)
                
                # Execute command if command handler is registered
                if self.command_handler:
                    result = await self.command_handler.execute(command, params)
                    return web.json_response(result)
                else:
                    return web.json_response({
                        "success": False,
                        "message": "Command handler not available"
                    }, status=503)
            
            except ValueError as e:
                logger.error(f"Invalid command: {str(e)}")
                return web.json_response({
                    "success": False,
                    "message": f"Invalid command: {str(e)}"
                }, status=400)
            
            except Exception as e:
                logger.error(f"Error executing command: {str(e)}")
                return web.json_response({
                    "success": False,
                    "message": f"Error executing command: {str(e)}"
                }, status=500)
        
        @self.routes.options('/{tail:.*}')
        async def options_handler(request):
            """Handle OPTIONS requests for CORS preflight."""
            return web.Response(status=204)
        
        # Add routes to app
        self.app.add_routes(self.routes)
    
    def _setup_socketio_events(self) -> None:
        """Set up Socket.IO events."""
        # Event handler will be initialized after routes are registered
        # This is just a placeholder for basic events
        
        @self.sio.event
        async def connect(sid, environ):
            """Handle client connection."""
            logger.info(f"Client connected: {sid}")
            # Send current status on connection
            await self.sio.emit('status_update', self._status, room=sid)
        
        @self.sio.event
        async def disconnect(sid):
            """Handle client disconnection."""
            logger.info(f"Client disconnected: {sid}")
    
    def register_routes(self, routes_module) -> None:
        """Register routes from a module.
        
        Args:
            routes_module: Module containing route definitions
        """
        routes_module.register_routes(self.app, self.routes, self.sio, self)
        
        # Register additional endpoints
        from .endpoints import LunaEndpoints
        self.endpoints = LunaEndpoints(self.app, self.routes, self)
        
        # Register event handler
        from .events import LunaEventHandler
        self.event_handler = LunaEventHandler(self.sio, self)
    
    def register_luna_core(self, luna_core) -> None:
        """Register Luna core instance.
        
        Args:
            luna_core: Luna core instance
        """
        self.luna_core = luna_core
    
    def register_event_handler(self, event: str, handler: Callable[[Dict[str, Any]], Awaitable[None]]) -> None:
        """Register an event handler.
        
        Args:
            event: Event name
            handler: Event handler function
        """
        self.event_handlers[event] = handler
    
    async def emit_event(self, event: str, data: Dict[str, Any]) -> None:
        """Emit an event to all connected clients.
        
        Args:
            event: Event name
            data: Event data
        """
        await self.sio.emit(event, data)
        
        # Call registered handler if exists
        if event in self.event_handlers:
            await self.event_handlers[event](data)
    
    async def update_status(self, status_update: Dict[str, Any]) -> None:
        """Update the API status.
        
        Args:
            status_update: Status update data
        """
        self._status.update(status_update)
        self._status["last_update"] = self._get_timestamp()
        await self.emit_event('status_update', self._status)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    async def start(self) -> None:
        """Start the API server."""
        logger.info(f"Starting Luna API server on {self.host}:{self.port}")
        
        # Check if port is available
        if not self._is_port_available(self.port):
            logger.warning(f"Port {self.port} is already in use. Trying to find an available port...")
            self.port = self._find_available_port()
            logger.info(f"Using port {self.port} instead")
        
        # Start the server
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        
        logger.info(f"Luna API server running on http://{self.host}:{self.port}")
    
    async def stop(self) -> None:
        """Stop the API server."""
        logger.info("Stopping Luna API server")
        
        if self.site:
            await self.site.stop()
        
        if self.runner:
            await self.runner.cleanup()
        
        logger.info("Luna API server stopped")
    
    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available.
        
        Args:
            port: Port to check
            
        Returns:
            bool: True if port is available, False otherwise
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("localhost", port))
                return True
            except socket.error:
                return False
    
    def _find_available_port(self, start_port: int = 5000, max_port: int = 5100) -> int:
        """Find an available port.
        
        Args:
            start_port: Starting port number
            max_port: Maximum port number
            
        Returns:
            int: Available port number
        """
        for port in range(start_port, max_port):
            if self._is_port_available(port):
                return port
        
        # If no port is available, raise an exception
        raise RuntimeError(f"No available ports found in range {start_port}-{max_port}")