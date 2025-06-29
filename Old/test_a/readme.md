# Event Discovery App 🗺️

A sophisticated web application that discovers personalized local events based on user interests through intelligent web scraping, AI-powered analysis, and real-time event matching.

## 🌟 Features

- **Automatic Location Detection**: Detects user location via IP geolocation
- **Deep Web Scraping**: Searches multiple sources to understand user interests
- **AI-Powered Analysis**: Optional AI integration for enhanced interest extraction
- **Real-Time Event Matching**: Finds events happening within the next 12 hours
- **Interactive Map Display**: Shows events on an OpenStreetMap interface
- **Smart Filtering**: Events within 50-mile radius with relevance scoring
- **Privacy-Focused**: Minimal data collection, no permanent storage

## 🏗️ Architecture

The application follows a modular architecture with these key components:

1. **Location Service** (`location_service.py`): IP-based geolocation
2. **Scraper Orchestrator** (`scraper_orchestrator.py`): Manages multiple web scrapers
3. **Data Processor** (`data_processor.py`): NLP-based interest extraction
4. **AI Integration** (`ai_integration.py`): Optional AI enhancement
5. **EventBrite Service** (`eventbrite_service.py`): Event search and filtering
6. **Map Service** (`map_service.py`): Interactive map generation
7. **Cache Service** (`cache_service.py`): Performance optimization
8. **Event Orchestrator** (`event_orchestrator.py`): Main workflow coordinator

## 📋 Requirements

- Python 3.8+
- Redis (optional, for caching)
- EventBrite API token (required)
- OpenAI API key (optional)
- HuggingFace API key (optional)
- IPInfo token (optional, for enhanced geolocation)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/event-discovery-app.git
cd event-discovery-app
```

### 2. Run Setup Script

```bash
python setup.py
```

This will:
- Check Python version
- Create necessary directories
- Generate `.env` file template
- Install dependencies (if confirmed)
- Download NLP data
- Check optional services

### 3. Configure API Keys

Edit the `.env` file and add your API keys:

```env
EVENTBRITE_API_TOKEN=your_eventbrite_token_here
OPENAI_API_KEY=your_openai_key_here_optional
HUGGINGFACE_API_KEY=your_huggingface_key_here_optional
IPINFO_TOKEN=your_ipinfo_token_here_optional
```

### 4. Start the Application

```bash
python app.py
```

Or use the startup script:

```bash
chmod +x run.sh
./run.sh
```

Visit `http://localhost:5000` in your browser.

## 🔧 Configuration

The application is highly configurable through `config.py`:

### Search Settings
- `max_search_time`: Maximum time for web scraping (default: 60s)
- `search_depth`: 1-5, affects thoroughness vs speed
- `max_results_per_source`: Limit results per scraper

### Event Settings
- `search_radius_miles`: Event search radius (default: 50)
- `time_window_hours`: Time window for events (default: 12)
- `max_events`: Maximum events to return (default: 100)

### AI Settings
- `enable_ai`: Enable/disable AI features
- `ai_provider`: Choose provider (openai, huggingface, local)
- `interest_extraction_confidence`: Minimum confidence threshold

### Security Settings
- `enable_rate_limiting`: API rate limiting
- `requests_per_minute`: Rate limit threshold
- `cache_expiry_hours`: Cache TTL

## 🔌 API Endpoints

### Core Endpoints
- `GET /`: Landing page
- `GET /user-info`: User information form
- `POST /api/detect-location`: Detect user location
- `POST /api/search`: Process search request
- `GET /api/status/<session_id>`: Get processing status
- `GET /results`: Display search results

### Utility Endpoints
- `GET /api/events/<event_id>`: Get event details
- `GET /api/export/<format>`: Export results (json, csv, ics)
- `POST /api/feedback`: Submit user feedback
- `GET /health`: Health check endpoint

## 🛠️ Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black .
flake8 .
```

### Adding New Scrapers

1. Add scraper method to `ScraperOrchestrator`
2. Implement data extraction logic
3. Register in `_initialize_scrapers()`

### Adding New AI Providers

1. Create new processor class inheriting from `AIProcessor`
2. Implement required methods
3. Register in `AIIntegration.__init__()`

## 🚢 Production Deployment

### Using Docker

```bash
docker-compose up -d
```

### Using Systemd (Linux)

```bash
sudo cp eventdiscovery.service /etc/systemd/system/
sudo systemctl enable eventdiscovery
sudo systemctl start eventdiscovery
```

### With Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 📊 Performance Optimization

### Caching Strategy
- Redis for high-performance caching
- Disk cache fallback
- Session-based result caching
- Location data caching (24h)
- Search results caching (1h)

### Scalability
- Async processing for long-running tasks
- Connection pooling for scrapers
- Rate limiting for API protection
- Horizontal scaling with load balancer

## 🔒 Security Considerations

- HTTPS enforcement in production
- Session security with secure cookies
- Rate limiting on all endpoints
- Input validation and sanitization
- No permanent storage of personal data
- API key encryption

## 🐛 Troubleshooting

### Common Issues

1. **Location detection fails**
   - Check internet connection
   - Try manual location entry
   - Verify IP is not VPN/proxy

2. **No events found**
   - Verify EventBrite API key
   - Check location accuracy
   - Try broader search terms

3. **Slow processing**
   - Enable Redis caching
   - Reduce search depth
   - Check network latency

### Debug Mode

Enable debug logging:

```env
DEBUG=True
```

Check logs:

```bash
tail -f data/logs/app.log
```

## 📚 API Documentation

### EventBrite API
- [EventBrite API Docs](https://www.eventbrite.com/platform/api)
- Required scopes: `event:read`

### Optional APIs
- [OpenAI API](https://platform.openai.com/docs)
- [HuggingFace API](https://huggingface.co/docs/api-inference)
- [IPInfo API](https://ipinfo.io/developers)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- EventBrite for event data API
- OpenStreetMap for mapping
- All open-source libraries used
- Community contributors

## 📞 Support

- Email: support@eventdiscovery.app
- Issues: GitHub Issues
- Documentation: [Wiki](https://github.com/yourusername/event-discovery-app/wiki)

---

Made with ❤️ by the Event Discovery Team
