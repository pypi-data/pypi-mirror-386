#!/usr/bin/env python3
"""
JDCat CLI Entry Point

This module provides the main entry point for the jdcat command-line tool.
It uses typer for command-line interface and uvicorn to start the FastAPI server.
"""

import sys
import os
import webbrowser
import threading
import time
from typing import Optional
import typer
import uvicorn
from pathlib import Path

# Add the current package to the Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

app = typer.Typer(
    add_completion=False,
    help="JDCat - Sensitive Check Local Service CLI Tool",
)

@app.callback()
def main_callback(
    version: Optional[bool] = typer.Option(
        None, "--version", help="Show version and exit", is_eager=True
    ),
):
    """
    JDCat CLI - Local proxy service for sensitive data detection
    """
    if version:
        from . import __version__
        typer.echo(f"jdcat {__version__}")
        raise typer.Exit()

@app.command()
def start(
    port: int = typer.Option(17866, "--port", help="Port to run the service on"),
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind the service to"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload for development"),
    open_browser: bool = typer.Option(True, "--open-browser/--no-open-browser", help="Automatically open browser after service starts"),
    browser_url: str = typer.Option("http://aq.jdtest.net:8007/", "--browser-url", help="URL to open in browser"),
):
    """
    Start the JDCat local service
    """
    typer.echo(f"Starting JDCat service on {host}:{port}")
    
    def open_browser_delayed():
        """Open browser after a short delay to ensure service is ready"""
        time.sleep(2)  # Wait 2 seconds for service to start
        try:
            typer.echo(f"Opening browser: {browser_url}")
            webbrowser.open(browser_url)
        except Exception as e:
            typer.echo(f"Warning: Failed to open browser: {e}", err=True)
    
    try:
        # Import the FastAPI app from sensitive_check_local
        from sensitive_check_local.api import app as fastapi_app
        
        # Start browser opening in background if requested
        if open_browser:
            browser_thread = threading.Thread(target=open_browser_delayed, daemon=True)
            browser_thread.start()
        
        # Start the uvicorn server
        uvicorn.run(
            fastapi_app,
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except ImportError as e:
        typer.echo(f"Error: Failed to import sensitive_check_local module: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error: Failed to start service: {e}", err=True)
        raise typer.Exit(1)

@app.command()
def stop():
    """
    Stop the JDCat local service
    """
    typer.echo("Stopping JDCat service...")
    # Note: This is a placeholder. In a real implementation, you might want to
    # implement proper service management (e.g., using PID files or signals)
    typer.echo("Service stop command received. Please use Ctrl+C to stop the running service.")

@app.command()
def status():
    """
    Check the status of JDCat local service
    """
    typer.echo("Checking JDCat service status...")
    # Note: This is a placeholder. In a real implementation, you might want to
    # check if the service is running on the configured port
    typer.echo("Status check not yet implemented. Use 'jdcat start' to run the service.")

def main():
    """
    Main entry point for the jdcat command
    """
    app()

if __name__ == "__main__":
    main()