
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
