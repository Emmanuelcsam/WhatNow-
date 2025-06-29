"""
app.py - Main Flask web application
"""
import os
import logging
import secrets
import asyncio
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, List, Optional

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Length, Optional as OptionalValidator
from werkzeug.exceptions import HTTPException

# Import all our services
from config import config
from location_service import LocationService, LocationData
from scraper_orchestrator import ScraperOrchestrator, SearchQuery
from data_processor import DataProcessor
from ai_integration import AIIntegration
from eventbrite_service import EventBriteService
from map_service import MapService
from cache_service import CacheService, RateLimiter, SessionCache
from event_orchestrator import EventOrchestrator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(config.logs_dir, 'app.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = config.secret_key
app.config['WTF_CSRF_TIME_LIMIT'] = None
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = config.security.secure_session_timeout

# Enable CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri="memory://",
    default_limits=["200 per day", "50 per hour"] if config.security.enable_rate_limiting else []
)

# Initialize services
cache_service = CacheService(config)
rate_limiter = RateLimiter(cache_service)
session_cache = SessionCache(cache_service)
location_service = LocationService(config.api.ipinfo_token)
orchestrator = EventOrchestrator(config, cache_service)

# Setup rate limits
if config.security.enable_rate_limiting:
    rate_limiter.add_limit('search', config.security.requests_per_minute, 60)
    rate_limiter.add_limit('api', config.security.requests_per_minute * 2, 60)


# Forms
class UserInfoForm(FlaskForm):
    """User information form"""
    first_name = StringField('First Name', validators=[
        DataRequired(message="First name is required"),
        Length(min=2, max=50, message="First name must be 2-50 characters")
    ])
    last_name = StringField('Last Name', validators=[
        DataRequired(message="Last name is required"),
        Length(min=2, max=50, message="Last name must be 2-50 characters")
    ])
    activity = TextAreaField('What would you like to do?', validators=[
        DataRequired(message="Please tell us what you'd like to do"),
        Length(min=10, max=500, message="Activity description must be 10-500 characters")
    ])
    location_data = HiddenField()


# Decorators
def require_session(f):
    """Require valid session"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'session_id' not in session:
            flash('Session expired. Please start over.', 'error')
            return redirect(url_for('index'))
        
        session_data = session_cache.get_session(session['session_id'])
        if not session_data:
            flash('Session expired. Please start over.', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function


def validate_config(f):
    """Validate configuration before handling requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        issues = config.validate()
        if issues['errors']:
            logger.error(f"Configuration errors: {issues['errors']}")
            return jsonify({
                'error': 'Server configuration error',
                'details': issues['errors']
            }), 500
        return f(*args, **kwargs)
    return decorated_function


# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}")
    return render_template('500.html'), 500


@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        'error': 'Rate limit exceeded',
        'message': str(e.description)
    }), 429


@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return e
    
    logger.error(f"Unhandled exception: {e}", exc_info=True)
    return render_template('500.html'), 500


# Routes
@app.route('/')
@validate_config
def index():
    """Landing page"""
    # Create new session
    session_id = secrets.token_urlsafe(32)
    session['session_id'] = session_id
    session_cache.create_session(session_id, {
        'created_at': datetime.now().isoformat(),
        'step': 'location_detection'
    })
    
    return render_template('index.html')


@app.route('/api/detect-location', methods=['POST'])
@limiter.limit("10 per minute")
def detect_location():
    """Detect user location from IP"""
    try:
        # Get client IP
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
        
        # Check cache first
        cached_location = cache_service.get_user_location(client_ip)
        if cached_location:
            logger.info(f"Location cache hit for {client_ip}")
            return jsonify({
                'success': True,
                'location': cached_location,
                'cached': True
            })
        
        # Detect location
        location_data = location_service.get_location_from_ip(client_ip)
        
        if location_data:
            # Enrich location data
            location_data = location_service.enrich_location_data(location_data)
            
            # Convert to dict
            location_dict = location_data.to_dict()
            
            # Cache result
            cache_service.cache_user_location(client_ip, location_dict)
            
            # Store in session
            if 'session_id' in session:
                session_cache.update_session(session['session_id'], {
                    'location': location_dict,
                    'step': 'user_info'
                })
            
            return jsonify({
                'success': True,
                'location': location_dict,
                'cached': False
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Could not detect location'
            }), 400
            
    except Exception as e:
        logger.error(f"Location detection error: {e}")
        return jsonify({
            'success': False,
            'error': 'Location detection failed'
        }), 500


