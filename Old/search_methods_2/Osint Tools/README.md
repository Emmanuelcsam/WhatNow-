# Advanced OSINT Scraper

A comprehensive Open Source Intelligence (OSINT) scraper that integrates multiple powerful tools including Maigret, Recon-ng, and SpiderFoot for thorough intelligence gathering.

## Features

- **Username Enumeration**: Uses Maigret to find social media profiles across 2000+ platforms
- **Domain Reconnaissance**: Leverages Recon-ng for comprehensive domain intelligence
- **Automated OSINT Scanning**: Integrates SpiderFoot for wide-ranging automated reconnaissance
- **API Integrations**: Supports multiple APIs for enhanced data gathering
- **Location Intelligence**: Analyzes geographical information
- **Breach Checking**: Integrates with Have I Been Pwned for compromise detection
- **Comprehensive Reporting**: Generates detailed investigation reports

## Supported Tools

### Primary Tools
- **Maigret**: Username enumeration across social media platforms
- **Recon-ng**: Web reconnaissance framework
- **SpiderFoot**: Automated OSINT reconnaissance tool

### API Integrations
- Shodan (IP/Network reconnaissance)
- Hunter.io (Email enumeration)
- Have I Been Pwned (Breach checking)
- VirusTotal (File/URL analysis)
- Clearbit (Company/Person enrichment)

## Installation

### Prerequisites
- Python 3.7 or higher
- Git
- Internet connection

### Quick Setup

1. Clone or download this repository
2. Run the setup script:
   ```powershell
   python setup.py
   ```
3. Edit the `.env` file with your API keys
4. Initialize the OSINT tools:
   ```powershell
   python osint_scraper.py --setup
   ```

### Manual Installation

1. Install Python dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

2. Create necessary directories:
   ```powershell
   mkdir tools, output, logs
   ```

3. Copy `.env.example` to `.env` and add your API keys

## Configuration

### API Keys

Edit the `.env` file to add your API keys:

```env
SHODAN_API_KEY=your_shodan_api_key_here
VIRUSTOTAL_API_KEY=your_virustotal_api_key_here
HIBP_API_KEY=your_hibp_api_key_here
HUNTER_API_KEY=your_hunter_api_key_here
CLEARBIT_API_KEY=your_clearbit_api_key_here
```

### Getting API Keys

- **Shodan**: Sign up at [shodan.io](https://www.shodan.io/)
- **Hunter.io**: Register at [hunter.io](https://hunter.io/)
- **Have I Been Pwned**: Get API access at [haveibeenpwned.com](https://haveibeenpwned.com/API/Key)
- **VirusTotal**: Sign up at [virustotal.com](https://www.virustotal.com/)
- **Clearbit**: Register at [clearbit.com](https://clearbit.com/)

## Usage

### Interactive Mode

Run the scraper in interactive mode for guided investigation:

```powershell
python osint_scraper.py --interactive
```

### Command Line Mode

Specify target information directly:

```powershell
python osint_scraper.py --name "John Doe" --email "john@example.com" --social "johndoe" "john.doe" --address "123 Main St" --coordinates 40.7128 -74.0060
```

### Options

- `--setup`: Setup and install OSINT tools
- `--name`: Target's full name
- `--email`: Target's email address
- `--social`: Social media handles (space-separated)
- `--address`: Target's physical address
- `--coordinates`: Latitude and longitude (space-separated)
- `--interactive`: Run in interactive mode

## Tool Integration Details

### Maigret Integration

Maigret is integrated to perform username enumeration across 2000+ social media platforms:

- Automatically generates username variants from full names
- Searches across major social platforms
- Provides detailed results with profile URLs
- Supports timeout configuration for reliability

### Recon-ng Integration

Recon-ng provides comprehensive domain reconnaissance:

- Creates isolated workspaces for each investigation
- Runs multiple reconnaissance modules
- Gathers DNS information, subdomains, and hosts
- Provides structured output for analysis

### SpiderFoot Integration

SpiderFoot offers automated OSINT scanning:

- Performs comprehensive target scanning
- Supports multiple data types (emails, domains, IPs)
- Generates detailed findings with categorization
- Provides extensive data correlation

## Output Structure

The scraper generates organized output in the following structure:

```
output/
├── investigation_[target]_[timestamp]/
│   ├── investigation_results.json
│   ├── maigret_results/
│   ├── recon_ng_results/
│   └── spiderfoot_results/
├── report_[target]_[timestamp].txt
└── logs/
    └── osint_[timestamp].log
```

## Security Considerations

### Legal and Ethical Use

- **Always obtain proper authorization** before conducting OSINT investigations
- Respect privacy laws and regulations (GDPR, CCPA, etc.)
- Use gathered information responsibly and ethically
- Follow your organization's policies and procedures

### Data Protection

- Secure storage of investigation results
- Proper handling of sensitive information
- Regular cleanup of temporary files
- Encryption of stored data when appropriate

### Rate Limiting

The scraper implements rate limiting to:
- Avoid overwhelming target services
- Prevent IP blocking
- Respect API usage limits
- Maintain operational security

## Advanced Features

### Custom Modules

The scraper supports custom modules for specialized investigations:

```python
from osint_utilities import OSINTUtilities

# Initialize with your API keys
utils = OSINTUtilities(api_keys)

# Comprehensive domain analysis
domain_results = utils.comprehensive_domain_analysis("example.com")

# Email investigation
email_results = utils.email_investigation("target@example.com")

# Location analysis
location_results = utils.location_analysis(40.7128, -74.0060)
```

### DNS Reconnaissance

Built-in DNS reconnaissance capabilities:

- DNS record enumeration (A, AAAA, MX, NS, TXT, CNAME)
- Reverse DNS lookups
- Subdomain enumeration
- DNS zone transfers (where permitted)

### WHOIS Integration

Comprehensive WHOIS analysis:

- Domain registration information
- Registrar details
- Creation and expiration dates
- Contact information (where available)

## Troubleshooting

### Common Issues

1. **Tool Installation Failures**
   - Ensure Git is installed and accessible
   - Check internet connectivity
   - Verify Python version compatibility

2. **API Rate Limiting**
   - Check API key validity
   - Verify API usage limits
   - Implement additional delays if needed

3. **Permission Errors**
   - Run with appropriate privileges
   - Check file system permissions
   - Ensure write access to output directories

### Debugging

Enable verbose logging by modifying the log level in the script:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

### Development Setup

For development, install additional dependencies:

```powershell
pip install pytest black flake8
```

Run tests:
```powershell
pytest tests/
```

## License

This project is intended for educational and authorized security research purposes only. Users are responsible for ensuring compliance with applicable laws and regulations.

## Disclaimer

This tool is for authorized and legal use only. The authors are not responsible for any misuse or illegal activities conducted with this software. Always obtain proper authorization before conducting any reconnaissance activities.

## Support

For support and questions:

1. Check the troubleshooting section
2. Review the logs in the `logs/` directory
3. Ensure all API keys are properly configured
4. Verify tool installations are complete

## Roadmap

Planned features and improvements:

- [ ] Web interface for easier operation
- [ ] Additional API integrations
- [ ] Enhanced reporting formats (PDF, HTML)
- [ ] Automated scheduling capabilities
- [ ] Machine learning for pattern recognition
- [ ] Integration with threat intelligence platforms
- [ ] Mobile app companion

## Version History

- **v1.0.0**: Initial release with core functionality
  - Maigret, Recon-ng, and SpiderFoot integration
  - Basic API support
  - Command-line and interactive interfaces
