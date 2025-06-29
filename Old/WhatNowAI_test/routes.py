"""
Flask application routes for WhatNowAI
Merged version combining features from routes.py and routes_enhanced.py

This module defines all the API endpoints for the WhatNowAI application, including:
- Onboarding flow with TTS integration
- Location services and geocoding
- Event discovery and mapping
- Background research and personalization
"""
from flask import Blueprint, render_template, request, jsonify, abort, send_file
import logging
from pathlib import Path
import os

# Core services imports
from services.tts_service import TTSService, get_introduction_text, INTRODUCTION_TEXTS
from services.geocoding_service import GeocodingService
from services.location_detection_service import LocationDetectionService
from services.mapping_service import MappingService
from services.user_profiling_service import EnhancedUserProfilingService
from services.fallback_event_service import FallbackEventService

# Enhanced location services
try:
    from services.enhanced_location_service import create_location_service
    from config.settings import LOCATION_CONFIG
    ENHANCED_LOCATION_AVAILABLE = True
except ImportError:
    ENHANCED_LOCATION_AVAILABLE = False
    create_location_service = None

# Optional enhanced services with error handling
# Advanced profiling is now integrated into the main user profiling service
ADVANCED_PROFILING_AVAILABLE = False
AdvancedProfilingService = None

try:
    from services.enhanced_integration_service import EnhancedIntegrationService
    INTEGRATION_SERVICE_AVAILABLE = True
except ImportError:
    INTEGRATION_SERVICE_AVAILABLE = False
    EnhancedIntegrationService = None

# Import existing services with error handling
try:
    from services.ticketmaster_service import TicketmasterService
    TICKETMASTER_AVAILABLE = True
except ImportError:
    TICKETMASTER_AVAILABLE = False
    TicketmasterService = None

# AllEvents service removed - API returns persistent 404 errors
ALLEVENTS_AVAILABLE = False

# Background search service
try:
    from searchmethods.enhanced_background_search import EnhancedBackgroundSearchService, UserProfile
    BACKGROUND_SEARCH_AVAILABLE = True
except ImportError:
    BACKGROUND_SEARCH_AVAILABLE = False
    EnhancedBackgroundSearchService = None
    UserProfile = None

# Configuration imports
from config.settings import (
    AUDIO_DIR, DEFAULT_TTS_VOICE,
    TICKETMASTER_API_KEY,
    TICKETMASTER_CONFIG, MAP_CONFIG
)

# Utils
from utils.helpers import validate_coordinates, generate_response_text

logger = logging.getLogger(__name__)

# Create blueprint
main_bp = Blueprint('main', __name__)

# Initialize core services (these are required)
tts_service = TTSService(str(AUDIO_DIR), DEFAULT_TTS_VOICE)
geocoding_service = GeocodingService()
location_detection_service = LocationDetectionService()
mapping_service = MappingService(MAP_CONFIG)
user_profiling_service = EnhancedUserProfilingService()
fallback_event_service = FallbackEventService()

# Initialize optional services
ticketmaster_service = None
if TICKETMASTER_AVAILABLE and TICKETMASTER_API_KEY:
    try:
        ticketmaster_service = TicketmasterService(TICKETMASTER_API_KEY, TICKETMASTER_CONFIG)
        logger.info("Ticketmaster service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Ticketmaster: {e}")

# AllEvents service removed - API returns persistent 404 errors

advanced_profiling_service = None
if ADVANCED_PROFILING_AVAILABLE:
    try:
        advanced_profiling_service = AdvancedProfilingService()
        logger.info("Advanced profiling service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize advanced profiling: {e}")

integration_service = None
if INTEGRATION_SERVICE_AVAILABLE:
    try:
        integration_config = {
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
            'TICKETMASTER_API_KEY': TICKETMASTER_API_KEY,
            'ALLEVENTS_API_KEY': None  # Removed - API not functional
        }
        integration_service = EnhancedIntegrationService(integration_config)
        logger.info("Enhanced integration service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize integration service: {e}")

# Initialize enhanced location service
enhanced_location_service = None
if ENHANCED_LOCATION_AVAILABLE:
    try:
        enhanced_location_service = create_location_service(
            ipstack_key=LOCATION_CONFIG.get('IPSTACK_API_KEY')
        )
        logger.info("Enhanced location service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize enhanced location service: {e}")


@main_bp.route('/')
def home():
    """Render the homepage with the form"""
    return render_template('home.html')