@app.route('/user-info')
@require_session
def user_info():
    """User information page"""
    form = UserInfoForm()
    
    # Get location from session
    session_data = session_cache.get_session(session['session_id'])
    location = session_data.get('location', {})
    
    return render_template('user_info.html', form=form, location=location)


@app.route('/api/search', methods=['POST'])
@require_session
@limiter.limit("5 per minute")
def search():
    """Process user search and find events"""
    try:
        # Check rate limit
        if not rate_limiter.check_limit('search', session['session_id']):
            return jsonify({
                'error': 'Rate limit exceeded. Please wait before searching again.'
            }), 429
        
        # Validate form
        form = UserInfoForm()
        if not form.validate_on_submit():
            return jsonify({
                'success': False,
                'errors': form.errors
            }), 400
        
        # Get session data
        session_data = session_cache.get_session(session['session_id'])
        location = session_data.get('location', {})
        
        if not location:
            return jsonify({
                'success': False,
                'error': 'Location data missing'
            }), 400
        
        # Create search query
        search_query = {
            'first_name': form.first_name.data,
            'last_name': form.last_name.data,
            'activity': form.activity.data,
            'location': location
        }
        
        # Update session
        session_cache.update_session(session['session_id'], {
            'search_query': search_query,
            'step': 'processing'
        })
        
        # Check cache
        cache_key = f"{search_query['first_name']}_{search_query['last_name']}_{search_query['activity'][:20]}"
        cached_events = cache_service.get_events(cache_key)
        
        if cached_events:
            logger.info("Using cached event results")
            return jsonify({
                'success': True,
                'cached': True,
                'redirect': url_for('results')
            })
        
        # Start async processing
        asyncio.create_task(
            orchestrator.process_search_async(
                search_query,
                session['session_id']
            )
        )
        
        return jsonify({
            'success': True,
            'cached': False,
            'redirect': url_for('processing')
        })
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({
            'success': False,
            'error': 'Search processing failed'
        }), 500


@app.route('/processing')
@require_session
def processing():
    """Processing status page"""
    session_data = session_cache.get_session(session['session_id'])
    return render_template('processing.html', session_data=session_data)


@app.route('/api/status/<session_id>')
@limiter.limit("30 per minute")
def get_status(session_id):
    """Get processing status"""
    session_data = session_cache.get_session(session_id)
    
    if not session_data:
        return jsonify({'error': 'Session not found'}), 404
    
    status = session_data.get('processing_status', {})
    
    return jsonify({
        'status': status.get('status', 'unknown'),
        'progress': status.get('progress', 0),
        'message': status.get('message', ''),
        'complete': status.get('complete', False),
        'error': status.get('error')
    })


@app.route('/results')
@require_session
def results():
    """Results page"""
    session_data = session_cache.get_session(session['session_id'])
    
    # Get search results
    search_query = session_data.get('search_query', {})
    events = session_data.get('events', [])
    processed_data = session_data.get('processed_data', {})
    
    if not events:
        flash('No events found. Please try a different search.', 'warning')
        return redirect(url_for('user_info'))
    
    # Create map
    map_service = MapService(config)
    location = session_data.get('location', {})
    user_location = (location.get('latitude', 0), location.get('longitude', 0))
    
    map_html = map_service.create_event_map(
        events,
        user_location,
        config.events.search_radius_miles
    )
    
    return render_template(
        'results.html',
        events=events,
        map_html=map_html,
        search_query=search_query,
        processed_data=processed_data,
        location=location
    )


@app.route('/api/events/<event_id>')
@limiter.limit("20 per minute")
def get_event_details(event_id):
    """Get detailed event information"""
    try:
        eventbrite_service = EventBriteService(config)
        details = eventbrite_service.get_event_details(event_id)
        
        if details:
            return jsonify({
                'success': True,
                'event': details
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Event not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Event details error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch event details'
        }), 500


