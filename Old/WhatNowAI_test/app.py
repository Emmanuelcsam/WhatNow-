"""
WhatNowAI Enhanced Flask Application

An intelligent activity recommendation system with advanced OSINT capabilities that helps users
discover local events and activities based on their location, interests, and preferences.

Enhanced Features:
- Multi-step onboarding with text-to-speech guidance
- Multiple event API integrations (Ticketmaster, SeatGeek, Songkick, etc.)
- Enhanced OSINT capabilities for personalized recommendations
- Interactive maps with event visualization
- AI-powered search and recommendation engine
- Privacy-focused background research
"""
import logging.config
import sys
from flask import Flask

# Ensure Python 3.8+
if sys.version_info < (3, 8):
    print("Python 3.8+ is required for enhanced features")
    sys.exit(1)

from routes import main_bp
from config.settings import (
    FLASK_CONFIG, LOGGING_CONFIG, AUDIO_DIR,
    check_api_keys, ENHANCED_SEARCH_CONFIG
)
from services.tts_service import TTSService

# Configure logging
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# Import the consolidated routes (all features are now in main routes)
from routes import main_bp
ENHANCED_ROUTES_AVAILABLE = True  # All features are consolidated


def create_app() -> Flask:
    """
    Enhanced application factory function with all integrations

    Returns:
        Configured Flask application instance with enhanced features
    """
    app = Flask(__name__)

    # Determine which features are available
    # Set secret key for sessions
    app.config['SECRET_KEY'] = FLASK_CONFIG.get('SECRET_KEY', 'dev-key-change-in-production')

    # Enable async support
    app.config['PROPAGATE_EXCEPTIONS'] = True

    # Register the consolidated blueprint
    app.register_blueprint(main_bp)
    logger.info("Routes registered with all features enabled")

    # Initialize services
    tts_service = TTSService(str(AUDIO_DIR))

    # Cleanup old audio files on startup
    try:
        tts_service.cleanup_old_audio()
        logger.info("Audio cleanup completed")
    except Exception as e:
        logger.warning(f"Audio cleanup failed: {e}")

    # Log available features and capabilities
    logger.info("=== WhatNowAI Capabilities ===")
    logger.info("✓ All features enabled (consolidated version)")

    # Core features
    logger.info("✓ Text-to-speech guidance")
    logger.info("✓ Location detection and geocoding")
    logger.info("✓ Event discovery (Ticketmaster, Fallback sources)")
    logger.info("✓ Interactive mapping")

    # Enhanced features
    if ENHANCED_ROUTES_AVAILABLE:
        logger.info("✓ Advanced user profiling with web scraping")
        logger.info("✓ AI-powered relation detection")
        logger.info("✓ Multiple fallback event sources")
        logger.info("✓ Personalized recommendations")
        logger.info("✓ Comprehensive OSINT integration")

    if ENHANCED_SEARCH_CONFIG.get('ENABLE_DEEP_SEARCH'):
        logger.info("✓ Deep search capabilities enabled")

    if ENHANCED_SEARCH_CONFIG.get('ENABLE_SOCIAL_SEARCH'):
        logger.info("✓ Social media search enabled")

    logger.info("==============================")
    logger.info("WhatNowAI application initialized successfully")
    return app


def main():
    """Main entry point"""
    # Check API keys on startup
    try:
        check_api_keys()
    except Exception as e:
        logger.warning(f"API key check failed: {e}")
        logger.info("Continuing with available services...")

    app = create_app()

    logger.info(f"Starting WhatNowAI on {FLASK_CONFIG['HOST']}:{FLASK_CONFIG['PORT']}")
    logger.info("All systems initialized - ready for comprehensive user profiling!")

    app.run(
        debug=FLASK_CONFIG['DEBUG'],
        host=FLASK_CONFIG['HOST'],
        port=FLASK_CONFIG['PORT']
    )


if __name__ == '__main__':
    main()
