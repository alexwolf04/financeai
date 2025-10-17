#!/usr/bin/env python3
"""
FinanceAI Demo Runner
Starts the API server and loads sample data for demonstration
"""

import subprocess
import time
import requests
import sys
import os
from data.sample_transactions import upload_sample_data

def check_api_health(max_retries=30):
    """Check if the API is running and healthy"""
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:8000/health")
            if response.status_code == 200:
                print("✅ API is healthy!")
                return True
        except requests.exceptions.ConnectionError:
            pass
        
        print(f"⏳ Waiting for API to start... ({i+1}/{max_retries})")
        time.sleep(2)
    
    return False

def main():
    print("🚀 Starting FinanceAI Demo")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("app/main.py"):
        print("❌ Error: Please run this script from the project root directory")
        sys.exit(1)
    
    # Start the API server
    print("📡 Starting API server...")
    try:
        # Start the server in the background
        server_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "app.main:app", 
            "--host", "0.0.0.0", "--port", "8000", "--reload"
        ])
        
        # Wait for the server to start
        if not check_api_health():
            print("❌ Failed to start API server")
            server_process.terminate()
            sys.exit(1)
        
        # Load sample data
        print("📊 Loading sample data...")
        try:
            upload_sample_data()
            print("✅ Sample data loaded successfully!")
        except Exception as e:
            print(f"⚠️  Warning: Failed to load sample data: {e}")
            print("You can load it manually later using the web interface")
        
        print("\n🎉 FinanceAI Demo is ready!")
        print("=" * 50)
        print("📱 Frontend: http://localhost:3000 (if using Docker)")
        print("🔗 API: http://localhost:8000")
        print("📚 API Docs: http://localhost:8000/docs")
        print("💾 Sample User ID: demo_user")
        print("\n🛑 Press Ctrl+C to stop the server")
        
        # Keep the script running
        try:
            server_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping server...")
            server_process.terminate()
            server_process.wait()
            print("✅ Server stopped")
            
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()