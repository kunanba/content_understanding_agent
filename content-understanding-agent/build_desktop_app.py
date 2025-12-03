"""
Script to launch Streamlit app for PyInstaller packaging.
This is the entry point for the desktop application.
"""
import os
import sys
import subprocess
import socket
from pathlib import Path

def find_free_port():
    """Find an available port for Streamlit."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

def main():
    """Launch Streamlit app."""
    # Get the directory where the executable is located
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        app_dir = Path(sys._MEIPASS)
    else:
        # Running as script
        app_dir = Path(__file__).parent
    
    # Change to app directory
    os.chdir(app_dir)
    
    # Find available port
    port = find_free_port()
    
    # Launch Streamlit
    streamlit_cmd = [
        sys.executable,
        "-m", "streamlit",
        "run",
        str(app_dir / "app.py"),
        "--server.port", str(port),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ]
    
    print(f"Starting Content Understanding Agent on port {port}...")
    print(f"Open your browser to: http://localhost:{port}")
    
    subprocess.run(streamlit_cmd)

if __name__ == "__main__":
    main()
