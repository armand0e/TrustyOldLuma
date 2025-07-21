"""
Luna CLI

This module implements the Luna CLI backend that communicates with the GUI.
"""

import argparse
import asyncio
import json
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Awaitable

from ..core.luna_core import LunaCore
from .api import LunaAPIServer, register_routes
from .commands import LunaCommandHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path.home() / "AppData" / "Roaming" / "Luna" / "logs" / "luna_cli.log", mode='a')
    ]
)
logger = logging.getLogger("luna.cli")

class LunaCLI:
    """Luna CLI backend for GUI communication."""
    
    def __init__(self):
        """Initialize the Luna CLI."""
        self.api_server = None
        self.luna_core = None
        self.command_handler = None
        self.running = False
        self.config_path = None
        self.background_tasks = []
        self.service_mode = False
        self.service_pid_file = Path.home() / "AppData" / "Roaming" / "Luna" / "luna_cli.pid"
    
    async def initialize(self, config_path: Optional[Path] = None, api_port: int = 5000, 
                      service_mode: bool = False) -> bool:
        """Initialize the Luna CLI.
        
        Args:
            config_path: Path to Luna configuration file
            api_port: Port for API server
            service_mode: Run as a background service
            
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            # Set service mode
            self.service_mode = service_mode
            
            # Create logs directory if it doesn't exist
            logs_dir = Path.home() / "AppData" / "Roaming" / "Luna" / "logs"
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize Luna core
            self.config_path = config_path or self._get_default_config_path()
            self.luna_core = LunaCore(self.config_path)
            await self.luna_core.initialize()
            
            # Initialize command handler
            self.command_handler = LunaCommandHandler(self.luna_core)
            
            # Initialize API server
            self.api_server = LunaAPIServer(port=api_port)
            
            # Register routes
            from .api import routes
            self.api_server.register_routes(routes)
            
            # Register Luna core with API server
            self.api_server.register_luna_core(self.luna_core)
            
            # Register command handler with API server
            self.api_server.command_handler = self.command_handler
            
            # Register signal handlers
            self._register_signal_handlers()
            
            # Write PID file if in service mode
            if self.service_mode:
                self._write_pid_file()
            
            logger.info(f"Luna CLI initialized (service mode: {self.service_mode})")
            return True
        
        except Exception as e:
            logger.error(f"Error initializing Luna CLI: {str(e)}")
            return False
    
    async def start(self) -> None:
        """Start the Luna CLI."""
        if not self.api_server:
            raise RuntimeError("Luna CLI not initialized")
        
        # Start API server
        await self.api_server.start()
        self.running = True
        
        # Start background tasks
        await self._start_background_tasks()
        
        # Log startup information
        logger.info(f"Luna CLI started on port {self.api_server.port}")
        if self.service_mode:
            logger.info(f"Running in service mode (PID: {os.getpid()})")
        
        # Auto-start components if configured
        if self.luna_core.config.get("luna", {}).get("core", {}).get("auto_start", False):
            logger.info("Auto-starting Luna components")
            if self.luna_core.config.get("luna", {}).get("core", {}).get("injector_enabled", True):
                await self.luna_core.start_injector()
            if self.luna_core.config.get("luna", {}).get("core", {}).get("unlocker_enabled", True):
                await self.luna_core.start_unlocker()
        
        # Keep running until stopped
        while self.running:
            await asyncio.sleep(1)
    
    async def stop(self) -> None:
        """Stop the Luna CLI."""
        logger.info("Stopping Luna CLI")
        self.running = False
        
        # Stop background tasks
        await self._stop_background_tasks()
        
        # Stop API server
        if self.api_server:
            await self.api_server.stop()
        
        # Stop Luna core
        if self.luna_core:
            await self.luna_core.shutdown()
        
        # Remove PID file if in service mode
        if self.service_mode:
            self._remove_pid_file()
        
        logger.info("Luna CLI stopped")
    
    def _register_signal_handlers(self) -> None:
        """Register signal handlers for graceful shutdown."""
        loop = asyncio.get_event_loop()
        
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self._handle_signal()))
    
    async def _handle_signal(self) -> None:
        """Handle termination signals."""
        logger.info("Received termination signal")
        await self.stop()
    
    def _get_default_config_path(self) -> Path:
        """Get default configuration path.
        
        Returns:
            Path: Default configuration path
        """
        # Check for config in current directory
        local_config = Path("luna_config.jsonc")
        if local_config.exists():
            return local_config
        
        # Check for config in user's documents directory
        docs_dir = Path.home() / "Documents" / "Luna"
        docs_config = docs_dir / "luna_config.jsonc"
        if docs_config.exists():
            return docs_config
        
        # Check for config in AppData directory
        appdata_dir = Path.home() / "AppData" / "Roaming" / "Luna"
        appdata_config = appdata_dir / "luna_config.jsonc"
        if appdata_config.exists():
            return appdata_config
        
        # Default to local config
        return local_config
    
    def _write_pid_file(self) -> None:
        """Write PID file for service mode."""
        try:
            # Create parent directory if it doesn't exist
            self.service_pid_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write PID to file
            with open(self.service_pid_file, 'w') as f:
                f.write(str(os.getpid()))
            
            logger.debug(f"PID file written: {self.service_pid_file}")
        
        except Exception as e:
            logger.error(f"Error writing PID file: {str(e)}")
    
    def _remove_pid_file(self) -> None:
        """Remove PID file for service mode."""
        try:
            if self.service_pid_file.exists():
                self.service_pid_file.unlink()
                logger.debug(f"PID file removed: {self.service_pid_file}")
        
        except Exception as e:
            logger.error(f"Error removing PID file: {str(e)}")
    
    async def _start_background_tasks(self) -> None:
        """Start background tasks."""
        # Status monitoring task
        self.background_tasks.append(asyncio.create_task(self._status_monitoring_task()))
        
        # Health check task
        self.background_tasks.append(asyncio.create_task(self._health_check_task()))
        
        logger.debug(f"Started {len(self.background_tasks)} background tasks")
    
    async def _stop_background_tasks(self) -> None:
        """Stop background tasks."""
        for task in self.background_tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self.background_tasks.clear()
        logger.debug("Background tasks stopped")
    
    async def _status_monitoring_task(self) -> None:
        """Background task for status monitoring."""
        try:
            while self.running:
                # Get current status
                if self.api_server and self.luna_core:
                    status = {
                        "injector_status": "Active" if self.luna_core.injector_running else "Inactive",
                        "unlocker_status": "Active" if self.luna_core.unlocker_running else "Inactive",
                        "last_update": self._get_timestamp()
                    }
                    
                    # Update API server status
                    await self.api_server.update_status(status)
                
                # Sleep for a while
                await asyncio.sleep(5)
        
        except asyncio.CancelledError:
            logger.debug("Status monitoring task cancelled")
        
        except Exception as e:
            logger.error(f"Error in status monitoring task: {str(e)}")
    
    async def _health_check_task(self) -> None:
        """Background task for health checking."""
        try:
            while self.running:
                # Check Luna core health
                if self.luna_core:
                    # This is a placeholder for actual health check logic
                    pass
                
                # Sleep for a while
                await asyncio.sleep(30)
        
        except asyncio.CancelledError:
            logger.debug("Health check task cancelled")
        
        except Exception as e:
            logger.error(f"Error in health check task: {str(e)}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()

def parse_args():
    """Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Luna CLI - Backend for Luna Gaming Tool")
    parser.add_argument("--config", help="Path to Luna configuration file")
    parser.add_argument("--port", type=int, default=5000, help="API server port")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--service", action="store_true", help="Run as a background service")
    parser.add_argument("--stop-service", action="store_true", help="Stop running service")
    parser.add_argument("--status", action="store_true", help="Check service status")
    parser.add_argument("--auto-start", action="store_true", help="Auto-start Luna components")
    parser.add_argument("--no-auto-start", action="store_true", help="Disable auto-start")
    parser.add_argument("--host", default="localhost", help="Host to bind the API server to")
    
    return parser.parse_args()

