#!/usr/bin/env python3
"""
Quick dependency installer for OSINT Scraper
This script will install all required dependencies
"""

import subprocess
import sys
import os
from pathlib import Path

def install_package(package):
    """Install a Python package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    """Install all required dependencies"""
    print("Installing OSINT Scraper dependencies...")
    print("=" * 50)
    
    # Core dependencies
    dependencies = [
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0", 
        "lxml>=4.9.0",
        "selenium>=4.15.0",
        "webdriver-manager>=4.0.0",
        "python-dotenv>=1.0.0",
        "colorama>=0.4.6",
        "tabulate>=0.9.0",
        "pyyaml>=6.0.1",
        "dnspython>=2.4.0",
        "python-whois>=0.9.0",
        "shodan>=1.30.0"
    ]
    
    failed_installs = []
    
    for dep in dependencies:
        print(f"Installing {dep}...")
        if install_package(dep):
            print(f"✓ {dep} installed successfully")
        else:
            print(f"✗ Failed to install {dep}")
            failed_installs.append(dep)
    
    print("\n" + "=" * 50)
    
    if failed_installs:
        print("❌ Some packages failed to install:")
        for pkg in failed_installs:
            print(f"  - {pkg}")
        print("\nTry installing them manually with:")
        print(f"pip install {' '.join(failed_installs)}")
        return False
    else:
        print("✅ All dependencies installed successfully!")
        print("\nNext steps:")
        print("1. Copy .env.example to .env and add your API keys")
        print("2. Run: python osint_scraper.py --setup")
        print("3. Start investigating: python osint_scraper.py --interactive")
        return True

if __name__ == "__main__":
    success = main()
    input("\nPress Enter to continue...")
    sys.exit(0 if success else 1)
