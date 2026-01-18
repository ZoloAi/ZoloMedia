# zCLI/subsystems/zServer/zServer_modules/gunicorn_manager.py

"""
Gunicorn Subprocess Manager for zServer Production Mode

Manages Gunicorn WSGI server as a subprocess, providing:
- Automatic Gunicorn startup with proper configuration
- Subprocess health monitoring
- Graceful shutdown handling
- Log file management
"""

import subprocess
import os
import sys
from typing import Any, Optional
from pathlib import Path


class GunicornManager:
    """
    Manages Gunicorn WSGI server as a subprocess.
    
    Handles the full lifecycle of a Gunicorn process for Production mode,
    allowing zCLI to provide a seamless declarative interface where users
    just change deployment mode and zCLI handles the rest.
    
    Attributes:
        app_module: Module path for WSGI app (e.g., "app:application")
        host: Bind host address
        port: Bind port number
        workers: Number of worker processes
        logger: zCLI logger instance
        process: Subprocess instance (when running)
    """
    
    def __init__(
        self, 
        app_module: str,
        host: str = "127.0.0.1",
        port: int = 8000,
        workers: int = 4,
        logger: Optional[Any] = None
    ):
        """
        Initialize Gunicorn manager.
        
        Args:
            app_module: WSGI application module path (e.g., "wsgi:app")
            host: Bind host address (default: 127.0.0.1)
            port: Bind port number (default: 8000)
            workers: Number of worker processes (default: 4)
            logger: Logger instance for status messages
        """
        self.app_module = app_module
        self.host = host
        self.port = port
        self.workers = workers
        self.logger = logger
        self.process: Optional[subprocess.Popen] = None
    
    def start(self):
        """
        Start Gunicorn subprocess.
        
        Creates a Gunicorn process with appropriate configuration for
        production use. Logs are written to ./logs/ directory.
        
        Raises:
            RuntimeError: If Gunicorn is not installed
            OSError: If subprocess creation fails
        """
        # Ensure logs directory exists
        logs_dir = Path("./logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Build Gunicorn command
        cmd = [
            sys.executable, "-m", "gunicorn",  # Use same Python as zCLI
            "-w", str(self.workers),
            "-b", f"{self.host}:{self.port}",
            "--access-logfile", str(logs_dir / "gunicorn_access.log"),
            "--error-logfile", str(logs_dir / "gunicorn_error.log"),
            "--log-level", "info",
            "--timeout", "30",
            "--worker-class", "sync",
            self.app_module
        ]
        
        if self.logger:
            self.logger.info(f"[zServer] Starting Gunicorn: {' '.join(cmd)}")
        
        try:
            # Start Gunicorn as subprocess
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            if self.logger:
                self.logger.info(f"[zServer] Gunicorn started (PID: {self.process.pid})")
                self.logger.info(f"[zServer] Production mode: http://{self.host}:{self.port}")
        
        except FileNotFoundError:
            error_msg = (
                "[zServer] Gunicorn not found. Install with: pip install gunicorn\n"
                "Production mode requires Gunicorn for WSGI serving."
            )
            if self.logger:
                self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        except Exception as e:
            error_msg = f"[zServer] Failed to start Gunicorn: {e}"
            if self.logger:
                self.logger.error(error_msg)
            raise OSError(error_msg) from e
    
    def stop(self):
        """
        Stop Gunicorn subprocess gracefully.
        
        Sends SIGTERM to allow graceful shutdown, then waits for process
        to exit. If process doesn't exit within timeout, forces termination.
        """
        if not self.process:
            if self.logger:
                self.logger.warning("[zServer] Gunicorn not running")
            return
        
        if self.logger:
            self.logger.info("[zServer] Stopping Gunicorn...")
        
        try:
            # Graceful shutdown with SIGTERM
            self.process.terminate()
            
            # Wait for process to exit (5 second timeout)
            try:
                self.process.wait(timeout=5)
                if self.logger:
                    self.logger.info("[zServer] Gunicorn stopped gracefully")
            except subprocess.TimeoutExpired:
                # Force kill if doesn't exit gracefully
                if self.logger:
                    self.logger.warning("[zServer] Gunicorn didn't stop gracefully, forcing...")
                self.process.kill()
                self.process.wait()
                if self.logger:
                    self.logger.info("[zServer] Gunicorn stopped (forced)")
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"[zServer] Error stopping Gunicorn: {e}")
        
        finally:
            self.process = None
    
    def is_running(self) -> bool:
        """
        Check if Gunicorn subprocess is running.
        
        Returns:
            bool: True if Gunicorn is running, False otherwise
        """
        if not self.process:
            return False
        
        # Check if process has terminated
        return self.process.poll() is None
    
    def get_pid(self) -> Optional[int]:
        """
        Get Gunicorn process ID.
        
        Returns:
            int or None: Process ID if running, None otherwise
        """
        if self.process and self.is_running():
            return self.process.pid
        return None

