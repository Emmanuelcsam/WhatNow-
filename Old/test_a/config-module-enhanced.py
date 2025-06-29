"""
config_module.py - Enhanced configuration for OSINT scraper orchestrator
"""
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json

@dataclass
class ScraperConfig:
    """Configuration for web scraping tools"""
    # General settings
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    max_results_per_source: int = 10
    search_depth: int = 2
    request_timeout: int = 10
    rate_limit_delay: float = 1.0
    
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
    
    # Proton configuration
    proton_engines: List[str] = field(default_factory=lambda: ['google', 'bing', 'duckduckgo'])
    proton_max_results: int = 20
    proton_deep_search: bool = True
    
    # snscrape configuration
    snscrape_platforms: List[str] = field(default_factory=lambda: ['twitter-search'])
    snscrape_max_results: int = 50
    snscrape_since: Optional[str] = None
    snscrape_until: Optional[str] = None
    
    # Twint configuration
    twint_limit: int = 20
    twint_since: Optional[str] = None
    twint_until: Optional[str] = None
    twint_verified: bool = False
    twint_store_json: bool = False
    twint_hide_output: bool = True
    
    # Tookie configuration
    tookie_modules: List[str] = field(default_factory=lambda: ['whois', 'dns', 'social'])
    tookie_output_format: str = 'json'
    tookie_verbose: bool = False
    
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
    cache_dir: str = './cache'
    cache_ttl: int = 3600  # seconds
    cache_max_size: int = 1000  # MB

@dataclass
class LoggingConfig:
    """Configuration for logging"""
    log_level: str = 'INFO'
    log_file: str = 'osint_scraper.log'
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

class Config:
    """Main configuration class"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.scraper = ScraperConfig()
        self.proxy = ProxyConfig()
        self.cache = CacheConfig()
        self.logging = LoggingConfig()
        self.security = SecurityConfig()
        
        # Load from file if provided
        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)
        
        # Environment variable overrides
        self._load_env_overrides()
    
    def load_from_file(self, config_file: str):
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                data = json.load(f)
            
            # Update scraper config
            if 'scraper' in data:
                for key, value in data['scraper'].items():
                    if hasattr(self.scraper, key):
                        setattr(self.scraper, key, value)
            
            # Update proxy config
            if 'proxy' in data:
                for key, value in data['proxy'].items():
                    if hasattr(self.proxy, key):
                        setattr(self.proxy, key, value)
            
            # Update cache config
            if 'cache' in data:
                for key, value in data['cache'].items():
                    if hasattr(self.cache, key):
                        setattr(self.cache, key, value)
            
            # Update logging config
            if 'logging' in data:
                for key, value in data['logging'].items():
                    if hasattr(self.logging, key):
                        setattr(self.logging, key, value)
            
            # Update security config
            if 'security' in data:
                for key, value in data['security'].items():
                    if hasattr(self.security, key):
                        setattr(self.security, key, value)
                        
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
                    if section == 'scraper' and hasattr(self.scraper, key):
                        # Convert value to appropriate type
                        current_value = getattr(self.scraper, key)
                        if isinstance(current_value, bool):
                            setattr(self.scraper, key, value.lower() == 'true')
                        elif isinstance(current_value, int):
                            setattr(self.scraper, key, int(value))
                        elif isinstance(current_value, float):
                            setattr(self.scraper, key, float(value))
                        else:
                            setattr(self.scraper, key, value)
    
    def save_to_file(self, config_file: str):
        """Save configuration to JSON file"""
        data = {
            'scraper': self.scraper.__dict__,
            'proxy': self.proxy.__dict__,
            'cache': self.cache.__dict__,
            'logging': self.logging.__dict__,
            'security': self.security.__dict__
        }
        
        with open(config_file, 'w') as f:
            json.dump(data, f, indent=4)
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Validate scraper settings
        if self.scraper.max_workers < 1:
            issues.append("max_workers must be at least 1")
        
        if self.scraper.max_results_per_source < 1:
            issues.append("max_results_per_source must be at least 1")
        
        if self.scraper.search_depth < 1:
            issues.append("search_depth must be at least 1")
        
        # Validate timeouts
        for tool, timeout in self.scraper.individual_timeout.items():
            if timeout < 1:
                issues.append(f"Timeout for {tool} must be at least 1 second")
        
        # Validate proxy settings
        if self.proxy.use_proxy and not self.proxy.proxy_list:
            issues.append("Proxy is enabled but no proxy list provided")
        
        # Validate cache settings
        if self.cache.enable_cache:
            if not os.path.exists(self.cache.cache_dir):
                try:
                    os.makedirs(self.cache.cache_dir)
                except Exception as e:
                    issues.append(f"Cannot create cache directory: {e}")
        
        return issues
    
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

# Example usage
if __name__ == "__main__":
    # Create default config
    config = Config()
    
    # Validate
    issues = config.validate()
    if issues:
        print("Configuration issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("Configuration is valid")
    
    # Save to file
    config.save_to_file("osint_config.json")
    
    # Show enabled tools
    print(f"Enabled tools: {', '.join(config.get_enabled_tools())}")
    
    # Optimize for speed
    config.optimize_for_speed()
    print("Optimized for speed")
