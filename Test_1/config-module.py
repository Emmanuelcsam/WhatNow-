"""
config.py - Main configuration module for the Event Discovery Application
"""
import os
from dataclasses import dataclass
from typing import Optional, Dict, List
from datetime import timedelta

@dataclass
class APIConfig:
    """API Configuration"""
    eventbrite_token: Optional[str] = os.getenv("EVENTBRITE_API_TOKEN", "")
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY", "")
    huggingface_api_key: Optional[str] = os.getenv("HUGGINGFACE_API_KEY", "")
    ipinfo_token: Optional[str] = os.getenv("IPINFO_TOKEN", "")
    google_maps_api_key: Optional[str] = os.getenv("GOOGLE_MAPS_API_KEY", "")

@dataclass
class ScraperConfig:
    """Web Scraper Configuration"""
    max_search_time: int = 60  # Maximum time in seconds for web scraping
    max_workers: int = 10  # Maximum concurrent workers
    request_timeout: int = 10  # Request timeout in seconds
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    # Scraper-specific settings
    enable_sherlock: bool = True
    enable_photon: bool = True
    enable_harvester: bool = True
    enable_custom_search: bool = True
    
    # Search depth settings
    search_depth: int = 3  # 1-5, affects thoroughness vs speed
    max_results_per_source: int = 50

@dataclass
class EventConfig:
    """Event Search Configuration"""
    search_radius_miles: int = 50
    time_window_hours: int = 12
    max_events: int = 100
    min_relevance_score: float = 0.6
    
    # Event categories to prioritize
    priority_categories: List[str] = None
    
    def __post_init__(self):
        if self.priority_categories is None:
            self.priority_categories = [
                "music", "arts", "food", "sports", "technology",
                "business", "health", "community", "education"
            ]

@dataclass
class AIConfig:
    """AI Processing Configuration"""
    enable_ai: bool = True
    ai_provider: str = "openai"  # "openai", "huggingface", or "local"
    
    # Model settings
    openai_model: str = "gpt-3.5-turbo"
    huggingface_model: str = "facebook/bart-large-mnli"
    
    # Processing settings
    interest_extraction_confidence: float = 0.7
    relation_generation_enabled: bool = True
    max_interests_to_extract: int = 20
    
    # Prompts
    interest_extraction_prompt: str = """
    Based on the following information about a person, extract their likely interests 
    and hobbies. Return a JSON list of interests with confidence scores (0-1).
    
    Information: {data}
    
    Format: [{"interest": "...", "confidence": 0.X, "reasoning": "..."}]
    """
    
    relation_generation_prompt: str = """
    Given these facts about a person: {facts}
    
    Generate related interests they might have. For example:
    - "owns a dog" → "animal lover", "outdoor activities"
    - "software developer" → "technology events", "hackathons"
    
    Return as JSON: [{"derived_interest": "...", "source_fact": "...", "confidence": 0.X}]
    """

@dataclass
class SecurityConfig:
    """Security Configuration"""
    enable_rate_limiting: bool = True
    requests_per_minute: int = 60
    enable_data_anonymization: bool = True
    log_sensitive_data: bool = False
    secure_session_timeout: timedelta = timedelta(hours=1)
    
    # Data retention
    cache_expiry_hours: int = 24
    user_data_retention_days: int = 7

@dataclass
class AppConfig:
    """Main Application Configuration"""
    # Flask settings
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", 5000))
    secret_key: str = os.getenv("SECRET_KEY", os.urandom(24).hex())
    
    # Component configs
    api: APIConfig = None
    scraper: ScraperConfig = None
    events: EventConfig = None
    ai: AIConfig = None
    security: SecurityConfig = None
    
    # Paths
    base_dir: str = os.path.dirname(os.path.abspath(__file__))
    data_dir: str = os.path.join(base_dir, "data")
    cache_dir: str = os.path.join(data_dir, "cache")
    logs_dir: str = os.path.join(data_dir, "logs")
    temp_dir: str = os.path.join(data_dir, "temp")
    
    def __post_init__(self):
        # Initialize sub-configs if not provided
        if self.api is None:
            self.api = APIConfig()
        if self.scraper is None:
            self.scraper = ScraperConfig()
        if self.events is None:
            self.events = EventConfig()
        if self.ai is None:
            self.ai = AIConfig()
        if self.security is None:
            self.security = SecurityConfig()
        
        # Create necessary directories
        for directory in [self.data_dir, self.cache_dir, self.logs_dir, self.temp_dir]:
            os.makedirs(directory, exist_ok=True)
    
    def validate(self) -> Dict[str, List[str]]:
        """Validate configuration and return any warnings/errors"""
        issues = {"warnings": [], "errors": []}
        
        # Check API keys
        if not self.api.eventbrite_token:
            issues["errors"].append("EventBrite API token is required")
        
        if self.ai.enable_ai and self.ai.ai_provider == "openai" and not self.api.openai_api_key:
            issues["warnings"].append("OpenAI API key not set, AI features will be limited")
        
        if self.ai.enable_ai and self.ai.ai_provider == "huggingface" and not self.api.huggingface_api_key:
            issues["warnings"].append("HuggingFace API key not set, AI features will be limited")
        
        # Validate numeric ranges
        if not 1 <= self.scraper.search_depth <= 5:
            issues["errors"].append("Search depth must be between 1 and 5")
        
        if self.events.search_radius_miles <= 0:
            issues["errors"].append("Search radius must be positive")
        
        if self.events.time_window_hours <= 0:
            issues["errors"].append("Time window must be positive")
        
        return issues

# Global config instance
config = AppConfig()
