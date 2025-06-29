#!/usr/bin/env python3
"""
unified_installer.py - Complete installation, setup, and execution script
This script handles the entire setup process and runs all components
"""
import os
import sys
import subprocess
import platform
import json
import time
import logging
from pathlib import Path
import shutil
import venv
import argparse
from datetime import datetime
import traceback
import socket
import urllib.request
import importlib.util

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Configure logging
def setup_logging():
    """Setup logging configuration"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"installation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

class SystemChecker:
    """Check system requirements and environment"""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.system_info = {
            'platform': platform.system(),
            'python_version': sys.version,
            'architecture': platform.machine()
        }
    
    def check_python_version(self):
        """Check if Python version meets requirements"""
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            self.issues.append(f"Python 3.8+ required, found {version.major}.{version.minor}")
            return False
        
        logger.info(f"✓ Python {version.major}.{version.minor}.{version.micro} detected")
        return True
    
    def check_internet_connection(self):
        """Check internet connectivity"""
        try:
            urllib.request.urlopen('http://google.com', timeout=5)
            logger.info("✓ Internet connection available")
            return True
        except:
            self.issues.append("No internet connection detected")
            return False
    
    def check_disk_space(self):
        """Check available disk space"""
        try:
            import shutil
            stat = shutil.disk_usage(".")
            free_gb = stat.free / (1024**3)
            
            if free_gb < 1:
                self.issues.append(f"Insufficient disk space: {free_gb:.2f}GB free (need 1GB+)")
                return False
            
            logger.info(f"✓ Disk space available: {free_gb:.2f}GB")
            return True
        except:
            self.warnings.append("Could not check disk space")
            return True
    
    def check_system_dependencies(self):
        """Check for system-level dependencies"""
        dependencies = {
            'git': 'Git version control',
            'curl': 'HTTP client (optional)',
            'redis-cli': 'Redis cache (optional)'
        }
        
        for cmd, desc in dependencies.items():
            if shutil.which(cmd):
                logger.info(f"✓ {desc} found")
            else:
                if cmd == 'redis-cli':
                    self.warnings.append(f"{desc} not found - will use disk cache")
                else:
                    self.warnings.append(f"{desc} not found")
    
    def check_ports(self):
        """Check if required ports are available"""
        ports_to_check = [
            (5000, "Flask web server"),
            (6379, "Redis cache server")
        ]
        
        for port, service in ports_to_check:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            
            if result == 0:
                if port == 6379:
                    logger.info(f"✓ Port {port} in use - assuming {service} is running")
                else:
                    self.warnings.append(f"Port {port} already in use ({service})")
            else:
                logger.info(f"✓ Port {port} available for {service}")
    
    def run_all_checks(self):
        """Run all system checks"""
        print(f"\n{Colors.HEADER}{'='*60}")
        print("SYSTEM REQUIREMENTS CHECK")
        print(f"{'='*60}{Colors.ENDC}\n")
        
        checks = [
            ("Python Version", self.check_python_version),
            ("Internet Connection", self.check_internet_connection),
            ("Disk Space", self.check_disk_space),
            ("System Dependencies", self.check_system_dependencies),
            ("Network Ports", self.check_ports)
        ]
        
        all_passed = True
        for check_name, check_func in checks:
            try:
                print(f"Checking {check_name}...", end=" ")
                result = check_func()
                if result is False:
                    all_passed = False
                    print(f"{Colors.FAIL}FAILED{Colors.ENDC}")
                else:
                    print(f"{Colors.OKGREEN}OK{Colors.ENDC}")
            except Exception as e:
                logger.error(f"Check {check_name} error: {e}")
                self.warnings.append(f"{check_name} check error: {e}")
        
        # Report issues
        if self.issues:
            print(f"\n{Colors.FAIL}Critical Issues:{Colors.ENDC}")
            for issue in self.issues:
                print(f"  • {issue}")
        
        if self.warnings:
            print(f"\n{Colors.WARNING}Warnings:{Colors.ENDC}")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        return all_passed

class DependencyInstaller:
    """Install and manage Python dependencies"""
    
    def __init__(self):
        self.venv_path = Path("venv")
        self.pip_cmd = None
        self.python_cmd = None
    
    def create_virtual_environment(self):
        """Create Python virtual environment"""
        print(f"\n{Colors.HEADER}Creating virtual environment...{Colors.ENDC}")
        
        try:
            if self.venv_path.exists():
                logger.info("Virtual environment already exists")
            else:
                venv.create(self.venv_path, with_pip=True)
                logger.info("✓ Virtual environment created")
            
            # Set pip and python commands
            if platform.system() == "Windows":
                self.pip_cmd = self.venv_path / "Scripts" / "pip.exe"
                self.python_cmd = self.venv_path / "Scripts" / "python.exe"
            else:
                self.pip_cmd = self.venv_path / "bin" / "pip"
                self.python_cmd = self.venv_path / "bin" / "python"
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create virtual environment: {e}")
            return False
    
    def upgrade_pip(self):
        """Upgrade pip to latest version"""
        try:
            subprocess.run([str(self.pip_cmd), "install", "--upgrade", "pip"], check=True)
            logger.info("✓ Pip upgraded")
            return True
        except:
            logger.warning("Could not upgrade pip")
            return True
    
    def install_requirements(self):
        """Install Python requirements"""
        print(f"\n{Colors.HEADER}Installing Python dependencies...{Colors.ENDC}")
        
        # Core requirements
        core_requirements = [
            # Flask and web framework
            "Flask>=2.3.3",
            "Flask-WTF>=1.1.1",
            "Flask-CORS>=4.0.0",
            "Flask-Limiter>=3.5.0",
            "Werkzeug>=2.3.7",
            
            # Web scraping
            "requests>=2.31.0",
            "beautifulsoup4>=4.12.2",
            "lxml>=4.9.3",
            "aiohttp>=3.8.5",
            
            # Data processing and NLP
            "nltk>=3.8.1",
            "spacy>=3.6.1",
            "textblob>=0.17.1",
            "yake>=0.4.8",
            "scikit-learn>=1.3.0",
            "numpy>=1.25.2",
            "pandas>=2.1.0",
            
            # Location and mapping
            "geocoder>=1.38.1",
            "geopy>=2.4.0",
            "folium>=0.14.0",
            "pytz>=2023.3",
            "timezonefinder>=6.2.0",
            
            # Caching
            "redis>=5.0.0",
            "diskcache>=5.6.3",
            
            # Utilities
            "python-dotenv>=1.0.0",
            "icalendar>=5.0.7"
        ]
        
        # Optional AI requirements
        optional_requirements = [
            "openai>=0.28.0",
            "transformers>=4.33.2",
            "sentence-transformers>=2.2.2",
            "torch>=2.0.1",
            "ipinfo>=4.4.3"
        ]
        
        failed_packages = []
        
        # Install core requirements
        for package in core_requirements:
            try:
                print(f"Installing {package}...", end=" ")
                subprocess.run(
                    [str(self.pip_cmd), "install", package],
                    check=True,
                    capture_output=True
                )
                print(f"{Colors.OKGREEN}OK{Colors.ENDC}")
            except subprocess.CalledProcessError:
                print(f"{Colors.FAIL}FAILED{Colors.ENDC}")
                failed_packages.append(package)
        
        # Install optional requirements
        print(f"\n{Colors.HEADER}Installing optional dependencies...{Colors.ENDC}")
        for package in optional_requirements:
            try:
                print(f"Installing {package}...", end=" ")
                subprocess.run(
                    [str(self.pip_cmd), "install", package],
                    check=True,
                    capture_output=True,
                    timeout=300  # 5 minute timeout for large packages
                )
                print(f"{Colors.OKGREEN}OK{Colors.ENDC}")
            except:
                print(f"{Colors.WARNING}SKIPPED{Colors.ENDC}")
                logger.warning(f"Optional package {package} skipped")
        
        if failed_packages:
            logger.error(f"Failed to install: {', '.join(failed_packages)}")
            return False
        
        return True
    
    def download_nlp_data(self):
        """Download required NLP data"""
        print(f"\n{Colors.HEADER}Downloading NLP data...{Colors.ENDC}")
        
        # NLTK data
        try:
            import nltk
            nltk_data = [
                'punkt', 'stopwords', 'wordnet', 
                'averaged_perceptron_tagger', 'maxent_ne_chunker', 
                'words', 'vader_lexicon'
            ]
            
            for data in nltk_data:
                print(f"Downloading NLTK {data}...", end=" ")
                nltk.download(data, quiet=True)
                print(f"{Colors.OKGREEN}OK{Colors.ENDC}")
                
        except Exception as e:
            logger.warning(f"NLTK data download error: {e}")
        
        # spaCy model
        try:
            print("Downloading spaCy model...", end=" ")
            subprocess.run(
                [str(self.python_cmd), "-m", "spacy", "download", "en_core_web_sm"],
                check=True,
                capture_output=True
            )
            print(f"{Colors.OKGREEN}OK{Colors.ENDC}")
        except:
            print(f"{Colors.WARNING}SKIPPED{Colors.ENDC}")
            logger.warning("spaCy model download skipped")

class ProjectSetup:
    """Setup project structure and configuration"""
    
    def __init__(self):
        self.directories = [
            'data', 'data/cache', 'data/logs', 'data/temp',
            'static', 'static/css', 'static/js', 'static/images',
            'templates', 'logs', 'config'
        ]
    
    def create_directories(self):
        """Create required directories"""
        print(f"\n{Colors.HEADER}Setting up project structure...{Colors.ENDC}")
        
        for directory in self.directories:
            path = Path(directory)
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✓ Created {directory}")
    
    def create_env_file(self):
        """Create .env configuration file"""
        env_content = """# Event Discovery App Configuration

