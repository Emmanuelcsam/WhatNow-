# requirements.txt
# Core Flask dependencies
Flask==2.3.3
Flask-WTF==1.1.1
Flask-CORS==4.0.0
Flask-Limiter==3.5.0
Werkzeug==2.3.7

# Web scraping and HTTP
requests==2.31.0
beautifulsoup4==4.12.2
lxml==4.9.3
aiohttp==3.8.5
requests-futures==1.0.1
urllib3==2.0.4

# Data processing and NLP
nltk==3.8.1
spacy==3.6.1
textblob==0.17.1
yake==0.4.8
scikit-learn==1.3.0
numpy==1.25.2
pandas==2.1.0

# AI and ML (optional)
openai==0.28.0
transformers==4.33.2
sentence-transformers==2.2.2
torch==2.0.1

# Location and mapping
geocoder==1.38.1
geopy==2.4.0
folium==0.14.0
pytz==2023.3
timezonefinder==6.2.0
ipinfo==4.4.3

# Caching and storage
redis==5.0.0
diskcache==5.6.3

# Event calendar
icalendar==5.0.7

# Security and utilities
python-dotenv==1.0.0
cryptography==41.0.4

# Development dependencies (optional)
pytest==7.4.2
pytest-asyncio==0.21.1
black==23.9.1
flake8==6.1.0

# setup.py
"""
setup.py - Installation and setup script for Event Discovery App
"""
import os
import sys
import subprocess
import platform
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*60)
    print(text.center(60))
    print("="*60 + "\n")

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("ERROR: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"✓ Python {version.major}.{version.minor}.{version.micro} detected")

def create_directories():
    """Create necessary directories"""
    directories = [
        'data',
        'data/cache',
        'data/logs',
        'data/temp',
        'static',
        'static/css',
        'static/js',
        'static/images',
        'templates'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✓ Created directory structure")

def create_env_file():
    """Create .env file template"""
    env_template = """# Event Discovery App Configuration

# API Keys
EVENTBRITE_API_TOKEN=your_eventbrite_token_here
OPENAI_API_KEY=your_openai_key_here_optional
HUGGINGFACE_API_KEY=your_huggingface_key_here_optional
IPINFO_TOKEN=your_ipinfo_token_here_optional
GOOGLE_MAPS_API_KEY=your_google_maps_key_here_optional

# Flask Configuration
SECRET_KEY=change_this_to_random_secret_key
DEBUG=False
HOST=0.0.0.0
PORT=5000

# Security Settings
ENABLE_RATE_LIMITING=True
REQUESTS_PER_MINUTE=60

# Cache Settings
CACHE_EXPIRY_HOURS=24

# AI Settings
ENABLE_AI=True
AI_PROVIDER=local  # Options: openai, huggingface, local
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_template)
        print("✓ Created .env file template")
        print("  ⚠️  Please edit .env and add your API keys")
    else:
        print("✓ .env file already exists")

def install_dependencies():
    """Install Python dependencies"""
    print_header("Installing Dependencies")
    
    try:
        # Upgrade pip
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'])
        
        # Install requirements
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        
        print("✓ Installed Python dependencies")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies: {e}")
        sys.exit(1)

def download_nlp_data():
    """Download required NLP data"""
    print_header("Downloading NLP Data")
    
    try:
        import nltk
        nltk_data = [
            'punkt', 'stopwords', 'wordnet', 'averaged_perceptron_tagger',
            'maxent_ne_chunker', 'words', 'vader_lexicon'
        ]
        
        for data in nltk_data:
            nltk.download(data, quiet=True)
        
        print("✓ Downloaded NLTK data")
        
        # Download spaCy model
        try:
            subprocess.check_call([sys.executable, '-m', 'spacy', 'download', 'en_core_web_sm'])
            print("✓ Downloaded spaCy model")
        except:
            print("⚠️  Failed to download spaCy model (optional)")
            
    except Exception as e:
        print(f"⚠️  Failed to download NLP data (optional): {e}")

def check_redis():
    """Check if Redis is available"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379)
        r.ping()
        print("✓ Redis is available")
    except:
        print("⚠️  Redis not available (optional - will use disk cache)")

def create_systemd_service():
    """Create systemd service file (Linux only)"""
    if platform.system() != 'Linux':
        return
    
    service_content = f"""[Unit]
Description=Event Discovery Web Application
After=network.target

[Service]
Type=simple
User={os.getenv('USER')}
WorkingDirectory={os.getcwd()}
Environment="PATH={os.environ.get('PATH')}"
ExecStart={sys.executable} app.py
Restart=always

[Install]
WantedBy=multi-user.target
"""
    
    service_path = f"eventdiscovery.service"
    with open(service_path, 'w') as f:
        f.write(service_content)
    
    print(f"✓ Created systemd service file: {service_path}")
    print("  To install: sudo cp eventdiscovery.service /etc/systemd/system/")
    print("  To enable: sudo systemctl enable eventdiscovery")
    print("  To start: sudo systemctl start eventdiscovery")

def main():
    """Main setup function"""
    print_header("Event Discovery App Setup")
    
    # Check Python version
    check_python_version()
    
    # Create directories
    create_directories()
    
    # Create env file
    create_env_file()
    
    # Install dependencies
    response = input("\nInstall Python dependencies? (y/n): ").lower()
    if response == 'y':
        install_dependencies()
        download_nlp_data()
    
    # Check optional services
    print_header("Checking Optional Services")
    check_redis()
    
    # Create service file
    if platform.system() == 'Linux':
        response = input("\nCreate systemd service file? (y/n): ").lower()
        if response == 'y':
            create_systemd_service()
    
    print_header("Setup Complete!")
    print("Next steps:")
    print("1. Edit .env file and add your API keys")
    print("2. Run 'python app.py' to start the application")
    print("3. Visit http://localhost:5000 in your browser")
    print("\nFor production deployment:")
    print("- Use a production WSGI server (gunicorn, uwsgi)")
    print("- Set up a reverse proxy (nginx)")
    print("- Enable HTTPS with SSL certificates")
    print("- Configure firewall rules")

if __name__ == "__main__":
    main()

# run.sh - Startup script
#!/bin/bash
# Event Discovery App Startup Script

echo "Starting Event Discovery App..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if Redis is running
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo "✓ Redis is running"
    else
        echo "⚠️  Redis is not running (optional)"
    fi
fi

# Set environment variables
export FLASK_APP=app.py

# Run database initialization
echo "Initializing database..."
flask init-db

# Start the application
if [ "$1" == "production" ]; then
    echo "Starting in production mode..."
    gunicorn -w 4 -b 0.0.0.0:5000 app:app
else
    echo "Starting in development mode..."
    python app.py
fi

# docker-compose.yml - Docker configuration
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./data:/app/data
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web
    restart: unless-stopped

volumes:
  redis_data:

# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLP data
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
RUN python -m spacy download en_core_web_sm || true

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/cache data/logs data/temp

# Expose port
EXPOSE 5000

# Run the application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
