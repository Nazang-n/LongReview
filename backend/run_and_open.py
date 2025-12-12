#!/usr/bin/env python
"""
Script to start the FastAPI backend and automatically open the docs in the browser.
"""

import subprocess
import webbrowser
import time
import sys

def main():
    """Start uvicorn and open docs in browser."""
    
    # Start uvicorn server
    print("Starting FastAPI backend server...")
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait a bit for the server to start
    print("Waiting for server to start...")
    time.sleep(3)
    
    # Open browser to docs
    docs_url = "http://127.0.0.1:8000/docs"
    print(f"Opening {docs_url}...")
    webbrowser.open(docs_url)
    
    print("\nBackend is running. Press Ctrl+C to stop.")
    print(f"API Docs: {docs_url}")
    print("Health check: http://127.0.0.1:8000/health")
    print("ReDoc: http://127.0.0.1:8000/redoc")
    
    try:
        process.wait()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    main()