@main_bp.route('/tts/introduction/<step>', methods=['POST'])
def generate_introduction_tts(step: str):
    """Generate TTS for introduction steps"""
    try:
        # Get any location data from request for context
        data = request.get_json() if request.is_json else {}
        location_data = data.get('location')

        # Generate dynamic text based on time and location
        text = get_introduction_text(step, location_data)

        # Fallback to static text if dynamic generation fails
        if not text:
            text = INTRODUCTION_TEXTS.get(step)

        if not text:
            return jsonify({
                'success': False,
                'message': 'Invalid introduction step'
            }), 400

        audio_id, _ = tts_service.generate_audio_sync(text)

        if audio_id:
            return jsonify({
                'success': True,
                'audio_id': audio_id,
                'text': text
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to generate audio'
            }), 500

    except Exception as e:
        logger.error(f"Error generating introduction TTS: {e}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while generating audio'
        }), 500


@main_bp.route('/submit', methods=['POST'])
def submit_info():
    """Handle form submission with user's name and activity"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        activity = data.get('activity', '').strip()
        social = data.get('social', {})

        if not name or not activity:
            return jsonify({
                'success': False,
                'message': 'Please provide both your name and what you want to do.'
            }), 400

        # Process the user input - start background processing
        response_message = f"Hello {name}! I'm processing your request to {activity}. Please wait while I work on this..."

        return jsonify({
            'success': True,
            'message': response_message,
            'name': name,
            'activity': activity,
            'social': social,
            'processing': True
        })

    except Exception as e:
        logger.error(f"Error in submit_info: {e}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while processing your request.'
        }), 500


@main_bp.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()

        if not message:
            return jsonify({
                'success': False,
                'message': 'Please provide a message.'
            }), 400

        # Simple response logic (can be enhanced with AI)
        response = f"I received your message: '{message}'. How can I help you further?"

        return jsonify({
            'success': True,
            'response': response
        })

    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while processing your message.'
        }), 500


@main_bp.route('/process', methods=['POST'])
def process_request():
    """Handle background processing of user request"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        activity = data.get('activity', '').strip()
        location_data = data.get('location', {})
        social_data = data.get('social', {})

        if not name or not activity:
            return jsonify({
                'success': False,
                'message': 'Missing name or activity information.'
            }), 400

        # Perform background search if available
        search_results = None
        search_summaries = None

        if BACKGROUND_SEARCH_AVAILABLE and UserProfile:
            try:
                logger.info(f"Starting enhanced background search for user: {name}")

                # Create user profile for search
                user_profile = UserProfile(
                    name=name,
                    location=f"{location_data.get('city', '')}, {location_data.get('country', '')}",
                    social_handles={
                        'twitter': social_data.get('twitter', ''),
                        'instagram': social_data.get('instagram', ''),
                        'github': social_data.get('github', ''),
                        'linkedin': social_data.get('linkedin', ''),
                        'tiktok': social_data.get('tiktok', ''),
                        'youtube': social_data.get('youtube', '')
                    },
                    activity=activity
                )

                # Perform background search using enhanced service
                enhanced_search_service = EnhancedBackgroundSearchService()
                search_data = enhanced_search_service.perform_search(user_profile)

                search_results = search_data.get('raw_results', {})
                search_summaries = search_data.get('summaries', {})

                total_results = search_data.get('total_results', 0)
                search_time = search_data.get('metadata', {}).get('search_time', 0)
                sources_used = search_data.get('metadata', {}).get('sources_used', [])

                logger.info(f"Enhanced search completed in {search_time:.2f}s. "
                           f"Found {total_results} results from {len(sources_used)} sources: {sources_used}")

            except Exception as search_error:
                logger.warning(f"Enhanced background search failed: {search_error}")

        # Default summaries if search failed or not available
        if not search_summaries:
            search_summaries = {
                'general': 'Profile analysis completed.',
                'social': 'Social media presence analyzed.',
                'location': 'Location-based preferences identified.',
                'activity': 'Activity preferences recorded.',
                'interests': 'Interest areas identified.'
            }

        # Generate response text with search context
        result = generate_response_text(name, activity, location_data, social_data, search_summaries)

        # Create enhanced user profile
        enhanced_user_profile = None
        recommendation_context = {}

        try:
            enhanced_user_profile = user_profiling_service.create_enhanced_profile(
                name=name,
                location=location_data,
                activity=activity,
                social_data=social_data if social_data else {},
                search_results={
                    'search_results': search_results if search_results else [],
                    'search_summaries': search_summaries if search_summaries else []
                }
            )

            if enhanced_user_profile:
                logger.info(f"Enhanced user profile created with {enhanced_user_profile.profile_completion:.1f}% completion")
                # Get recommendation context for events
                recommendation_context = user_profiling_service.get_recommendation_context(enhanced_user_profile)
            else:
                logger.warning("Enhanced user profile creation returned None")

        except Exception as profile_error:
            logger.warning(f"Enhanced user profiling failed: {profile_error}")
            enhanced_user_profile = None
            recommendation_context = {}

        # Prepare personalization data for later use
        personalization_data = {
            'search_results': search_results if search_results else [],
            'search_summaries': search_summaries if search_summaries else [],
            'user_profile': {
                'name': name,
                'activity': activity,
                'location': location_data,
                'social': social_data if social_data else {}
            },
            'enhanced_profile': recommendation_context if recommendation_context else {},
            'activity': activity,
            'interests': enhanced_user_profile.interests if enhanced_user_profile and hasattr(enhanced_user_profile, 'interests') else [],
            'profile_completion': enhanced_user_profile.profile_completion if enhanced_user_profile else 0
        }

        return jsonify({
            'success': True,
            'result': result,
            'name': name,
            'activity': activity,
            'location': location_data,
            'social': social_data,
            'search_summaries': search_summaries,
            'personalization_data': personalization_data,
            'enhanced_profile_completion': enhanced_user_profile.profile_completion if enhanced_user_profile else 0,
            'total_search_results': len(search_results) if search_results else 0,
            'redirect_to_map': True,
            'map_url': '/map'
        })

    except Exception as e:
        logger.error(f"Error in process_request: {e}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while processing your request.'
        }), 500


