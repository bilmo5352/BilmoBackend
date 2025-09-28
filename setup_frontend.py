#!/usr/bin/env python3
"""
Setup script for React frontend
"""

import os
import subprocess
import sys

def run_command(command, cwd=None):
    """Run a command and return the result"""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print("🚀 Setting up React Frontend for E-commerce Scraper")
    print("=" * 60)
    
    # Check if Node.js is installed
    print("📋 Checking Node.js installation...")
    success, stdout, stderr = run_command("node --version")
    if not success:
        print("❌ Node.js is not installed. Please install Node.js first:")
        print("   Download from: https://nodejs.org/")
        return
    
    print(f"✅ Node.js version: {stdout.strip()}")
    
    # Check if npm is installed
    print("📋 Checking npm installation...")
    success, stdout, stderr = run_command("npm --version")
    if not success:
        print("❌ npm is not installed. Please install npm first.")
        return
    
    print(f"✅ npm version: {stdout.strip()}")
    
    # Navigate to frontend directory
    frontend_dir = "frontend"
    if not os.path.exists(frontend_dir):
        print(f"❌ Frontend directory '{frontend_dir}' not found.")
        return
    
    print(f"📁 Navigating to {frontend_dir} directory...")
    os.chdir(frontend_dir)
    
    # Install dependencies
    print("📦 Installing React dependencies...")
    success, stdout, stderr = run_command("npm install")
    if not success:
        print(f"❌ Failed to install dependencies: {stderr}")
        return
    
    print("✅ Dependencies installed successfully!")
    
    print("\n🎉 Frontend setup completed!")
    print("\n📋 Next steps:")
    print("1. Make sure your Flask API is running on http://localhost:5000")
    print("2. Start the React frontend with: npm start")
    print("3. Open http://localhost:3000 in your browser")
    print("\n💡 The frontend will automatically connect to your Flask API")
    print("   and display search results from MongoDB!")

if __name__ == "__main__":
    main()


