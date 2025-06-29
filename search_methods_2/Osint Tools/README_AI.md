# OSINT Engine - AI Integration Ready

A streamlined OSINT (Open Source Intelligence) engine designed for integration with larger AI systems. This tool can investigate individuals using publicly available information and provides structured output for AI consumption.

## Key Features

✅ **AI-Ready**: Clean, structured APIs for AI system integration  
✅ **Norfolk-Specific**: Automatically detects Norfolk, VA residents and scrapes local events  
✅ **Interest Detection**: Extracts interests from OSINT data for personalized results  
✅ **Multiple Interfaces**: Command-line, Python API, and HTTP REST endpoints  
✅ **Free Services Only**: No paid API keys required  
✅ **Location-Aware**: Uses browser geolocation or coordinates  

## Quick Start for AI Systems

### 1. Simple Python Integration

```python
from simple_osint import investigate, get_interests, get_norfolk_events, is_norfolk_area

# Full investigation
result = investigate(
    name="John Doe",
    email="john@example.com", 
    social_handles=["johndoe"],
    latitude=36.8468,
    longitude=-76.2852
)

# Just get interests
interests = get_interests(name="John Doe", email="john@example.com")
# Returns: ['technology', 'art', 'community']

# Norfolk-specific events
norfolk_events = get_norfolk_events(
    name="John Doe",
    latitude=36.8468,
    longitude=-76.2852
)

# Quick location check
is_norfolk = is_norfolk_area(36.8468, -76.2852)  # True for Norfolk, VA
```

### 2. Command Line Integration

```bash
# Full investigation with JSON output
python simple_osint.py --name "John Doe" --email "john@example.com" --lat 36.8468 --lon -76.2852

# Get interests only
python simple_osint.py --name "John Doe" --mode interests

# Get Norfolk events only
python simple_osint.py --name "John Doe" --lat 36.8468 --lon -76.2852 --mode norfolk

# Check if location is Norfolk area
python simple_osint.py --lat 36.8468 --lon -76.2852 --mode location
```

### 3. HTTP API Integration

```bash
# Start the API server
python osint_api.py --host 0.0.0.0 --port 5000

# Use the API endpoints
curl -X POST http://localhost:5000/investigate \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "location": {"latitude": 36.8468, "longitude": -76.2852}
  }'
```

## Integration Examples

### For Large Language Models (LLMs)

```python
# LLM can call this to investigate a person mentioned in conversation
def investigate_person_for_llm(name, email=None, location=None):
    from simple_osint import investigate
    
    lat, lon = location if location else (None, None)
    result = investigate(name=name, email=email, latitude=lat, longitude=lon)
    
    return {
        'interests': result['interests'],
        'social_presence': result['social_platforms'],
        'norfolk_events': result.get('norfolk_events', {}),
        'location_context': result['location_info']
    }
```

### For Browser Extensions

```javascript
// Browser extension can use the HTTP API
async function investigateUser(userData) {
    const response = await fetch('http://localhost:5000/investigate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            name: userData.name,
            email: userData.email,
            browser_location: userData.location  // From navigator.geolocation
        })
    });
    
    return await response.json();
}
```

### For Chatbots

```python
# Chatbot integration
def get_personalized_norfolk_events(user_profile):
    from simple_osint import get_norfolk_events
    
    if user_profile.get('location') == 'norfolk_va':
        events = get_norfolk_events(
            name=user_profile.get('name'),
            email=user_profile.get('email'),
            latitude=36.8468,
            longitude=-76.2852
        )
        
        if events['is_norfolk_area'] and events['events']:
            return f"Found {len(events['events'])} events in Norfolk that match your interests!"
        
    return "No local events found for your area."
```

## Output Structure

