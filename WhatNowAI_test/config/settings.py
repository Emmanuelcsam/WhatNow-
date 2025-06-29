"""
Enhanced Application Configuration with Multiple API Integrations
Combines original settings with advanced features from Upgrades
"""
import os
from pathlib import Path
from typing import Dict, Any

# Base directory
BASE_DIR = Path(__file__).parent.parent

def load_secrets():
    """
    Load API keys and secrets from secrets.txt file and fall back to environment variables if not found.

    Returns:
        dict: A dictionary containing secrets.
    """
    vars = [
        "OPENAI_API_KEY", "TICKETMASTER_CONSUMER_KEY", "TICKETMASTER_CONSUMER_SECRET",
        "SEATGEEK_CLIENT_ID", "SEATGEEK_CLIENT_SECRET", "SONGKICK_API_KEY",
        "MEETUP_API_KEY", "PREDICTHQ_ACCESS_TOKEN", "EVENTFUL_API_KEY",
        "HUGGINGFACE_TOKEN", "SERPER_API_KEY", "SECRET_KEY",
        "ALLEVENTS_API_KEY", "NEWSAPI_KEY", "IPSTACK_API_KEY"
    ]
    secrets = {}
    secrets_file = BASE_DIR / 'secrets.txt'

    # Load from secrets.txt if it exists
    if secrets_file.exists():
        try:
            with open(secrets_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        secrets[key.strip()] = value.strip()
        except Exception as e:
            print(f"Warning: Could not load secrets.txt: {e}")

    # Fallback to environment variables for missing keys
    for var in vars:
        if var not in secrets:
            env_val = os.getenv(var)
            if env_val:
                secrets[var] = env_val

    return secrets

# Load secrets from file
_secrets = load_secrets()

# Audio configuration
AUDIO_DIR = BASE_DIR / 'static' / 'audio'
DEFAULT_TTS_VOICE = "en-US-JennyNeural"
AUDIO_CLEANUP_HOURS = 24

# Flask configuration - Enhanced with session support
FLASK_CONFIG = {
    'DEBUG': True,
    'HOST': '0.0.0.0',
    'PORT': 5002,
    'SECRET_KEY': os.getenv('SECRET_KEY', _secrets.get('SECRET_KEY', 'dev-key-change-in-production'))
}

# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        },
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'default',
            'stream': 'ext://sys.stdout'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console']
    }
}

# Geocoding configuration
GEOCODING_CONFIG = {
    'USER_AGENT': 'WhatNowAI/1.0',
    'TIMEOUT': 10
}

# API Keys from secrets.txt file and environment variables (env vars take precedence)
TICKETMASTER_API_KEY = os.getenv('TICKETMASTER_API_KEY', _secrets.get('TICKETMASTER_CONSUMER_KEY', ''))
ALLEVENTS_API_KEY = os.getenv('ALLEVENTS_API_KEY', _secrets.get('ALLEVENTS_API_KEY', ''))
NEWSAPI_KEY = os.getenv('NEWSAPI_KEY', _secrets.get('NEWSAPI_KEY', ''))
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', _secrets.get('OPENAI_API_KEY', ''))
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', _secrets.get('OPENAI_API_KEY', ''))

# Enhanced API Keys for Multiple Services
SEATGEEK_CLIENT_ID = os.getenv('SEATGEEK_CLIENT_ID', _secrets.get('SEATGEEK_CLIENT_ID', ''))
SEATGEEK_CLIENT_SECRET = os.getenv('SEATGEEK_CLIENT_SECRET', _secrets.get('SEATGEEK_CLIENT_SECRET', ''))
SONGKICK_API_KEY = os.getenv('SONGKICK_API_KEY', _secrets.get('SONGKICK_API_KEY', ''))
MEETUP_API_KEY = os.getenv('MEETUP_API_KEY', _secrets.get('MEETUP_API_KEY', ''))
PREDICTHQ_ACCESS_TOKEN = os.getenv('PREDICTHQ_ACCESS_TOKEN', _secrets.get('PREDICTHQ_ACCESS_TOKEN', ''))
EVENTFUL_API_KEY = os.getenv('EVENTFUL_API_KEY', _secrets.get('EVENTFUL_API_KEY', ''))

# Search and AI Enhancement APIs
SERPER_API_KEY = os.getenv('SERPER_API_KEY', _secrets.get('SERPER_API_KEY', ''))
HUGGINGFACE_TOKEN = os.getenv('HUGGINGFACE_TOKEN', _secrets.get('HUGGINGFACE_TOKEN', ''))

# Service Configurations
TICKETMASTER_CONFIG = {
    'BASE_URL': 'https://app.ticketmaster.com/discovery/v2',
    'SEARCH_RADIUS': 50,
    'MAX_EVENTS': 20,
    'DEFAULT_TIME_RANGE': 12,  # hours
    'TIMEOUT': 10
}

ALLEVENTS_CONFIG = {
    'BASE_URL': 'https://allevents.in/api',
    'SEARCH_RADIUS': 50,
    'MAX_EVENTS': 20,
    'DEFAULT_TIME_RANGE': 12,
    'TIMEOUT': 10
}

SEATGEEK_CONFIG = {
    'BASE_URL': 'https://api.seatgeek.com/2',
    'SEARCH_RADIUS': 50,  # miles
    'MAX_EVENTS': 30,
    'TIMEOUT': 10,
    'DEFAULT_TIME_RANGE': 12  # hours
}

SONGKICK_CONFIG = {
    'BASE_URL': 'https://api.songkick.com/api/3.0',
    'SEARCH_RADIUS': 50,
    'MAX_EVENTS': 30,
    'TIMEOUT': 10
}

