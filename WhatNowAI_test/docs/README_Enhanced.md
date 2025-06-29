# WhatNowAI - Enhanced Activity Recommendation System

🚀 **Enhanced Version with Advanced OSINT Capabilities**

WhatNowAI is an intelligent activity recommendation system that helps users discover local events and activities based on their location, interests, and preferences. This enhanced version includes advanced OSINT (Open Source Intelligence) capabilities, multiple event API integrations, and AI-powered personalization.

## 🌟 New Enhanced Features

### 🔍 Advanced Search & OSINT Integration

- **Multi-source search engines** (DuckDuckGo, Serper API)
- **OSINT tools integration** from `search_methods_2`
- **Privacy-focused data gathering**
- **Social media intelligence** (GitHub, LinkedIn, Twitter, etc.)
- **Professional background research**
- **Enhanced user profiling**

### 🎯 Multiple Event APIs

- **Ticketmaster** - Major events and concerts
- **SeatGeek** - Sports, concerts, theater
- **AllEvents** - Local community events
- **Songkick** - Music events (planned)
- **Meetup** - Community meetups (planned)
- **PredictHQ** - Comprehensive event data (planned)

### 🤖 AI-Powered Features

- **Smart event ranking** based on user preferences
- **Natural Language Processing** for better understanding
- **Sentiment analysis** of user interests
- **Contextual recommendations**
- **Privacy-protected personalization**

### 🛡️ Privacy & Security

- **Privacy-first approach** to data collection
- **Rate limiting** for API protection
- **Secure configuration** management
- **Optional data scraping** with user consent
- **GDPR-compliant** data handling

## 📋 Prerequisites

- Python 3.8 or higher
- Virtual environment (recommended)
- API keys (see Configuration section)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd WhatNowAI_test

# Run the enhanced setup script
./setup_enhanced.sh
```

### 2. Configure API Keys

Edit `secrets.txt` with your API keys:

```bash
# Core Event APIs (at least one recommended)
TICKETMASTER_CONSUMER_KEY=your_ticketmaster_api_key
ALLEVENTS_API_KEY=your_allevents_api_key

# Enhanced APIs (optional but recommended)
SEATGEEK_CLIENT_ID=your_seatgeek_client_id
SEATGEEK_CLIENT_SECRET=your_seatgeek_client_secret
SONGKICK_API_KEY=your_songkick_api_key

# AI & Search (optional)
OPENAI_API_KEY=your_openai_api_key
SERPER_API_KEY=your_serper_api_key

# Security
SECRET_KEY=your_random_secret_key
```

### 3. Run the Application

```bash
source venv/bin/activate
python app.py
```

Visit `http://localhost:5002` to start discovering activities!

## 🔧 Manual Installation

If the setup script doesn't work, install manually:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p static/audio logs cache

# Copy example configuration
cp secrets.txt.example secrets.txt
```

## 🗝️ API Keys & Configuration

### Essential APIs

| Service | Purpose | Free Tier | Sign Up |
|---------|---------|-----------|---------|
| **Ticketmaster** | Major events | 5,000 calls/day | [Developer Portal](https://developer.ticketmaster.com/) |
| **AllEvents** | Local events | Varies | [AllEvents API](https://allevents.in/api) |

### Enhanced APIs (Optional)

| Service | Purpose | Free Tier | Sign Up |
|---------|---------|-----------|---------|
| **SeatGeek** | Sports, concerts | 1,000 calls/hour | [Platform](https://platform.seatgeek.com/) |
| **Songkick** | Music events | 1,000 calls/day | [API](https://www.songkick.com/developer) |
| **OpenAI** | AI features | $18 free credit | [Platform](https://platform.openai.com/) |
| **Serper** | Enhanced search | 1,000 searches/day | [Serper.dev](https://serper.dev/) |

### Configuration Options

Edit `config/settings.py` to customize:

```python
# Search timeout (seconds)
ENHANCED_SEARCH_CONFIG['TIMEOUT'] = 15

# Privacy mode
ENHANCED_SEARCH_CONFIG['PRIVACY_MODE'] = True

# Enable/disable features
ENHANCED_SEARCH_CONFIG['ENABLE_SOCIAL_SEARCH'] = True
ENHANCED_SEARCH_CONFIG['ENABLE_DEEP_SEARCH'] = True
```

## 🔍 Enhanced Search Capabilities

### OSINT Integration

The enhanced version integrates tools from `search_methods_2/`:

- **Person Search Engine** - Comprehensive person lookup
- **OSINT Engine** - Advanced intelligence gathering
- **Social Media Search** - Platform-specific searches
- **Privacy Protection** - Respects user privacy settings

### Search Features

- **Multi-engine search** (DuckDuckGo, Serper)
- **Social platform integration** (GitHub, LinkedIn, Twitter)
- **Professional background research**
- **Location-based activity discovery**
- **Interest-based event matching**

## 🎯 How It Works

### 1. User Onboarding

- **Text-to-speech guidance** through setup process
- **Location detection** or manual entry
- **Interest collection** and activity preferences
- **Optional social media handles** for personalization

### 2. Enhanced Search Process

```
User Input → Enhanced Search Service → Multiple APIs
                     ↓
