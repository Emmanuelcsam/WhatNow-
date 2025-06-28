"""
config.py - Enhanced configuration for OSINT scraper with free event discovery
"""
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class ScraperConfig:
    """Configuration for web scraping tools"""
    # General settings
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    max_results_per_source: int = 10
    search_depth: int = 2
    request_timeout: int = 10
    rate_limit_delay: float = 1.0
    max_search_time: int = 60
    
    # Tool enable flags
    enable_sherlock: bool = True
    enable_photon: bool = True
    enable_harvester: bool = True
    enable_daprofiler: bool = True
    enable_proton: bool = True
    enable_snscrape: bool = True
    enable_twint: bool = True
    enable_tookie: bool = True
    
    # Sherlock configuration
    sherlock_timeout: int = 5
    sherlock_sites_limit: int = 50
    sherlock_print_all: bool = False
    sherlock_no_color: bool = True
    
    # Photon configuration
    photon_level: int = 2
    photon_threads: int = 4
    photon_timeout: int = 3
    photon_dns: bool = True
    photon_keys: bool = True
    photon_export: bool = False
    
    # theHarvester configuration
    harvester_sources: List[str] = field(default_factory=lambda: ['google', 'bing', 'duckduckgo'])
    harvester_limit: int = 100
    harvester_start: int = 0
    harvester_dns_lookup: bool = False
    harvester_dns_brute: bool = False
    
    # DaProfiler configuration
    daprofiler_platforms: List[str] = field(default_factory=lambda: ['facebook', 'twitter', 'instagram', 'linkedin'])
    daprofiler_use_selenium: bool = False
    daprofiler_headless: bool = True
    daprofiler_timeout: int = 20
    
    # Parallel execution settings
    max_workers: int = 10
    async_timeout: int = 60
    individual_timeout: Dict[str, int] = field(default_factory=lambda: {
        'google_search': 10,
        'duckduckgo': 10,
        'bing': 10,
        'social_media': 15,
        'sherlock': 30,
        'photon': 30,
        'theharvester': 30,
        'daprofiler': 30,
        'proton': 20,
        'snscrape': 20,
        'twint': 25,
        'tookie': 30
    })

@dataclass
class EventsConfig:
    """Configuration for event discovery"""
    search_radius_miles: int = 25
    time_window_hours: int = 168  # 1 week
    max_events: int = 50
    event_sources: List[str] = field(default_factory=lambda: [
        'google_events', 'meetup', 'facebook', 'eventful', 'allevents', 'yelp'
    ])
    
    # Source-specific settings
    google_events_enabled: bool = True
    meetup_enabled: bool = True  # Only if API key provided
    facebook_events_enabled: bool = True
    local_aggregator_enabled: bool = True

@dataclass
class APIConfig:
    """API keys configuration"""
    # Optional API keys
    meetup_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    huggingface_api_key: Optional[str] = None
    ipinfo_token: Optional[str] = None
    
    def __post_init__(self):
        # Load from environment
        self.meetup_api_key = os.getenv('MEETUP_API_KEY', '')
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '')
        self.huggingface_api_key = os.getenv('HUGGINGFACE_API_KEY', '')
        self.ipinfo_token = os.getenv('IPINFO_TOKEN', '')

@dataclass
class AIConfig:
    """AI integration configuration"""
    enable_ai: bool = False
    ai_provider: str = 'local'  # local, openai, huggingface
    
    # Model settings
    openai_model: str = 'gpt-3.5-turbo'
    huggingface_model: str = 'facebook/bart-large-mnli'
    
    # Processing settings
    interest_extraction_confidence: float = 0.6
    max_interests_to_extract: int = 20
    
    # Prompts
    interest_extraction_prompt: str = """
    Analyze the following data and extract user interests, hobbies, and preferences.
    Return as JSON array with format:
    [{"interest": "...", "category": "...", "confidence": 0.0-1.0, "reasoning": "..."}, ...]
    
    Data: {data}
    """
    
    relation_generation_prompt: str = """
    Based on these facts about a person, infer their likely interests and event preferences.
    Return as JSON array with format:
    [{"source_fact": "...", "derived_interest": "...", "confidence": 0.0-1.0, "reasoning": "...", "category": "..."}, ...]
    
    Facts: {facts}
    """

@dataclass
class ProxyConfig:
    """Configuration for proxy usage"""
    use_proxy: bool = False
    proxy_list: List[str] = field(default_factory=list)
    proxy_rotation: bool = True
    proxy_type: str = 'http'  # http, https, socks5
    proxy_auth: Optional[Dict[str, str]] = None

