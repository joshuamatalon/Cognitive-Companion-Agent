#!/usr/bin/env python3
"""
Quick Start Script for Cognitive Companion Agent
Double-click this file to run the application!
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def main():
    print("🧠 Cognitive Companion Agent - Quick Start")
    print("=" * 50)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print(f"📁 Working directory: {script_dir}")
    
    # Check if streamlit is installed
    try:
        import streamlit
        print("✅ Streamlit found")
    except ImportError:
        print("❌ Streamlit not installed!")
        print("📦 Installing Streamlit...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
            print("✅ Streamlit installed successfully")
        except subprocess.CalledProcessError:
            print("❌ Failed to install Streamlit")
            input("Press Enter to exit...")
            return
    
    # Check if app.py exists
    if not Path("app.py").exists():
        print("❌ app.py not found in current directory!")
        input("Press Enter to exit...")
        return
    
    print("🚀 Starting Cognitive Companion Agent...")
    print("🌐 Your browser will open automatically")
    print("⛔ Press Ctrl+C in this window to stop the application")
    print("")
    
    try:
        # Start streamlit
        process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.headless", "false"
        ])
        
        # Wait a bit for the server to start
        time.sleep(3)
        
        # Open browser
        webbrowser.open("http://localhost:8501")
        
        # Wait for the process to complete
        process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping application...")
        process.terminate()
        
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()