def check_service_status():
    """Check if Luna CLI service is running.
    
    Returns:
        bool: True if service is running, False otherwise
    """
    pid_file = Path.home() / "AppData" / "Roaming" / "Luna" / "luna_cli.pid"
    
    if not pid_file.exists():
        return False
    
    try:
        # Read PID from file
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        # Check if process is running
        if sys.platform == "win32":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(1, False, pid)
            if handle:
                kernel32.CloseHandle(handle)
                return True
            return False
        else:
            # Unix-like systems
            import os
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False
    
    except Exception:
        return False

def stop_service():
    """Stop Luna CLI service.
    
    Returns:
        bool: True if service was stopped, False otherwise
    """
    pid_file = Path.home() / "AppData" / "Roaming" / "Luna" / "luna_cli.pid"
    
    if not pid_file.exists():
        logger.info("No Luna CLI service running")
        return False
    
    try:
        # Read PID from file
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        # Send termination signal
        if sys.platform == "win32":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(1, False, pid)
            if handle:
                # Windows-specific termination
                result = kernel32.TerminateProcess(handle, 0)
                kernel32.CloseHandle(handle)
                
                if result:
                    logger.info(f"Sent termination signal to Luna CLI service (PID: {pid})")
                    
                    # Wait for process to terminate
                    for _ in range(10):
                        if not check_service_status():
                            # Remove PID file if it still exists
                            if pid_file.exists():
                                pid_file.unlink()
                            return True
                        time.sleep(0.5)
                    
                    logger.warning(f"Luna CLI service (PID: {pid}) did not terminate within timeout")
                    return False
                else:
                    logger.error(f"Failed to terminate Luna CLI service (PID: {pid})")
                    return False
            else:
                logger.info(f"Luna CLI service (PID: {pid}) is not running")
                # Remove stale PID file
                pid_file.unlink()
                return True
        else:
            # Unix-like systems
            import os
            import signal
            try:
                os.kill(pid, signal.SIGTERM)
                logger.info(f"Sent termination signal to Luna CLI service (PID: {pid})")
                
                # Wait for process to terminate
                for _ in range(10):
                    try:
                        os.kill(pid, 0)
                        time.sleep(0.5)
                    except OSError:
                        # Process has terminated
                        # Remove PID file if it still exists
                        if pid_file.exists():
                            pid_file.unlink()
                        return True
                
                logger.warning(f"Luna CLI service (PID: {pid}) did not terminate within timeout")
                return False
            except OSError:
                logger.info(f"Luna CLI service (PID: {pid}) is not running")
                # Remove stale PID file
                pid_file.unlink()
                return True
    
    except Exception as e:
        logger.error(f"Error stopping Luna CLI service: {str(e)}")
        return False

