"""
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