# API Keys (Optional - leave blank to use free services only)
MEETUP_API_KEY=
OPENAI_API_KEY=
HUGGINGFACE_API_KEY=
IPINFO_TOKEN=

# Flask Configuration
SECRET_KEY=your_secret_key_here_change_this
DEBUG=False
HOST=0.0.0.0
PORT=5000

# Security Settings
ENABLE_RATE_LIMITING=True
REQUESTS_PER_MINUTE=60
MAX_SEARCH_TIME=60
CACHE_EXPIRY_HOURS=24

# Event Settings
SEARCH_RADIUS_MILES=25
TIME_WINDOW_HOURS=168
MAX_EVENTS=50

# AI Settings
ENABLE_AI=False
AI_PROVIDER=local
INTEREST_EXTRACTION_CONFIDENCE=0.6
MAX_INTERESTS_TO_EXTRACT=20

# Paths
DATA_DIR=./data
CACHE_DIR=./data/cache
LOGS_DIR=./logs
"""
        
        env_path = Path(".env")
        if not env_path.exists():
            env_path.write_text(env_content)
            logger.info("✓ Created .env file")
            print(f"{Colors.WARNING}Please edit .env file to add any API keys{Colors.ENDC}")
        else:
            logger.info(".env file already exists")
    
    def create_templates(self):
        """Create basic HTML templates"""
        templates_dir = Path("templates")
        
        # Base template
        base_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Event Discovery{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body { padding-top: 60px; }
        .navbar { background-color: #2c3e50; }
        .btn-primary { background-color: #3498db; border-color: #3498db; }
        .event-card { margin-bottom: 20px; transition: transform 0.2s; }
        .event-card:hover { transform: translateY(-5px); }
    </style>
    {% block extra_css %}{% endblock %}
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark fixed-top">
        <div class="container">
            <a class="navbar-brand" href="/">Event Discovery</a>
        </div>
    </nav>
    
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'danger' if category == 'error' else category }} alert-dismissible fade show" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        {% block content %}{% endblock %}
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>"""
        
        # Index template
        index_template = """{% extends "base.html" %}
{% block title %}Event Discovery - Home{% endblock %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8">
        <h1 class="text-center mb-4">Discover Local Events</h1>
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Welcome to Event Discovery</h5>
                <p class="card-text">
                    Find events tailored to your interests based on online activity analysis.
                </p>
                <div id="location-status" class="alert alert-info">
                    <i class="fas fa-spinner fa-spin"></i> Detecting your location...
                </div>
                <div class="text-center mt-3">
                    <button class="btn btn-primary btn-lg" onclick="window.location.href='/user-info'" disabled id="start-btn">
                        Get Started
                    </button>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
// Detect location on page load
window.addEventListener('load', function() {
    fetch('/api/detect-location', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('location-status').innerHTML = 
                    '<i class="fas fa-check-circle"></i> Location detected: ' + 
                    data.location.city + ', ' + data.location.region;
                document.getElementById('start-btn').disabled = false;
            } else {
                document.getElementById('location-status').className = 'alert alert-warning';
                document.getElementById('location-status').innerHTML = 
                    '<i class="fas fa-exclamation-triangle"></i> Could not detect location. Please try again.';
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
});
</script>
{% endblock %}"""
        
        # Create templates
        (templates_dir / "base.html").write_text(base_template)
        (templates_dir / "index.html").write_text(index_template)
        
        # Create other required templates
        templates = {
            "404.html": """{% extends "base.html" %}
{% block content %}
<div class="text-center">
    <h1>404 - Page Not Found</h1>
    <p>The page you're looking for doesn't exist.</p>
    <a href="/" class="btn btn-primary">Go Home</a>
</div>
{% endblock %}""",
            
            "500.html": """{% extends "base.html" %}
{% block content %}
<div class="text-center">
    <h1>500 - Server Error</h1>
    <p>Something went wrong. Please try again later.</p>
    <a href="/" class="btn btn-primary">Go Home</a>
</div>
{% endblock %}""",
            
            "user_info.html": """{% extends "base.html" %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8">
        <h2>Tell us about yourself</h2>
        <form method="POST" action="/api/search">
            {{ form.csrf_token }}
            <div class="mb-3">
                {{ form.first_name.label(class="form-label") }}
                {{ form.first_name(class="form-control") }}
            </div>
            <div class="mb-3">
                {{ form.last_name.label(class="form-label") }}
                {{ form.last_name(class="form-control") }}
            </div>
            <div class="mb-3">
                {{ form.activity.label(class="form-label") }}
                {{ form.activity(class="form-control", rows=4) }}
            </div>
            <button type="submit" class="btn btn-primary">Find Events</button>
        </form>
    </div>
</div>
{% endblock %}""",
            
            "processing.html": """{% extends "base.html" %}
{% block content %}
<div class="text-center">
    <h2>Searching for Events...</h2>
    <div class="progress mt-4" style="height: 30px;">
        <div id="progress-bar" class="progress-bar progress-bar-striped progress-bar-animated" 
             role="progressbar" style="width: 0%">0%</div>
    </div>
    <p id="status-message" class="mt-3">Starting search...</p>
</div>

<script>
// Poll for status updates
function checkStatus() {
    fetch('/api/status/{{ session.session_id }}')
        .then(response => response.json())
        .then(data => {
            const progressBar = document.getElementById('progress-bar');
            progressBar.style.width = data.progress + '%';
            progressBar.textContent = data.progress + '%';
            document.getElementById('status-message').textContent = data.message;
            
            if (data.complete) {
                window.location.href = '/results';
            } else if (!data.error) {
                setTimeout(checkStatus, 1000);
            }
        });
}
checkStatus();
</script>
{% endblock %}""",
            
            "results.html": """{% extends "base.html" %}
{% block content %}
<h2>Events for You</h2>
<div class="row">
    <div class="col-md-8">
        {% for event in events %}
        <div class="card event-card">
            <div class="card-body">
                <h5 class="card-title">{{ event.name }}</h5>
                <p class="card-text">
                    <i class="fas fa-clock"></i> {{ event.date }} at {{ event.time }}<br>
                    <i class="fas fa-map-marker"></i> {{ event.venue }}<br>
                    <i class="fas fa-tag"></i> {{ event.category }}<br>
                    <i class="fas fa-star"></i> Relevance: {{ event.relevance }}
                </p>
                <a href="{{ event.url }}" target="_blank" class="btn btn-primary">View Event</a>
            </div>
        </div>
        {% endfor %}
    </div>
    <div class="col-md-4">
        <div id="map" style="height: 400px;"></div>
    </div>
</div>
{% endblock %}"""
        }
        
        for filename, content in templates.items():
            (templates_dir / filename).write_text(content)
        
        logger.info("✓ Created HTML templates")

