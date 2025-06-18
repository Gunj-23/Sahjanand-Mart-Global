#!/usr/bin/env python3
"""
Quick start script for Sahjanand Mart
This script will install and run the application automatically.
"""

import subprocess
import sys
import os
import webbrowser
import time
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed!")
        print(f"Error: {e.stderr}")
        return False

def main():
    """Main installation and setup process."""
    print("🚀 Welcome to Sahjanand Mart Setup!")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("setup.py").exists():
        print("❌ Error: setup.py not found. Please run this script from the project root directory.")
        sys.exit(1)
    
    # Install the package in development mode
    if not run_command("pip install -e .", "Installing Sahjanand Mart"):
        sys.exit(1)
    
    # Initialize database
    if not run_command("sahjanand-mart init-db", "Initializing database"):
        sys.exit(1)
    
    # Create admin user
    print("🔑 Creating admin user...")
    admin_command = 'echo admin | echo admin123 | sahjanand-mart create-admin --username admin --password admin123'
    try:
        subprocess.run("sahjanand-mart create-admin --username admin --password admin123", 
                      shell=True, check=True, input="admin\nadmin123\n", text=True)
        print("✅ Admin user created successfully!")
        print("   Username: admin")
        print("   Password: admin123")
    except subprocess.CalledProcessError:
        print("⚠️  Admin user creation skipped (may already exist)")
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Quick Start Guide:")
    print("   1. The application will start automatically")
    print("   2. Login with username: admin, password: admin123")
    print("   3. Start using the POS system!")
    
    print("\n🌐 Starting Sahjanand Mart...")
    
    # Start the application
    try:
        subprocess.run("sahjanand-mart run --open-browser", shell=True, check=True)
    except KeyboardInterrupt:
        print("\n👋 Sahjanand Mart stopped. Thank you for using our POS system!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start application: {e}")
        print("\n🔧 Manual start command:")
        print("   sahjanand-mart run --open-browser")

if __name__ == "__main__":
    main()