@dataclass
class CacheConfig:
    """Configuration for result caching"""
    enable_cache: bool = True
    cache_dir: str = './data/cache'
    cache_ttl: int = 3600  # seconds
    cache_max_size: int = 1000  # MB

@dataclass
class LoggingConfig:
    """Configuration for logging"""
    log_level: str = 'INFO'
    log_file: str = './logs/app.log'
    log_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    enable_console_log: bool = True
    enable_file_log: bool = True

@dataclass
class SecurityConfig:
    """Security and compliance configuration"""
    respect_robots_txt: bool = True
    max_requests_per_domain: int = 100
    blacklisted_domains: List[str] = field(default_factory=list)
    ssl_verify: bool = True
    data_encryption: bool = False
    pii_filtering: bool = True
    enable_rate_limiting: bool = True
    requests_per_minute: int = 60
    secure_session_timeout: int = 3600
    cache_expiry_hours: int = 24

class Config:
    """Main configuration class"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.scraper = ScraperConfig()
        self.events = EventsConfig()
        self.api = APIConfig()
        self.ai = AIConfig()
        self.proxy = ProxyConfig()
        self.cache = CacheConfig()
        self.logging = LoggingConfig()
        self.security = SecurityConfig()
        
        # Flask settings
        self.secret_key = os.getenv('SECRET_KEY', 'change_this_to_random_secret_key')
        self.debug = os.getenv('DEBUG', 'False').lower() == 'true'
        self.host = os.getenv('HOST', '0.0.0.0')
        self.port = int(os.getenv('PORT', 5000))
        
        # Paths
        self.data_dir = os.getenv('DATA_DIR', './data')
        self.cache_dir = os.getenv('CACHE_DIR', './data/cache')
        self.logs_dir = os.getenv('LOGS_DIR', './logs')
        
        # Load from file if provided
        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)
        
        # Environment variable overrides
        self._load_env_overrides()
        
        # Create directories
        self._create_directories()
    
    def _create_directories(self):
        """Ensure required directories exist"""
        for dir_path in [self.data_dir, self.cache_dir, self.logs_dir]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def load_from_file(self, config_file: str):
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                data = json.load(f)
            
            # Update each config section
            for section_name in ['scraper', 'events', 'api', 'ai', 'proxy', 'cache', 'logging', 'security']:
                if section_name in data and hasattr(self, section_name):
                    section = getattr(self, section_name)
                    for key, value in data[section_name].items():
                        if hasattr(section, key):
                            setattr(section, key, value)
                        
        except Exception as e:
            print(f"Error loading config file: {e}")
    
    def _load_env_overrides(self):
        """Load configuration overrides from environment variables"""
        # Example: OSINT_SCRAPER_MAX_WORKERS=20
        prefix = 'OSINT_'
        
        for env_var, value in os.environ.items():
            if env_var.startswith(prefix):
                # Parse the environment variable
                parts = env_var[len(prefix):].lower().split('_')
                
                if len(parts) >= 2:
                    section = parts[0]
                    key = '_'.join(parts[1:])
                    
                    # Apply the override
                    if hasattr(self, section):
                        section_obj = getattr(self, section)
                        if hasattr(section_obj, key):
                            # Convert value to appropriate type
                            current_value = getattr(section_obj, key)
                            if isinstance(current_value, bool):
                                setattr(section_obj, key, value.lower() == 'true')
                            elif isinstance(current_value, int):
                                setattr(section_obj, key, int(value))
                            elif isinstance(current_value, float):
                                setattr(section_obj, key, float(value))
                            else:
                                setattr(section_obj, key, value)
    
    def save_to_file(self, config_file: str):
        """Save configuration to JSON file"""
        data = {
            'scraper': self.scraper.__dict__,
            'events': self.events.__dict__,
            'api': self.api.__dict__,
            'ai': self.ai.__dict__,
            'proxy': self.proxy.__dict__,
            'cache': self.cache.__dict__,
            'logging': self.logging.__dict__,
            'security': self.security.__dict__
        }
        
        with open(config_file, 'w') as f:
            json.dump(data, f, indent=4)
    
    def validate(self) -> Dict[str, List[str]]:
        """Validate configuration and return issues"""
        errors = []
        warnings = []
        
        # Validate scraper settings
        if self.scraper.max_workers < 1:
            errors.append("max_workers must be at least 1")
        
        if self.scraper.max_results_per_source < 1:
            errors.append("max_results_per_source must be at least 1")
        
        # Validate event settings
        if self.events.search_radius_miles < 1:
            errors.append("search_radius_miles must be at least 1")
        
        if self.events.max_events < 1:
            errors.append("max_events must be at least 1")
        
        # Validate timeouts
        for tool, timeout in self.scraper.individual_timeout.items():
            if timeout < 1:
                errors.append(f"Timeout for {tool} must be at least 1 second")
        
        # Validate proxy settings
        if self.proxy.use_proxy and not self.proxy.proxy_list:
            errors.append("Proxy is enabled but no proxy list provided")
        
        # Validate cache settings
        if self.cache.enable_cache:
            if not os.path.exists(self.cache.cache_dir):
                try:
                    os.makedirs(self.cache.cache_dir)
                except Exception as e:
                    errors.append(f"Cannot create cache directory: {e}")
        
        # Check API keys
        if not self.api.meetup_api_key:
            warnings.append("Meetup API key not provided - Meetup events will be disabled")
        
        if self.ai.enable_ai:
            if self.ai.ai_provider == 'openai' and not self.api.openai_api_key:
                warnings.append("OpenAI API key not provided - AI features will use local models")
            elif self.ai.ai_provider == 'huggingface' and not self.api.huggingface_api_key:
                warnings.append("HuggingFace API key not provided - AI features will use local models")
        
        return {'errors': errors, 'warnings': warnings}
    
    def get_enabled_tools(self) -> List[str]:
        """Get list of enabled tools"""
        tools = []
        
        # Check each tool's enable flag
        tool_flags = {
            'sherlock': self.scraper.enable_sherlock,
            'photon': self.scraper.enable_photon,
            'theharvester': self.scraper.enable_harvester,
            'daprofiler': self.scraper.enable_daprofiler,
            'proton': self.scraper.enable_proton,
            'snscrape': self.scraper.enable_snscrape,
            'twint': self.scraper.enable_twint,
            'tookie': self.scraper.enable_tookie
        }
        
        for tool, enabled in tool_flags.items():
            if enabled:
                tools.append(tool)
        
        return tools
    
    def get_enabled_event_sources(self) -> List[str]:
        """Get list of enabled event sources"""
        sources = []
        
        if self.events.google_events_enabled:
            sources.append('google_events')
        
        if self.events.meetup_enabled and self.api.meetup_api_key:
            sources.append('meetup')
        
        if self.events.facebook_events_enabled:
            sources.append('facebook')
        
        if self.events.local_aggregator_enabled:
            sources.extend(['eventful', 'allevents', 'yelp'])
        
        return sources
    
    def optimize_for_speed(self):
        """Optimize settings for speed over completeness"""
        self.scraper.max_results_per_source = 5
        self.scraper.search_depth = 1
        self.scraper.sherlock_sites_limit = 20
        self.scraper.photon_level = 1
        self.scraper.harvester_limit = 50
        self.scraper.snscrape_max_results = 20
        self.scraper.twint_limit = 10
        self.scraper.max_workers = 15
        
        # Reduce individual timeouts
        for tool in self.scraper.individual_timeout:
            self.scraper.individual_timeout[tool] = min(
                self.scraper.individual_timeout[tool], 15
            )
        
        # Reduce event settings
        self.events.max_events = 25
        self.events.search_radius_miles = 15
    
    def optimize_for_completeness(self):
        """Optimize settings for completeness over speed"""
        self.scraper.max_results_per_source = 20
        self.scraper.search_depth = 3
        self.scraper.sherlock_sites_limit = 100
        self.scraper.photon_level = 3
        self.scraper.harvester_limit = 200
        self.scraper.snscrape_max_results = 100
        self.scraper.twint_limit = 50
        self.scraper.max_workers = 8
        
        # Increase individual timeouts
        for tool in self.scraper.individual_timeout:
            self.scraper.individual_timeout[tool] = max(
                self.scraper.individual_timeout[tool], 45
            )
        
        # Increase event settings
        self.events.max_events = 100
        self.events.search_radius_miles = 50
        self.events.time_window_hours = 336  # 2 weeks

# Create global config instance
config = Config()

# Validate on import
issues = config.validate()
if issues['errors']:
    print(f"Configuration errors: {issues['errors']}")
if issues['warnings']:
    for warning in issues['warnings']:
        print(f"Warning: {warning}")