### Investigation Result
```json
{
  "success": true,
  "target": {
    "name": "John Doe",
    "email": "john@example.com",
    "social_handles": ["johndoe"],
    "location": [36.8468, -76.2852]
  },
  "interests": ["technology", "art", "community"],
  "social_platforms": ["GitHub", "LinkedIn", "Instagram"],
  "location_info": {
    "is_norfolk_area": true,
    "address": "Norfolk, VA, United States",
    "nearby_amenities": [
      {"type": "restaurant", "count": 15},
      {"type": "museum", "count": 3}
    ]
  },
  "norfolk_events": {
    "events": [
      {
        "title": "Tech Meetup",
        "date": "Tonight 7:00 PM",
        "location": "Downtown Norfolk",
        "relevance_score": 3,
        "matched_interests": ["tech", "programming", "networking"]
      }
    ],
    "filter_applied": true,
    "user_interests": ["technology", "programming"]
  }
}
```

## File Structure

```
OSINTscrapper/
├── simple_osint.py          # Main AI interface (START HERE)
├── osint_engine_ai.py       # Core engine
├── osint_api.py             # HTTP API server
├── osint_utilities.py       # OSINT utilities
├── requirements.txt         # Dependencies
└── README_AI.md            # This file
```

## Dependencies

```bash
pip install requests beautifulsoup4 lxml python-dotenv colorama dnspython python-whois
```

Optional (for HTTP API):
```bash
pip install flask flask-cors
```

## Norfolk Feature

The system automatically detects if a person is located in Norfolk, Virginia (or surrounding Hampton Roads area) and:

1. **Location Detection**: Uses precise geographic boundaries
2. **Interest Matching**: Filters events based on detected interests from OSINT profile
3. **Event Scraping**: Pulls current events from NFK Currents website
4. **Relevance Scoring**: Ranks events by interest match

### Norfolk Coverage Area
- Norfolk, VA
- Virginia Beach, VA  
- Chesapeake, VA
- Portsmouth, VA
- Suffolk, VA
- Newport News, VA
- Hampton, VA

## Error Handling

The system gracefully handles:
- Missing dependencies (auto-installs when possible)
- Network failures
- Invalid coordinates
- Missing OSINT data
- Rate limiting

## Privacy & Ethics

- Only uses publicly available information
- No paid APIs or services that violate privacy
- Respects website rate limits
- No data storage beyond session

## Performance

- Typical investigation: 10-30 seconds
- Interest extraction: < 5 seconds  
- Norfolk location check: < 2 seconds
- Event filtering: < 1 second

## Troubleshooting

### Common Issues

1. **Import errors**: Run `pip install -r requirements.txt`
2. **Network timeouts**: Check internet connection
3. **No interests found**: Provide more social media handles
4. **Norfolk not detected**: Verify coordinates are in Hampton Roads area

### Debug Mode

```python
from osint_engine_ai import OSINTEngine

# Enable logging for debugging
engine = OSINTEngine(enable_logging=True)
result = engine.investigate(name="Test User")
```

## AI Integration Best Practices

1. **Batch Processing**: For multiple users, add delays between requests
2. **Caching**: Cache results for repeated queries
3. **Error Handling**: Always check the 'success' field in results
4. **Rate Limiting**: Respect external service limits
5. **Data Validation**: Validate coordinates and email formats

## Example AI Agent Integration

```python
class OSINTAgent:
    def __init__(self):
        from simple_osint import osint
        self.osint = osint
    
    def analyze_person(self, person_data):
        """AI agent method to analyze a person"""
        result = self.osint.investigate_person(
            name=person_data.get('name'),
            email=person_data.get('email'),
            social_handles=person_data.get('social_handles'),
            latitude=person_data.get('lat'),
            longitude=person_data.get('lon')
        )
        
        # AI can now use this structured data
        return self.process_osint_data(result)
    
    def process_osint_data(self, osint_result):
        """Process OSINT data for AI decision making"""
        interests = osint_result['interests']
        location = osint_result['location_info']
        events = osint_result.get('norfolk_events', {})
        
        # AI logic here
        return {
            'recommended_actions': self.generate_recommendations(interests),
            'local_context': self.analyze_location(location),
            'event_suggestions': events.get('events', [])
        }
```

---

**Ready for AI Integration!** 🤖

Start with `simple_osint.py` for the easiest integration path.
