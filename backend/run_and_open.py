#!/usr/bin/env python
"""
Script to start the FastAPI backend and automatically open the docs in the browser.
"""

import subprocess
import webbrowser
import time
import sys
import socket

def get_local_ip():
    """Get the local IP address of the machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def main():
    """Start uvicorn and open docs in browser."""
    
    # Start uvicorn server on 0.0.0.0 (accessible from other machines)
    print("Starting FastAPI backend server...")
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait a bit for the server to start
    print("Waiting for server to start...")
    time.sleep(3)
    
    # Get local IP for access from other machines
    local_ip = get_local_ip()
    docs_url = "http://127.0.0.1:8000/docs"
    remote_url = f"http://{local_ip}:8000/docs"
    
    # Try to open browser
    print(f"Attempting to open {docs_url}...")
    try:
        webbrowser.open(docs_url)
        print("Browser opened successfully!")
    except Exception as e:
        print(f"Could not automatically open browser: {e}")
    
    print("\n" + "="*60)
    print("Backend is running. Press Ctrl+C to stop.")
    print("="*60)
    print(f"\nLocal access (this PC):")
    print(f"  API Docs: {docs_url}")
    print(f"  Health check: http://127.0.0.1:8000/health")
    print(f"  ReDoc: http://127.0.0.1:8000/redoc")
    print(f"\nRemote access (other PCs on network):")
    print(f"  API Docs: {remote_url}")
    print(f"  Health check: http://{local_ip}:8000/health")
    print(f"  ReDoc: http://{local_ip}:8000/redoc")
    print("="*60 + "\n")
    
    try:
        process.wait()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    main()
