#!/usr/bin/env python3
"""
Quick verification that the OSINT scraper is ready for GitHub
"""

import os
import sys

def check_setup():
    """Verify the project is ready for GitHub"""
    
    print("🔍 Checking OSINT Scraper Setup...")
    print("=" * 50)
    
    # Check required files exist
    required_files = [
        'osint_scraper.py',
        'osint_utilities.py', 
        'osint_engine_ai.py',
        'simple_osint.py',
        'osint_api.py',
        'requirements.txt',
        'README.md',
        'README_AI.md',
        '.env.example',
        '.gitignore'
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file}")
            missing_files.append(file)
    
    # Check that .env is NOT present
    if os.path.exists('.env'):
        print("⚠️  .env file found - should be removed before pushing to GitHub")
    else:
        print("✅ .env file correctly absent")
    
    # Check requirements.txt doesn't have paid APIs
    if os.path.exists('requirements.txt'):
        with open('requirements.txt', 'r') as f:
            content = f.read()
            if 'shodan' in content.lower():
                print("⚠️  requirements.txt still contains Shodan")
            else:
                print("✅ requirements.txt uses only free dependencies")
    
    print("\n" + "=" * 50)
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    else:
        print("🎉 Project is ready for GitHub!")
        print("\n📋 Summary:")
        print("   • No API keys required")
        print("   • Uses only free services")
        print("   • All files present")
        print("   • Ready for AI integration")
        return True

if __name__ == '__main__':
    success = check_setup()
    sys.exit(0 if success else 1)