@main_bp.route('/geocode', methods=['POST'])
def reverse_geocode():
    """Reverse geocode latitude/longitude to get address information"""
    try:
        data = request.get_json()

        # Handle both reverse geocoding and forward geocoding
        if 'location' in data:
            # Forward geocoding (address to coordinates)
            location = data.get('location', '').strip()
            if not location:
                return jsonify({
                    'success': False,
                    'message': 'No location provided'
                }), 400

            coordinates = geocoding_service.geocode_address(location)
            if coordinates:
                return jsonify({
                    'success': True,
                    'coordinates': coordinates
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Could not geocode location'
                }), 404
        else:
            # Reverse geocoding (coordinates to address)
            latitude = data.get('latitude')
            longitude = data.get('longitude')

            # Try to convert to float if they're strings
            try:
                if latitude is not None:
                    latitude = float(latitude)
                if longitude is not None:
                    longitude = float(longitude)
            except (ValueError, TypeError) as e:
                logger.error(f"Failed to convert coordinates to float in geocode: {e}")
                return jsonify({
                    'success': False,
                    'message': 'Invalid coordinate format. Coordinates must be numbers.'
                }), 400

            if not validate_coordinates(latitude, longitude):
                return jsonify({
                    'success': False,
                    'message': 'Invalid latitude or longitude coordinates.'
                }), 400

            location_info = geocoding_service.reverse_geocode(latitude, longitude)

            if location_info:
                return jsonify({
                    'success': True,
                    'location': location_info
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to geocode location.'
                }), 500

    except Exception as e:
        logger.error(f"Error in reverse_geocode: {e}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while processing location.'
        }), 500


@main_bp.route('/detect_location', methods=['POST'])
@main_bp.route('/detect-location', methods=['POST'])  # Support both URL formats
def detect_location():
    """Detect user location using multiple methods"""
    try:
        data = request.get_json() or {}
        request_ip = request.remote_addr

        # Try to get location using advanced detection
        location_data = location_detection_service.get_user_location(request_ip)

        # Use browser coordinates if available
        if data and data.get('latitude') and data.get('longitude'):
            location_data.update({
                'latitude': float(data['latitude']),
                'longitude': float(data['longitude']),
                'accuracy': 'high',
                'source': 'browser'
            })

        if location_data.get('latitude') and location_data.get('longitude'):
            logger.info(f"Location detected: {location_data.get('city', 'Unknown')}, "
                       f"{location_data.get('state', 'Unknown')} via {location_data.get('source', 'unknown')}")
            return jsonify({
                'success': True,
                'location': location_data,
                'alternatives': location_detection_service.get_location_alternatives(location_data) if hasattr(location_detection_service, 'get_location_alternatives') else []
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Unable to detect location. Please enter manually.',
                'location': location_data
            }), 200

    except Exception as e:
        logger.error(f"Error in detect_location: {e}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while detecting location.',
            'location': {
                'latitude': None,
                'longitude': None,
                'city': 'Unknown',
                'state': 'Unknown',
                'country': 'Unknown',
                'confidence': 0.0,
                'source': 'error'
            }
        }), 500


