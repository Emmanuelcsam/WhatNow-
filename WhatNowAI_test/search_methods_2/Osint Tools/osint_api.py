#!/usr/bin/env python3
"""
OSINT Engine API Interface
Simple HTTP API for AI system integration
"""

import json
import sys
from pathlib import Path
from typing import Dict, Optional

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from flask import Flask, request, jsonify
    from flask_cors import CORS
except ImportError:
    print("Installing Flask for API interface...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "flask", "flask-cors"], check=True)
    from flask import Flask, request, jsonify
    from flask_cors import CORS

from osint_engine_ai import OSINTEngine

app = Flask(__name__)
CORS(app)  # Enable CORS for browser integration

# Initialize OSINT Engine
engine = OSINTEngine(enable_logging=False)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'OSINT Engine API'})

@app.route('/investigate', methods=['POST'])
def investigate():
    """
    Main investigation endpoint
    
    Expected JSON payload:
    {
        "name": "John Doe",
        "email": "john@example.com",
        "social_handles": ["johndoe", "jdoe"],
        "location": {"latitude": 36.8468, "longitude": -76.2852},
        "browser_location": {"latitude": 36.8468, "longitude": -76.2852}
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Extract parameters
        name = data.get('name', '')
        email = data.get('email', '')
        social_handles = data.get('social_handles', [])
        
        # Handle location data
        location_coords = None
        if data.get('location'):
            loc = data['location']
            if loc.get('latitude') and loc.get('longitude'):
                location_coords = (loc['latitude'], loc['longitude'])
        
        browser_location = data.get('browser_location')
        
        # Validate input
        if not name and not email:
            return jsonify({'error': 'Must provide either name or email'}), 400
        
        # Run investigation
        results = engine.investigate(
            name=name,
            email=email,
            social_handles=social_handles,
            location_coords=location_coords,
            browser_location=browser_location
        )
        
        # Export for AI consumption
        ai_export = json.loads(engine.export_for_ai(results))
        
        return jsonify(ai_export)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/interests', methods=['POST'])
def get_interests():
    """
    Get interests only
    
    Expected JSON payload: same as /investigate
    Returns: {"interests": ["technology", "art", ...], "keywords": ["tech", "creative", ...]}
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Quick investigation for interests only
        name = data.get('name', '')
        email = data.get('email', '')
        social_handles = data.get('social_handles', [])
        
        location_coords = None
        if data.get('location'):
            loc = data['location']
            if loc.get('latitude') and loc.get('longitude'):
                location_coords = (loc['latitude'], loc['longitude'])
        
        browser_location = data.get('browser_location')
        
        if not name and not email:
            return jsonify({'error': 'Must provide either name or email'}), 400
        
        results = engine.investigate(
            name=name,
            email=email,
            social_handles=social_handles,
            location_coords=location_coords,
            browser_location=browser_location
        )
        
        interests = results.get('extracted_interests', [])
        keywords = engine.get_interests_keywords(results)
        
        return jsonify({
            'interests': interests,
            'keywords': keywords,
            'success': results.get('success', False)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/norfolk-events', methods=['POST'])
def get_norfolk_events():
    """
    Get Norfolk events for a person based on their interests
    
    Expected JSON payload: same as /investigate
    Returns: {"events": [...], "is_norfolk_area": true/false}
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Check if location is provided
        location_coords = None
        if data.get('location'):
            loc = data['location']
            if loc.get('latitude') and loc.get('longitude'):
                location_coords = (loc['latitude'], loc['longitude'])
        
        browser_location = data.get('browser_location')
        if browser_location and not location_coords:
            location_coords = (
                browser_location.get('latitude'),
                browser_location.get('longitude')
            )
        
        if not location_coords:
            return jsonify({'error': 'Location coordinates required for Norfolk events'}), 400
        
        # Run quick investigation to get interests
        name = data.get('name', '')
        email = data.get('email', '')
        social_handles = data.get('social_handles', [])
        
        results = engine.investigate(
            name=name,
            email=email,
            social_handles=social_handles,
            location_coords=location_coords,
            browser_location=browser_location
        )
        
        is_norfolk = results.get('location_intel', {}).get('is_norfolk_area', False)
        norfolk_events = results.get('norfolk_events', {})
        
        return jsonify({
            'is_norfolk_area': is_norfolk,
            'events': norfolk_events.get('events', []) if norfolk_events else [],
            'news_items': norfolk_events.get('news_items', []) if norfolk_events else [],
            'user_interests': results.get('extracted_interests', []),
            'events_filtered': norfolk_events.get('filter_applied', False) if norfolk_events else False
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/location-check', methods=['POST'])
def check_location():
    """
    Check if location is in Norfolk, VA area
    
    Expected JSON payload:
    {
        "location": {"latitude": 36.8468, "longitude": -76.2852}
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        location_coords = None
        if data.get('location'):
            loc = data['location']
            if loc.get('latitude') and loc.get('longitude'):
                location_coords = (loc['latitude'], loc['longitude'])
        
        browser_location = data.get('browser_location')
        if browser_location and not location_coords:
            location_coords = (
                browser_location.get('latitude'),
                browser_location.get('longitude')
            )
        
        if not location_coords:
            return jsonify({'error': 'Location coordinates required'}), 400
        
        # Quick location check
        results = engine.investigate(
            name="",
            email="",
            location_coords=location_coords
        )
        
        location_intel = results.get('location_intel', {})
        
        return jsonify({
            'is_norfolk_area': location_intel.get('is_norfolk_area', False),
            'address': location_intel.get('reverse_geocoding', {}).get('display_name', ''),
            'coordinates': location_coords
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description="OSINT Engine API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    print(f"Starting OSINT Engine API on {args.host}:{args.port}")
    print(f"Available endpoints:")
    print(f"  GET  /health - Health check")
    print(f"  POST /investigate - Full OSINT investigation")
    print(f"  POST /interests - Get interests only")
    print(f"  POST /norfolk-events - Get Norfolk events")
    print(f"  POST /location-check - Check if location is Norfolk area")
    
    app.run(host=args.host, port=args.port, debug=args.debug)
