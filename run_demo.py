#!/usr/bin/env python3
"""
FinanceAI Quick Start
Simple script to start the API server and load sample data
"""

import subprocess
import sys
import os

def main():
    print("🚀 Starting FinanceAI")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not os.path.exists("app/main.py"):
        print("❌ Error: Please run this script from the project root directory")
        sys.exit(1)
    
    print("📡 Starting API server...")
    print("🔗 API will be available at: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("📱 Frontend: Open frontend/index.html in your browser")
    print("\n🛑 Press Ctrl+C to stop the server")
    print("=" * 40)
    
    try:
        # Start the server
        subprocess.run([
            sys.executable, "-m", "uvicorn", "app.main:app", 
            "--host", "0.0.0.0", "--port", "8000", "--reload"
        ])
    except KeyboardInterrupt:
        print("\n✅ Server stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure you've installed requirements: pip install -r requirements.txt")

if __name__ == "__main__":
    main()