@main_bp.route('/audio/<audio_id>')
def serve_audio(audio_id: str):
    """Serve generated audio files"""
    try:
        if not tts_service.audio_exists(audio_id):
            abort(404)

        # Get audio path and convert to Path object for enhanced version compatibility
        audio_path = tts_service.get_audio_path(audio_id)
        audio_path_obj = Path(audio_path)

        if audio_path_obj.exists():
            return send_file(
                str(audio_path_obj),
                mimetype='audio/mp3',
                as_attachment=False
            )
        else:
            abort(404)

    except Exception as e:
        logger.error(f"Audio serve error: {e}")
        abort(500)


@main_bp.route('/map/events', methods=['POST'])
def get_map_events():
    """Get events and activities for map display"""
    try:
        data = request.get_json()
        location_data = data.get('location', {})
        user_interests = data.get('interests', [])
        user_activity = data.get('activity', '')
        personalization_data = data.get('personalization_data', {})

        # Debug logging
        logger.info(f"Getting map events for location: {location_data}")
        logger.info(f"User activity: '{user_activity}'")

        latitude = location_data.get('latitude')
        longitude = location_data.get('longitude')

        # Try to convert to float if they're strings
        try:
            if latitude is not None:
                latitude = float(latitude)
            if longitude is not None:
                longitude = float(longitude)
        except (ValueError, TypeError) as e:
            logger.error(f"Failed to convert coordinates to float: {e}")
            return jsonify({
                'success': False,
                'message': 'Invalid coordinate format. Coordinates must be numbers.'
            }), 400

        if not validate_coordinates(latitude, longitude):
            logger.error(f"Got invalid coordinates: {latitude}, {longitude}")
            return jsonify({
                'success': False,
                'message': 'Valid location is required. Please go back to onboarding and share your location to find events near you.'
            }), 400

        # Clear previous markers
        mapping_service.clear_markers()

        all_events = []
        sources_used = []

        # Get events from Ticketmaster if available
        if ticketmaster_service:
            try:
                logger.info(f"Searching Ticketmaster events...")

                # Extract enhanced profile data if available
                enhanced_profile_data = personalization_data.get('enhanced_profile', {})
                user_profile_for_ai = None

                if enhanced_profile_data:
                    user_profile_for_ai = enhanced_profile_data
                elif personalization_data.get('user_profile'):
                    # Fallback to basic profile data
                    basic_profile = personalization_data['user_profile']
                    user_profile_for_ai = {
                        'name': basic_profile.get('name', ''),
                        'location': basic_profile.get('location', {}),
                        'primary_activity': basic_profile.get('activity', user_activity),
                        'interests': [],
                        'preferences': {'activity_style': 'balanced'},
                        'behavioral_patterns': {},
                        'activity_context': {'intent': 'seeking'},
                        'completion_score': 25
                    }

                ticketmaster_events = ticketmaster_service.search_events(
                    location=location_data,
                    user_interests=user_interests,
                    user_activity=user_activity,
                    personalization_data=personalization_data,
                    user_profile=user_profile_for_ai if hasattr(ticketmaster_service, 'search_events') else None
                )

                if ticketmaster_events:
                    mapping_service.add_ticketmaster_events(ticketmaster_events)
                    all_events.extend(ticketmaster_events)
                    sources_used.append('ticketmaster')
                    logger.info(f"Added {len(ticketmaster_events)} Ticketmaster events")

            except Exception as tm_error:
                logger.warning(f"Ticketmaster search failed: {tm_error}")

        # AllEvents API removed due to persistent 404 errors

        # Always use fallback service to ensure we have events
        try:
            logger.info(f"Searching fallback events...")

            fallback_events = fallback_event_service.search_events(
                latitude=latitude,
                longitude=longitude,
                radius=50,
                user_interests=user_interests
            )

            if fallback_events:
                # Format fallback events for mapping
                for event in fallback_events:
                    # Ensure required fields
                    if 'latitude' not in event:
                        event['latitude'] = latitude + (hash(event.get('name', '')) % 100 - 50) / 1000
                    if 'longitude' not in event:
                        event['longitude'] = longitude + (hash(event.get('name', '')) % 100 - 50) / 1000
                    if 'id' not in event:
                        event['id'] = f"fallback_{hash(event.get('name', ''))}"

                all_events.extend(fallback_events)
                sources_used.append('fallback')
                logger.info(f"Added {len(fallback_events)} fallback events")

                # Add to mapping service - use generic dict method
                for event in fallback_events:
                    try:
                        mapping_service.add_generic_event(event, source='fallback')
                    except Exception as e:
                        logger.warning(f"Failed to add fallback event to map: {e}")

        except Exception as fb_error:
            logger.error(f"Fallback event search failed: {fb_error}")

        # Get map data
        map_data = mapping_service.get_map_data(latitude, longitude)
        category_stats = mapping_service.get_category_stats()

        logger.info(f"Total events found: {len(all_events)} from sources: {sources_used}")

        return jsonify({
            'success': True,
            'map_data': map_data,
            'category_stats': category_stats,
            'total_events': len(mapping_service.get_all_markers()),
            'sources_used': sources_used
        })

    except Exception as e:
        logger.error(f"Error getting map events: {e}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while loading events.'
        }), 500


