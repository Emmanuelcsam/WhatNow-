#!/usr/bin/env python3
"""
OSINT Scraper System Check
Verifies all dependencies and system requirements
"""

import sys
import subprocess
import importlib
from pathlib import Path

def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 7:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} (Compatible)")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} (Requires Python 3.7+)")
        return False

def check_package(package_name, import_name=None):
    """Check if a package is installed and importable"""
    if import_name is None:
        import_name = package_name
    
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, '__version__', 'Unknown')
        print(f"✓ {package_name}: {version}")
        return True
    except ImportError:
        print(f"✗ {package_name}: Not installed")
        return False

def check_git():
    """Check if git is installed"""
    try:
        result = subprocess.run(['git', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Git: {result.stdout.strip()}")
            return True
        else:
            print("✗ Git: Not working properly")
            return False
    except FileNotFoundError:
        print("✗ Git: Not installed")
        return False

def check_directories():
    """Check if required directories exist"""
    base_dir = Path(__file__).parent
    required_dirs = ['tools', 'output', 'logs']
    
    all_exist = True
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if dir_path.exists():
            print(f"✓ Directory {dir_name}: Exists")
        else:
            print(f"✗ Directory {dir_name}: Missing")
            all_exist = False
    
    return all_exist

def main():
    """Run system check"""
    print("OSINT Scraper System Check")
    print("=" * 40)
    
    checks = []
    
    # Python version
    print("\nPython Version:")
    checks.append(check_python_version())
    
    # Git installation
    print("\nGit:")
    checks.append(check_git())
    
    # Python packages
    print("\nPython Packages:")
    packages = [
        ('requests', 'requests'),
        ('beautifulsoup4', 'bs4'),
        ('lxml', 'lxml'),
        ('selenium', 'selenium'),
        ('webdriver-manager', 'webdriver_manager'),
        ('python-dotenv', 'dotenv'),
        ('colorama', 'colorama'),
        ('tabulate', 'tabulate'),
        ('pyyaml', 'yaml'),
        ('dnspython', 'dns'),
        ('python-whois', 'whois'),
        ('shodan', 'shodan')
    ]
    
    for package_name, import_name in packages:
        checks.append(check_package(package_name, import_name))
    
    # Directories
    print("\nDirectories:")
    checks.append(check_directories())
    
    # Environment file
    print("\nConfiguration:")
    env_file = Path('.env')
    if env_file.exists():
        print("✓ .env file: Exists")
        checks.append(True)
    else:
        print("⚠ .env file: Missing (copy from .env.example)")
        checks.append(False)
    
    # Summary
    print("\n" + "=" * 40)
    passed = sum(checks)
    total = len(checks)
    
    if passed == total:
        print(f"✅ All checks passed ({passed}/{total})")
        print("\nYour system is ready to run OSINT Scraper!")
        print("Run: python osint_scraper.py --interactive")
    else:
        print(f"❌ {total - passed} checks failed ({passed}/{total})")
        print("\nTo fix issues:")
        print("1. Install missing packages: python install_deps.py")
        print("2. Create directories: python osint_scraper.py --setup")
        print("3. Copy .env.example to .env and configure API keys")

if __name__ == "__main__":
    main()
    input("\nPress Enter to continue...")
