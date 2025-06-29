@echo off
REM OSINT Scraper Launcher for Windows
REM This script helps launch the OSINT scraper with common options

echo Advanced OSINT Scraper
echo ======================

:menu
echo.
echo Choose an option:
echo 1. Install dependencies
echo 2. Check system requirements
echo 3. Setup tools and environment
echo 4. Run interactive investigation
echo 5. Run demo
echo 6. View help
echo 7. Exit
echo.

set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" goto install
if "%choice%"=="2" goto check
if "%choice%"=="3" goto setup
if "%choice%"=="4" goto interactive
if "%choice%"=="5" goto demo
if "%choice%"=="6" goto help
if "%choice%"=="7" goto exit
goto menu

:install
echo Installing dependencies...
python install_deps.py
pause
goto menu

:check
echo Checking system requirements...
python check_system.py
pause
goto menu

:setup
echo Setting up OSINT environment...
python setup.py
echo.
echo Installing tools...
python osint_scraper.py --setup
pause
goto menu

:interactive
echo Starting interactive investigation...
python osint_scraper.py --interactive
pause
goto menu

:demo
echo Running demo...
python demo.py
pause
goto menu

:help
echo.
echo OSINT Scraper Help
echo ==================
echo.
echo Usage: python osint_scraper.py [options]
echo.
echo Options:
echo   --setup                   Setup and install OSINT tools
echo   --interactive             Run in interactive mode
echo   --name "Full Name"        Target's full name
echo   --email "email@domain"    Target's email address
echo   --social handle1 handle2  Social media handles
echo   --address "Address"       Target's address
echo   --coordinates lat lon     Latitude and longitude
echo.
echo Examples:
echo   python osint_scraper.py --name "John Doe" --email "john@example.com"
echo   python osint_scraper.py --interactive
echo.
echo Utilities:
echo   python install_deps.py    Install all dependencies
echo   python check_system.py    Check system requirements
echo   python demo.py            Run demonstration
echo.
pause
goto menu

:exit
echo Goodbye!
exit /b 0