class ComponentValidator:
    """Validate that all components are working"""
    
    def __init__(self, python_cmd):
        self.python_cmd = python_cmd
        self.components = {}
        self.test_results = {}
    
    def test_component(self, name: str, test_func):
        """Test a single component"""
        try:
            print(f"Testing {name}...", end=" ")
            result = test_func()
            self.test_results[name] = result
            if result:
                print(f"{Colors.OKGREEN}OK{Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}FAILED{Colors.ENDC}")
            return result
        except Exception as e:
            print(f"{Colors.FAIL}ERROR{Colors.ENDC}")
            logger.error(f"Component {name} test error: {e}")
            self.test_results[name] = False
            return False
    
    def test_imports(self):
        """Test that all required modules can be imported"""
        modules_to_test = [
            'flask', 'requests', 'bs4', 'nltk', 'spacy',
            'geopy', 'folium', 'redis', 'diskcache'
        ]
        
        all_ok = True
        for module in modules_to_test:
            try:
                importlib.import_module(module)
            except ImportError:
                logger.error(f"Cannot import {module}")
                all_ok = False
        
        return all_ok
    
    def test_config(self):
        """Test configuration module"""
        try:
            # Import and test config
            sys.path.insert(0, os.getcwd())
            from config import config
            
            # Validate configuration
            issues = config.validate()
            if issues['errors']:
                logger.error(f"Config errors: {issues['errors']}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Config test error: {e}")
            return False
    
    def test_database(self):
        """Test database/cache connectivity"""
        try:
            from cache_service import CacheService
            from config import config
            
            cache = CacheService(config)
            
            # Test cache operations
            test_key = "test_key"
            test_value = {"test": "data"}
            
            cache.set(test_key, test_value, ttl=60)
            retrieved = cache.get(test_key)
            cache.delete(test_key)
            
            return retrieved == test_value
            
        except Exception as e:
            logger.error(f"Database test error: {e}")
            return False
    
    def test_web_scraping(self):
        """Test web scraping capabilities"""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            response = requests.get("https://www.google.com", timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            return response.status_code == 200 and soup.title is not None
            
        except Exception as e:
            logger.error(f"Web scraping test error: {e}")
            return False
    
    def test_event_service(self):
        """Test the new free event service"""
        try:
            from free_events_service import GoogleEventsService
            
            service = GoogleEventsService()
            # Just test that it initializes
            return True
            
        except Exception as e:
            logger.error(f"Event service test error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all component tests"""
        print(f"\n{Colors.HEADER}{'='*60}")
        print("COMPONENT VALIDATION")
        print(f"{'='*60}{Colors.ENDC}\n")
        
        tests = [
            ("Python Imports", self.test_imports),
            ("Configuration", self.test_config),
            ("Cache/Database", self.test_database),
            ("Web Scraping", self.test_web_scraping),
            ("Event Service", self.test_event_service)
        ]
        
        for test_name, test_func in tests:
            self.test_component(test_name, test_func)
        
        # Summary
        passed = sum(1 for result in self.test_results.values() if result)
        total = len(self.test_results)
        
        print(f"\n{Colors.HEADER}Test Summary: {passed}/{total} passed{Colors.ENDC}")
        
        if passed < total:
            print(f"\n{Colors.WARNING}Failed components:{Colors.ENDC}")
            for name, result in self.test_results.items():
                if not result:
                    print(f"  • {name}")
        
        return passed == total

class ApplicationLauncher:
    """Launch and manage the application"""
    
    def __init__(self, python_cmd):
        self.python_cmd = python_cmd
        self.processes = []
    
    def start_redis(self):
        """Start Redis server if available"""
        if shutil.which('redis-server'):
            try:
                print("Starting Redis server...", end=" ")
                process = subprocess.Popen(
                    ['redis-server'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.processes.append(process)
                time.sleep(2)  # Give Redis time to start
                print(f"{Colors.OKGREEN}OK{Colors.ENDC}")
                return True
            except:
                print(f"{Colors.WARNING}SKIPPED{Colors.ENDC}")
                return False
        return False
    
    def update_config_for_free_events(self):
        """Update configuration to use free event service"""
        config_update = """
# Import the original config
from config_module import Config as BaseConfig
from dataclasses import dataclass

# Extend config for free events service
@dataclass 
class EventsConfig:
    search_radius_miles: int = 25
    time_window_hours: int = 168
    max_events: int = 50

@dataclass
class APIConfig:
    meetup_api_key: str = ""
    ipinfo_token: str = ""
    openai_api_key: str = ""
    huggingface_api_key: str = ""

class Config(BaseConfig):
    def __init__(self, config_file=None):
        super().__init__(config_file)
        self.events = EventsConfig()
        self.api = APIConfig()
        
        # Load from environment
        import os
        self.api.meetup_api_key = os.getenv('MEETUP_API_KEY', '')
        self.api.ipinfo_token = os.getenv('IPINFO_TOKEN', '')
        
        # Update to use free event service
        self.eventbrite_enabled = False

# Create global config instance
config = Config()
"""
        
        # Write updated config
        with open("config.py", "w") as f:
            f.write(config_update)
        
        logger.info("✓ Updated configuration for free events")
    
    def create_app_launcher(self):
        """Create the main app.py that integrates everything"""
        app_content = '''"""
app.py - Main Flask application with free event discovery
"""
import sys
import os
sys.path.insert(0, os.getcwd())

# Import the Flask app from flask-app.py
from flask_app import *

# Import and integrate the free events service
from free_events_service import FreeEventDiscoveryService

# Override the EventBrite service with our free service
import event_orchestrator
event_orchestrator.EventBriteService = FreeEventDiscoveryService

# Update the event orchestrator
class UpdatedEventOrchestrator(EventOrchestrator):
    def __init__(self, config, cache_service):
        super().__init__(config, cache_service)
        # Replace EventBrite with free service
        self.eventbrite_service = FreeEventDiscoveryService(config)

# Replace the orchestrator in the app
event_orchestrator.EventOrchestrator = UpdatedEventOrchestrator
orchestrator.__class__ = UpdatedEventOrchestrator
orchestrator.eventbrite_service = FreeEventDiscoveryService(config)

if __name__ == "__main__":
    print("Starting Event Discovery App...")
    print(f"Access the application at: http://localhost:{config.port}")
    print("Press Ctrl+C to stop")
    
    app.run(
        host=config.host,
        port=config.port,
        debug=config.debug
    )
'''
        
        with open("app.py", "w") as f:
            f.write(app_content)
        
        logger.info("✓ Created app launcher")
    
    def start_application(self):
        """Start the Flask application"""
        print(f"\n{Colors.HEADER}{'='*60}")
        print("STARTING APPLICATION")
        print(f"{'='*60}{Colors.ENDC}\n")
        
        # Update configuration
        self.update_config_for_free_events()
        
        # Create app launcher
        self.create_app_launcher()
        
        # Start Redis if available
        self.start_redis()
        
        # Launch Flask app
        print(f"\n{Colors.OKGREEN}Starting Event Discovery App...{Colors.ENDC}")
        print(f"Access the application at: {Colors.OKCYAN}http://localhost:5000{Colors.ENDC}")
        print(f"Press {Colors.WARNING}Ctrl+C{Colors.ENDC} to stop\n")
        
        try:
            subprocess.run([str(self.python_cmd), "app.py"])
        except KeyboardInterrupt:
            print(f"\n{Colors.WARNING}Shutting down...{Colors.ENDC}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up processes"""
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Event Discovery App Installer and Launcher")
    parser.add_argument('--skip-install', action='store_true', help='Skip installation steps')
    parser.add_argument('--test-only', action='store_true', help='Only run tests')
    parser.add_argument('--setup-only', action='store_true', help='Only setup, don\'t launch')
    args = parser.parse_args()
    
    print(f"{Colors.HEADER}{'='*60}")
    print("EVENT DISCOVERY APP - UNIFIED INSTALLER")
    print(f"{'='*60}{Colors.ENDC}")
    
    # System checks
    checker = SystemChecker()
    if not checker.run_all_checks():
        if checker.issues:
            print(f"\n{Colors.FAIL}Cannot continue due to critical issues.{Colors.ENDC}")
            sys.exit(1)
    
    # Installation
    if not args.skip_install:
        installer = DependencyInstaller()
        
        if not installer.create_virtual_environment():
            print(f"{Colors.FAIL}Failed to create virtual environment{Colors.ENDC}")
            sys.exit(1)
        
        installer.upgrade_pip()
        
        if not installer.install_requirements():
            print(f"{Colors.FAIL}Failed to install requirements{Colors.ENDC}")
            sys.exit(1)
        
        installer.download_nlp_data()
    else:
        # Set up paths for existing venv
        installer = DependencyInstaller()
        installer.venv_path = Path("venv")
        if platform.system() == "Windows":
            installer.python_cmd = installer.venv_path / "Scripts" / "python.exe"
        else:
            installer.python_cmd = installer.venv_path / "bin" / "python"
    
    # Project setup
    setup = ProjectSetup()
    setup.create_directories()
    setup.create_env_file()
    setup.create_templates()
    
    # Copy script files if they exist
    script_files = [
        "config_module.py", "main_search.py", "scraper_orchestrator.py",
        "data_processor.py", "ai_integration.py", "free_events_service.py",
        "location_service.py", "map_service.py", "cache_service.py",
        "event_orchestrator.py", "flask_app.py"
    ]
    
    for script in script_files:
        if os.path.exists(script) and script.endswith('.py'):
            # Just ensure they're in the right place
            logger.info(f"✓ Found {script}")
    
    # Component validation
    validator = ComponentValidator(installer.python_cmd)
    if not validator.run_all_tests():
        print(f"\n{Colors.WARNING}Some components failed validation.{Colors.ENDC}")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    if args.test_only:
        print(f"\n{Colors.OKGREEN}Testing complete!{Colors.ENDC}")
        sys.exit(0)
    
    if args.setup_only:
        print(f"\n{Colors.OKGREEN}Setup complete!{Colors.ENDC}")
        print(f"Run '{Colors.OKCYAN}python unified_installer.py{Colors.ENDC}' to start the application")
        sys.exit(0)
    
    # Launch application
    launcher = ApplicationLauncher(installer.python_cmd)
    launcher.start_application()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)
