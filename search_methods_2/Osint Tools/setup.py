#!/usr/bin/env python3
"""
Setup script for OSINT Scraper
Installs dependencies and sets up the environment
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description=""):
    """Run a command and handle errors"""
    print(f"Running: {description or command}")
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False

def install_python_requirements():
    """Install Python requirements"""
    print("Installing Python requirements...")
    return run_command(f"{sys.executable} -m pip install -r requirements.txt", 
                      "Installing Python packages")

def check_git():
    """Check if git is installed"""
    try:
        subprocess.run(["git", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Git is not installed. Please install Git first.")
        return False

def setup_directories():
    """Create necessary directories"""
    directories = ["tools", "output", "logs"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"Created directory: {directory}")

def create_env_file():
    """Create .env file from example if it doesn't exist"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        env_file.write_text(env_example.read_text())
        print("Created .env file from example. Please edit it with your API keys.")
    else:
        print(".env file already exists or .env.example not found")

def main():
    """Main setup function"""
    print("Setting up OSINT Scraper...")
    print("=" * 50)
    
    # Check git
    if not check_git():
        return False
    
    # Setup directories
    setup_directories()
    
    # Install Python requirements
    if not install_python_requirements():
        print("Failed to install Python requirements")
        return False
    
    # Create .env file
    create_env_file()
    
    print("\n" + "=" * 50)
    print("Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit the .env file with your API keys")
    print("2. Run: python osint_scraper.py --setup")
    print("3. Start investigating: python osint_scraper.py --interactive")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