@app.route('/api/export/<format>')
@require_session
def export_results(format):
    """Export results in various formats"""
    if format not in ['json', 'csv', 'ics']:
        return jsonify({'error': 'Invalid format'}), 400
    
    session_data = session_cache.get_session(session['session_id'])
    events = session_data.get('events', [])
    
    if format == 'json':
        return jsonify({
            'events': events,
            'search_query': session_data.get('search_query', {}),
            'location': session_data.get('location', {}),
            'exported_at': datetime.now().isoformat()
        })
    
    elif format == 'csv':
        # Create CSV
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'name', 'date', 'time', 'venue', 'distance', 'category', 
            'relevance', 'url'
        ])
        
        writer.writeheader()
        for event in events:
            writer.writerow({
                'name': event['name'],
                'date': event.get('date', ''),
                'time': event.get('time', ''),
                'venue': event.get('venue', ''),
                'distance': event.get('distance', ''),
                'category': event.get('category', ''),
                'relevance': event.get('relevance', ''),
                'url': event.get('url', '')
            })
        
        output.seek(0)
        return output.getvalue(), 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename=events.csv'
        }
    
    elif format == 'ics':
        # Create iCalendar
        from icalendar import Calendar, Event as CalEvent
        
        cal = Calendar()
        cal.add('prodid', '-//Event Discovery App//EN')
        cal.add('version', '2.0')
        
        for event in events:
            # Parse event data and create calendar event
            # This is simplified - would need proper date parsing
            cal_event = CalEvent()
            cal_event.add('summary', event['name'])
            cal_event.add('location', event.get('venue', ''))
            cal_event.add('url', event.get('url', ''))
            
            cal.add_component(cal_event)
        
        return cal.to_ical(), 200, {
            'Content-Type': 'text/calendar',
            'Content-Disposition': 'attachment; filename=events.ics'
        }


@app.route('/api/feedback', methods=['POST'])
@require_session
@limiter.limit("10 per hour")
def submit_feedback():
    """Submit user feedback"""
    try:
        data = request.get_json()
        
        # Log feedback (in production, save to database)
        logger.info(f"User feedback: {data}")
        
        return jsonify({
            'success': True,
            'message': 'Thank you for your feedback!'
        })
        
    except Exception as e:
        logger.error(f"Feedback error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to submit feedback'
        }), 500


@app.route('/health')
def health_check():
    """Health check endpoint"""
    health = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'cache': cache_service.get_stats(),
            'ai': AIIntegration(config).get_status() if config.ai.enable_ai else {'enabled': False}
        }
    }
    
    return jsonify(health)


@app.route('/privacy')
def privacy_policy():
    """Privacy policy page"""
    return render_template('privacy.html')


@app.route('/terms')
def terms_of_service():
    """Terms of service page"""
    return render_template('terms.html')


# CLI commands
@app.cli.command()
def init_db():
    """Initialize database"""
    print("Initializing database...")
    # Add database initialization logic here
    print("Database initialized!")


@app.cli.command()
def clear_cache():
    """Clear all cache"""
    cache_service.clear()
    print("Cache cleared!")


@app.cli.command()
def test_services():
    """Test all services"""
    print("Testing services...")
    
    # Test location service
    try:
        location = location_service.get_location_from_ip()
        print(f"✓ Location service: {location.city if location else 'Failed'}")
    except Exception as e:
        print(f"✗ Location service: {e}")
    
    # Test EventBrite
    try:
        eb = EventBriteService(config)
        print(f"✓ EventBrite service: {'Enabled' if eb.enabled else 'Disabled'}")
    except Exception as e:
        print(f"✗ EventBrite service: {e}")
    
    # Test AI
    try:
        ai = AIIntegration(config)
        print(f"✓ AI service: {ai.get_status()}")
    except Exception as e:
        print(f"✗ AI service: {e}")
    
    print("Service test complete!")


if __name__ == '__main__':
    # Validate configuration
    issues = config.validate()
    if issues['errors']:
        logger.error(f"Configuration errors: {issues['errors']}")
        print("Please fix configuration errors before starting the application.")
        exit(1)
    
    if issues['warnings']:
        for warning in issues['warnings']:
            logger.warning(warning)
    
    # Start the application
    app.run(
        host=config.host,
        port=config.port,
        debug=config.debug
    )