@main_bp.route('/map/search', methods=['POST'])
def search_map_events():
    """Search events on the map"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()

        if not query:
            return jsonify({
                'success': False,
                'message': 'Please provide a search query.'
            }), 400

        # Search markers
        matching_markers = mapping_service.search_markers(query)

        return jsonify({
            'success': True,
            'markers': [marker.to_dict() for marker in matching_markers],
            'total_results': len(matching_markers)
        })

    except Exception as e:
        logger.error(f"Error searching map events: {e}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while searching events.'
        }), 500


@main_bp.route('/map')
def map_view():
    """Render the map page"""
    # The map page will get user data from sessionStorage via JavaScript
    # We provide empty defaults that will be overridden by the frontend
    return render_template('map.html',
                         name='',
                         activity='',
                         location={},
                         social={})


@main_bp.route('/health')
def health_check():
    """Health check endpoint"""
    services_status = {
        'core': {
            'tts': True,
            'geocoding': True,
            'location_detection': True,
            'mapping': True,
            'user_profiling': True,
            'fallback_events': True
        },
        'optional': {
            'ticketmaster': ticketmaster_service is not None,
            'allevents': False,  # Removed - API not functional
            'background_search': BACKGROUND_SEARCH_AVAILABLE,
            'advanced_profiling': advanced_profiling_service is not None,
            'integration_service': integration_service is not None
        }
    }

    # Count active services
    active_core = sum(services_status['core'].values())
    active_optional = sum(services_status['optional'].values())
    total_core = len(services_status['core'])
    total_optional = len(services_status['optional'])

    return jsonify({
        'status': 'healthy',
        'services': services_status,
        'summary': {
            'core_services': f"{active_core}/{total_core} active",
            'optional_services': f"{active_optional}/{total_optional} active"
        },
        'version': '2.0.0-merged'
    })


# Error handlers
@main_bp.errorhandler(404)
def not_found(_):
    return jsonify({
        'success': False,
        'message': 'Resource not found'
    }), 404


@main_bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500


@main_bp.route('/api/location/from-ip', methods=['POST'])
def get_location_from_ip():
    """Enhanced IP-based location detection"""
    try:
        if not enhanced_location_service:
            return jsonify({
                'error': 'Enhanced location service not available'
            }), 503

        data = request.get_json() or {}
        ip_address = data.get('ip') or request.remote_addr

        # Get comprehensive location data
        location_result = enhanced_location_service.get_location_from_ip(ip_address)

        if location_result:
            logger.info(f"Enhanced IP location detected: {location_result.city}, {location_result.state}")
            return jsonify(location_result.to_dict())
        else:
            return jsonify({
                'error': 'Could not determine location from IP'
            }), 404

    except Exception as e:
        logger.error(f"Enhanced IP location error: {e}")
        return jsonify({
            'error': 'Location detection failed'
        }), 500


@main_bp.route('/api/location/reverse-geocode', methods=['POST'])
def reverse_geocode_coordinates():
    """Reverse geocode coordinates to address"""
    try:
        data = request.get_json() or {}
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        if not latitude or not longitude:
            return jsonify({
                'error': 'Latitude and longitude are required'
            }), 400

        if enhanced_location_service:
            # Use enhanced service for reverse geocoding
            location_data = enhanced_location_service._reverse_geocode_coordinates(
                float(latitude), float(longitude)
            )
        else:
            # Fallback to basic geocoding service
            location_data = geocoding_service.reverse_geocode(float(latitude), float(longitude))

        if location_data:
            return jsonify(location_data)
        else:
            return jsonify({
                'error': 'Could not reverse geocode coordinates'
            }), 404

    except Exception as e:
        logger.error(f"Reverse geocoding error: {e}")
        return jsonify({
            'error': 'Reverse geocoding failed'
        }), 500


@main_bp.route('/api/location/comprehensive', methods=['POST'])
def get_comprehensive_location():
    """Get comprehensive location using all available methods"""
    try:
        if not enhanced_location_service:
            return jsonify({
                'error': 'Enhanced location service not available'
            }), 503

        data = request.get_json() or {}
        ip_address = data.get('ip') or request.remote_addr
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        # Get comprehensive location data
        comprehensive_data = enhanced_location_service.get_comprehensive_location(
            ip_address=ip_address,
            lat=latitude,
            lon=longitude
        )

        logger.info(f"Comprehensive location data: confidence {comprehensive_data.get('confidence', 0):.2f}")
        return jsonify(comprehensive_data)

    except Exception as e:
        logger.error(f"Comprehensive location error: {e}")
        return jsonify({
            'error': 'Comprehensive location detection failed'
        }), 500


@main_bp.route('/api/location/validate', methods=['POST'])
def validate_location():
    """Validate location data"""
    try:
        if not enhanced_location_service:
            return jsonify({
                'error': 'Enhanced location service not available'
            }), 503

        data = request.get_json() or {}
        is_valid = enhanced_location_service.validate_location(data)

        return jsonify({
            'valid': is_valid,
            'data': data
        })

    except Exception as e:
        logger.error(f"Location validation error: {e}")
        return jsonify({
            'error': 'Location validation failed'
        }), 500


@main_bp.route('/api/location/geocode', methods=['POST'])
def geocode_address():
    """Geocode an address to coordinates"""
    try:
        data = request.get_json() or {}
        address = data.get('address')

        if not address:
            return jsonify({
                'error': 'Address is required'
            }), 400

        if enhanced_location_service:
            # Use enhanced service for geocoding
            location_result = enhanced_location_service.get_location_for_address(address)
            if location_result:
                return jsonify(location_result.to_dict())
        else:
            # Fallback to basic geocoding
            location_data = geocoding_service.geocode_address(address)
            if location_data:
                return jsonify(location_data)

        return jsonify({
            'error': 'Could not geocode address'
        }), 404

    except Exception as e:
        logger.error(f"Address geocoding error: {e}")
        return jsonify({
            'error': 'Address geocoding failed'
        }), 500


@main_bp.route('/api/location/test', methods=['GET', 'POST'])
def test_location_service():
    """Test endpoint to verify enhanced location service functionality"""
    try:
        if not enhanced_location_service:
            return jsonify({
                'error': 'Enhanced location service not available',
                'basic_service': geocoding_service is not None
            }), 503

        # Test IP detection
        user_ip = enhanced_location_service.get_user_ip()
        ip_location = None

        if user_ip:
            ip_location = enhanced_location_service.get_location_from_ip(user_ip)

        # Test comprehensive detection
        comprehensive_data = enhanced_location_service.get_comprehensive_location()

        return jsonify({
            'status': 'Enhanced location service operational',
            'detected_ip': user_ip,
            'ip_location': ip_location.to_dict() if ip_location else None,
            'comprehensive_data': comprehensive_data,
            'providers_count': len(enhanced_location_service.providers),
            'service_info': {
                'cache_size': len(enhanced_location_service.cache),
                'ipstack_available': any(p.name == 'IPStack' for p in enhanced_location_service.providers)
            }
        })

    except Exception as e:
        logger.error(f"Location service test error: {e}")
        return jsonify({
            'error': f'Location service test failed: {str(e)}'
        }), 500


@main_bp.route('/location-demo')
def location_demo():
    """Demo page for enhanced location detection"""
    return render_template('location_demo.html')
