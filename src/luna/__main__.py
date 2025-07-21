#!/usr/bin/env python3
"""
Luna Gaming Tool - Main entry point.

This module provides the main entry point for the Luna Gaming Tool,
allowing it to be run as a module with `python -m luna`.
"""

import sys
import asyncio
from pathlib import Path

from luna.setup.luna_setup_tool import LunaSetupTool
from luna.cli import run as run_cli


def main():
    """Main entry point for the Luna Gaming Tool."""
    # Import here to avoid circular imports
    import argparse
    
    parser = argparse.ArgumentParser(description="Luna Gaming Tool - Unified gaming setup and management")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Run Luna setup tool")
    setup_parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    setup_parser.add_argument("-q", "--quiet", action="store_true", help="Suppress non-essential output")
    setup_parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    setup_parser.add_argument("--config-only", action="store_true", help="Only update configuration files")
    setup_parser.add_argument("--skip-admin", action="store_true", help="Skip administrator privilege checks")
    setup_parser.add_argument("--skip-security", action="store_true", help="Skip Windows Defender exclusion setup")
    setup_parser.add_argument("--no-cleanup", action="store_true", help="Skip cleanup of temporary files")
    setup_parser.add_argument("--force", action="store_true", help="Force setup even if files already exist")
    setup_parser.add_argument("--timeout", type=int, default=300, help="Network timeout in seconds")
    setup_parser.add_argument("--luna-core-path", type=Path, help="Custom path for Luna core installation")
    setup_parser.add_argument("--legacy-greenluma-path", type=Path, help="Path to existing GreenLuma installation for migration")
    setup_parser.add_argument("--legacy-koalageddon-path", type=Path, help="Path to existing Koalageddon installation for migration")
    setup_parser.add_argument("--app-id", type=str, default="480", help="Steam App ID for Luna AppList")
    setup_parser.add_argument("--download-url", type=str, help="Custom download URL for Luna installer")
    
    # CLI command
    cli_parser = subparsers.add_parser("cli", help="Run Luna CLI backend")
    cli_parser.add_argument("--config", help="Path to Luna configuration file")
    cli_parser.add_argument("--port", type=int, default=5000, help="API server port")
    cli_parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    cli_parser.add_argument("--service", action="store_true", help="Run as a background service")
    cli_parser.add_argument("--stop-service", action="store_true", help="Stop running service")
    cli_parser.add_argument("--status", action="store_true", help="Check service status")
    cli_parser.add_argument("--auto-start", action="store_true", help="Auto-start Luna components")
    cli_parser.add_argument("--no-auto-start", action="store_true", help="Disable auto-start")
    cli_parser.add_argument("--host", default="localhost", help="Host to bind the API server to")
    
    args = parser.parse_args()
    
    # Set Windows-specific asyncio policy
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Run the appropriate command
    if args.command == "cli":
        # Run CLI backend
        run_cli()
    else:
        # Default to setup tool
        # Create and run the Luna setup tool
        setup_tool = LunaSetupTool(
            verbose=getattr(args, 'verbose', False),
            quiet=getattr(args, 'quiet', False),
            dry_run=getattr(args, 'dry_run', False),
            config_only=getattr(args, 'config_only', False),
            skip_admin=getattr(args, 'skip_admin', False),
            skip_security=getattr(args, 'skip_security', False),
            no_cleanup=getattr(args, 'no_cleanup', False),
            force=getattr(args, 'force', False),
            timeout=getattr(args, 'timeout', 300),
            luna_core_path=getattr(args, 'luna_core_path', None),
            legacy_greenluma_path=getattr(args, 'legacy_greenluma_path', None),
            legacy_koalageddon_path=getattr(args, 'legacy_koalageddon_path', None),
            app_id=getattr(args, 'app_id', "480"),
            download_url=getattr(args, 'download_url', None)
        )
        
        # Run the setup tool with asyncio
        asyncio.run(setup_tool.run())


if __name__ == "__main__":
    main()