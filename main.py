#!/usr/bin/env python3
"""
ChaseHound Launcher Script
==========================

Simple script to launch the ChaseHound Streamlit app with its backend server.
This script starts both the backend server and the Streamlit app.

Usage:
    python main.py
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Optional


class Colors:
    """Color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class ChaseHoundLauncher:
    """Main launcher class for ChaseHound application."""
    
    def __init__(self):
        """Initialize the launcher."""
        # Optional color support for Windows terminals
        try:
            if os.name == "nt":
                import colorama  # type: ignore
                colorama.just_fix_windows_console()
        except Exception:
            pass
        
        self.backend_process: Optional[subprocess.Popen] = None
        self.streamlit_process: Optional[subprocess.Popen] = None
        self.backend_url = "http://localhost:8000"
        self.streamlit_url = "http://localhost:8501"
        
        # Script paths
        self.backend_script = Path(__file__).parent / "src_CD" / "backendCDServer.py"
        self.streamlit_script = Path(__file__).parent / "src_CD" / "chaseHoundStreamLitApp.py"
        
        # Required packages
        self.required_packages = ['streamlit', 'flask', 'flask-cors', 'pandas', 'yfinance', 'requests']
    
    def print_colored(self, message: str, color: str = Colors.ENDC):
        """Print a colored message to the terminal."""
        print(f"{color}{message}{Colors.ENDC}")
    
    def print_success(self, message: str):
        """Print a success message in green."""
        self.print_colored(f"SUCCESS: {message}", Colors.GREEN)
    
    def print_error(self, message: str):
        """Print an error message in red."""
        self.print_colored(f"ERROR: {message}", Colors.RED)
    
    def print_warning(self, message: str):
        """Print a warning message in yellow."""
        self.print_colored(f"WARNING: {message}", Colors.YELLOW)
    
    def print_info(self, message: str):
        """Print an info message in blue."""
        self.print_colored(f"INFO: {message}", Colors.BLUE)
    
    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed."""
        missing_packages = []
        
        for package in self.required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            self.print_error(f"Missing required packages: {', '.join(missing_packages)}")
            return False
        
        self.print_success("All dependencies are installed")
        return True
    
    def install_dependencies(self) -> bool:
        """Install dependencies from requirements.txt."""
        requirements_file = Path(__file__).parent / "requirements.txt"
        
        if not requirements_file.exists():
            self.print_error(f"Requirements file not found: {requirements_file}")
            return False
        
        self.print_info("Installing dependencies from requirements.txt...")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.returncode == 0:
                self.print_success("Dependencies installed successfully")
                return True
            else:
                self.print_error(f"Failed to install dependencies: {result.stderr}")
                return False
                
        except subprocess.CalledProcessError as e:
            self.print_error(f"Failed to install dependencies: {e.stderr}")
            return False
        except Exception as e:
            self.print_error(f"Unexpected error during installation: {e}")
            return False
    
    def check_and_install_dependencies(self) -> bool:
        """Check dependencies and install them if missing."""
        if self.check_dependencies():
            return True
        
        self.print_warning("Some dependencies are missing. Attempting to install...")
        
        if not self.install_dependencies():
            self.print_error("Failed to install dependencies")
            self.print_info("Please manually install dependencies with: pip install -r requirements.txt")
            return False
        
        # Verify installation was successful
        if not self.check_dependencies():
            self.print_error("Dependencies installation completed but some packages are still missing")
            return False
        
        return True
    
    def wait_for_backend(self, timeout: int = 30) -> bool:
        """Wait for the backend server to be reachable.
        Since the backend does not expose /health, any HTTP response indicates readiness.
        """
        # Lazy import so the script can show a better error if requests is missing
        try:
            import requests  # type: ignore
        except ImportError:
            self.print_error("Python package 'requests' is required. Please install it: pip install requests")
            return False
        
        self.print_info(f"Waiting for backend server at {self.backend_url}...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                resp = requests.get(self.backend_url, timeout=2)
                # Any HTTP response (even 404/405/500) means the server is up and responding
                if isinstance(resp.status_code, int):
                    self.print_success("Backend server is reachable")
                    return True
            except Exception:
                pass
            time.sleep(1)
        
        self.print_error(f"Backend server did not start within {timeout} seconds")
        return False
    
    def start_backend_server(self) -> bool:
        """Start the backend server in a separate process."""
        if not self.backend_script.exists():
            self.print_error(f"Backend server script not found: {self.backend_script}")
            return False
        
        try:
            # Inherit stdout/stderr to avoid PIPE buffer deadlocks and show logs live
            self.backend_process = subprocess.Popen(
                [sys.executable, str(self.backend_script)],
            )
            self.print_info("Backend server process started")
            return True
        except Exception as e:
            self.print_error(f"Failed to start backend server: {e}")
            return False
    
    def start_streamlit_app(self) -> bool:
        """Start the Streamlit app."""
        if not self.streamlit_script.exists():
            self.print_error(f"Streamlit app script not found: {self.streamlit_script}")
            return False
        
        try:
            # Inherit stdout/stderr to avoid PIPE buffer deadlocks and show logs live
            self.streamlit_process = subprocess.Popen(
                [sys.executable, "-m", "streamlit", "run", str(self.streamlit_script)],
            )
            self.print_info("Streamlit app process started")
            return True
        except Exception as e:
            self.print_error(f"Failed to start Streamlit app: {e}")
            return False
    
    def _terminate_process(self, proc: Optional[subprocess.Popen], name: str):
        if not proc:
            return
        try:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
            self.print_info(f"{name} stopped")
        except Exception:
            self.print_warning(f"Failed to gracefully stop {name}")
    
    def stop_processes(self):
        """Stop all running processes."""
        self._terminate_process(self.streamlit_process, "Streamlit app")
        self._terminate_process(self.backend_process, "Backend server")
    
    def monitor_processes(self):
        """Monitor running processes and handle shutdown."""
        try:
            while True:
                if self.backend_process and self.backend_process.poll() is not None:
                    self.print_error("Backend server process stopped unexpectedly")
                    break
                if self.streamlit_process and self.streamlit_process.poll() is not None:
                    self.print_error("Streamlit app process stopped unexpectedly")
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            self.print_info("\nShutting down ChaseHound...")
        finally:
            self.stop_processes()
            self.print_success("ChaseHound shutdown complete")
    
    def launch(self):
        """Main method to launch ChaseHound."""
        self.print_colored("ChaseHound Launcher", Colors.BOLD)
        self.print_colored("=" * 50, Colors.BOLD)
        
        if not self.check_and_install_dependencies():
            return False
        if not self.start_backend_server():
            return False
        if not self.wait_for_backend():
            self.print_error("Backend server failed to start properly")
            self.stop_processes()
            return False
        if not self.start_streamlit_app():
            self.print_error("Streamlit app failed to start")
            self.stop_processes()
            return False
        
        self.print_success("ChaseHound is now running!")
        self.print_info(f"Backend server: {self.backend_url}")
        self.print_info(f"Streamlit app: {self.streamlit_url}")
        self.print_info("Press Ctrl+C to stop all services")
        
        self.monitor_processes()
        return True


def main():
    """Main function to launch ChaseHound."""
    launcher = ChaseHoundLauncher()
    success = launcher.launch()
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()