async def main():
    """Main entry point for Luna CLI."""
    args = parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger("luna").setLevel(logging.DEBUG)
    
    # Check service status
    if args.status:
        if check_service_status():
            print("Luna CLI service is running")
            return
        else:
            print("Luna CLI service is not running")
            return
    
    # Stop service if requested
    if args.stop_service:
        if stop_service():
            print("Luna CLI service stopped")
            return
        else:
            print("Failed to stop Luna CLI service")
            sys.exit(1)
    
    # Check if service is already running
    if args.service and check_service_status():
        logger.error("Luna CLI service is already running")
        sys.exit(1)
    
    # Create and initialize Luna CLI
    cli = LunaCLI()
    config_path = Path(args.config) if args.config else None
    
    # Initialize CLI
    if await cli.initialize(config_path, args.port, args.service):
        # Update auto-start configuration if requested
        if args.auto_start or args.no_auto_start:
            config = await cli.luna_core.get_config()
            if args.auto_start:
                config["auto_start"] = True
                logger.info("Auto-start enabled")
            elif args.no_auto_start:
                config["auto_start"] = False
                logger.info("Auto-start disabled")
            await cli.luna_core.update_config(config)
        
        # Start CLI
        await cli.start()
    else:
        logger.error("Failed to initialize Luna CLI")
        sys.exit(1)

def run():
    """Run the Luna CLI."""
    try:
        # Set Windows-specific asyncio policy
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Luna CLI stopped by user")
    except Exception as e:
        logger.error(f"Luna CLI error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run()