MEETUP_CONFIG = {
    'BASE_URL': 'https://api.meetup.com',
    'SEARCH_RADIUS': 50,
    'MAX_EVENTS': 30,
    'TIMEOUT': 10
}

PREDICTHQ_CONFIG = {
    'BASE_URL': 'https://api.predicthq.com/v1',
    'SEARCH_RADIUS': 50,
    'MAX_EVENTS': 30,
    'TIMEOUT': 10,
    'CATEGORIES': ['concerts', 'festivals', 'performing-arts', 'sports', 'community']
}

# Map configuration
MAP_CONFIG = {
    'DEFAULT_ZOOM': 12,
    'MAX_MARKERS': 100,
    'TILE_SERVER': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    'ATTRIBUTION': '© OpenStreetMap contributors'
}

# Enhanced Search Configuration
ENHANCED_SEARCH_CONFIG = {
    'MAX_RESULTS_PER_SOURCE': 10,
    'TIMEOUT': 15,  # Reduced from 30 for better UX
    'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'USE_AI_FILTERING': True,
    'ENABLE_DEEP_SEARCH': True,
    'CACHE_DURATION': 3600,  # 1 hour
    'MAX_CONCURRENT_REQUESTS': 5,  # Reduced for stability
    'ENABLE_SOCIAL_SEARCH': True,
    'SOCIAL_PLATFORMS': ['github', 'linkedin', 'twitter', 'instagram'],  # Focus on key platforms
    'SEARCH_ENGINES': ['duckduckgo', 'serper'],
    'ENABLE_SEMANTIC_SEARCH': True,
    'PRIVACY_MODE': True  # Respect user privacy
}

# Data Processing Configuration
DATA_PROCESSING_CONFIG = {
    'MIN_CONFIDENCE_SCORE': 0.3,
    'MAX_INTERESTS': 20,
    'ENABLE_NLP': True,
    'ENABLE_ENTITY_RECOGNITION': True,
    'CACHE_PROCESSED_DATA': True,
    'PRIVACY_MODE': True,
    'FILTER_SENSITIVE_DATA': True
}

# AI Configuration
AI_CONFIG = {
    'USE_OPENAI': bool(OPENAI_API_KEY),
    'USE_HUGGINGFACE': bool(HUGGINGFACE_TOKEN),
    'OPENAI_API_KEY': OPENAI_API_KEY,
    'OPENAI_MODEL': 'gpt-3.5-turbo',
    'MAX_TOKENS': 500,
    'TEMPERATURE': 0.3,
    'LOCAL_MODELS': {
        'SENTIMENT': 'distilbert-base-uncased-finetuned-sst-2-english',
        'NER': 'dbmdz/bert-large-cased-finetuned-conll03-english',
        'CLASSIFICATION': 'facebook/bart-large-mnli'
    }
}

# Rate Limiting Configuration
RATE_LIMIT_CONFIG = {
    'ticketmaster': {'calls': 500, 'window': 86400},  # 500/day
    'seatgeek': {'calls': 1000, 'window': 3600},      # 1000/hour
    'songkick': {'calls': 1000, 'window': 86400},     # 1000/day
    'meetup': {'calls': 200, 'window': 3600},         # 200/hour
    'predicthq': {'calls': 500, 'window': 86400},     # 500/day
    'openai': {'calls': 60, 'window': 60},            # 60/minute
    'serper': {'calls': 1000, 'window': 86400},       # 1000/day
    'DEFAULT': {'calls': 100, 'window': 3600}         # Default: 100/hour
}

# Enhanced Location Service Configuration
IPSTACK_API_KEY = os.getenv('IPSTACK_API_KEY', _secrets.get('IPSTACK_API_KEY', ''))

# Location service settings
LOCATION_CONFIG = {
    'IPSTACK_API_KEY': IPSTACK_API_KEY,
    'ENABLE_IP_LOCATION': True,
    'ENABLE_BROWSER_LOCATION': True,
    'CACHE_TTL_HOURS': 1,
    'TIMEOUT_SECONDS': 10,
    'MAX_PROVIDERS': 3
}

def check_api_keys():
    """Check which API keys are available"""
    keys_status = {
        'TICKETMASTER_API_KEY': 'SET' if TICKETMASTER_API_KEY else 'NOT SET',
        'ALLEVENTS_API_KEY': 'SET' if ALLEVENTS_API_KEY else 'NOT SET',
        'OPENAI_API_KEY': 'SET' if OPENAI_API_KEY else 'NOT SET',
        'SEATGEEK_CLIENT_ID': 'SET' if SEATGEEK_CLIENT_ID else 'NOT SET',
        'SONGKICK_API_KEY': 'SET' if SONGKICK_API_KEY else 'NOT SET',
        'MEETUP_API_KEY': 'SET' if MEETUP_API_KEY else 'NOT SET',
        'PREDICTHQ_ACCESS_TOKEN': 'SET' if PREDICTHQ_ACCESS_TOKEN else 'NOT SET',
        'SERPER_API_KEY': 'SET' if SERPER_API_KEY else 'NOT SET',
        'HUGGINGFACE_TOKEN': 'SET' if HUGGINGFACE_TOKEN else 'NOT SET'
    }

    print("=== API Key Status ===")
    for key, status in keys_status.items():
        print(f"{key}: {status}")
    print("======================")

    # Count available services
    available_count = sum(1 for status in keys_status.values() if status == 'SET')
    total_count = len(keys_status)

    print(f"API Coverage: {available_count}/{total_count} services configured")

    if not TICKETMASTER_API_KEY and not ALLEVENTS_API_KEY:
        print("WARNING: No event API keys configured. Event discovery will be limited.")

    return keys_status