OSINT Integration → Privacy Filter → AI Ranking
                     ↓
Personalized Results → Interactive Map → User
```

### 3. Event Discovery

- **Multiple API sources** for comprehensive coverage
- **AI-powered ranking** based on user profile
- **Real-time results** with caching for performance
- **Interactive map** with event visualization

## 🛡️ Privacy & Security Features

### Privacy Protection

- **Opt-in data collection** - Users control what data is gathered
- **Anonymous searches** when possible
- **Data minimization** - Only collect necessary information
- **No permanent storage** of sensitive data
- **Rate limiting** to prevent abuse

### Security Measures

- **API key encryption** in configuration
- **Session security** with Flask sessions
- **Input validation** on all user data
- **Error handling** to prevent information disclosure

## 📊 Performance Optimizations

### Search Optimization

- **Parallel API calls** for faster results
- **Timeout management** to prevent hanging
- **Result caching** for repeated searches
- **Smart rate limiting** across services

### Resource Management

- **Connection pooling** for HTTP requests
- **Memory optimization** for large result sets
- **Background cleanup** of temporary files
- **Efficient data structures** for search results

## 🔧 Troubleshooting

### Common Issues

#### "No events found"

- Check API keys in `secrets.txt`
- Verify location permissions
- Try broader search radius
- Check API rate limits

#### "Enhanced search failed"

- Install optional dependencies: `pip install duckduckgo-search nltk`
- Check OSINT tools in `search_methods_2/`
- Verify network connectivity
- Review error logs

#### "Import errors"

- Activate virtual environment: `source venv/bin/activate`
- Reinstall requirements: `pip install -r requirements.txt`
- Check Python version: `python --version`

### Debug Mode

Enable debug logging:

```python
# In config/settings.py
LOGGING_CONFIG['root']['level'] = 'DEBUG'
```

### Performance Issues

- Reduce search timeout in settings
- Disable AI features if too slow
- Use fewer API sources
- Clear cache directory

## 🔄 Updates from Original

### What's Enhanced

✅ **Multiple event APIs** instead of just Ticketmaster
✅ **OSINT capabilities** for better personalization
✅ **Privacy-focused design** with user control
✅ **AI-powered ranking** of events
✅ **Enhanced search** with multiple engines
✅ **Better error handling** and fallbacks
✅ **Rate limiting** for API protection
✅ **Modular architecture** for easier maintenance

### What's Fixed

✅ **Personalization now works** with enhanced search
✅ **Data scraping issues resolved** with OSINT integration
✅ **Better timeout handling** prevents hanging
✅ **Improved error messages** for troubleshooting
✅ **API key management** simplified

## 🚧 Development

### Project Structure

```
WhatNowAI_test/
├── app.py                          # Enhanced main application
├── routes.py                       # API routes with new features
├── config/settings.py              # Enhanced configuration
├── services/                       # Service layer
│   ├── enhanced_search_service.py  # Multi-engine search
│   ├── osint_integration.py        # OSINT tools integration
│   ├── seatgeek_service.py         # SeatGeek API
│   ├── rate_limiter.py             # API rate limiting
│   └── ...                         # Other services
├── searchmethods/                  # Search implementations
│   └── enhanced_background_search.py
├── search_methods_2/               # OSINT tools (integrated)
├── Upgrades/                       # Enhancement modules
└── requirements.txt                # Updated dependencies
```

### Adding New APIs

1. Create service in `services/new_service.py`
2. Add configuration to `config/settings.py`
3. Update rate limiting in `RATE_LIMIT_CONFIG`
4. Register in `routes.py`

### Contributing

- Follow privacy-first principles
- Add comprehensive error handling
- Include rate limiting for APIs
- Update documentation
- Test with limited API keys

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Support

### Getting Help

- Check the troubleshooting section above
- Review error logs in the console
- Verify API key configuration
- Test with minimal setup first

### Community

- Report issues with detailed error messages
- Include configuration (without API keys)
- Provide steps to reproduce problems
- Suggest feature improvements

---

**🎉 Ready to discover what's happening around you with enhanced intelligence!**

*Enhanced with privacy-focused OSINT capabilities and multi-source event discovery.*
