# OSINT Orchestrator Quick Start Guide

## Installation Steps

### 1. Setup Python Environment
```bash
# Create virtual environment
python -m venv osint_env

# Activate virtual environment
# On Windows:
osint_env\Scripts\activate
# On Linux/Mac:
source osint_env/bin/activate
```

### 2. Install Dependencies
```bash
# Navigate to your project directory
cd /path/to/your/search_methods_2

# Install all requirements
pip install -r Test_1/requirements.txt

# Install specific tool requirements
cd DaProfiler && pip install -r requirements.txt && cd ..
cd Photon && pip install -r requirements.txt && cd ..
cd theharvester && pip install -r requirements.txt && cd ..
cd sherlock && pip install -r requirements.txt && cd ..
cd Proton && pip install -r requirements.txt && cd ..
cd tookie && pip install -r requirements.txt && cd ..
```

### 3. Download Additional Components
```bash
# For DaProfiler - Download geckodriver if not present
# Windows: Already included as geckodriver.exe
# Linux/Mac:
wget https://github.com/mozilla/geckodriver/releases/latest/download/geckodriver-v0.33.0-linux64.tar.gz
tar -xzf geckodriver-v0.33.0-linux64.tar.gz -C DaProfiler/
```

### 4. Configure Tools
```bash
# Create configuration file
cd Test_1
python config_module.py  # This creates osint_config.json

# Or create custom config
cat > osint_config.json << EOF
{
    "scraper": {
        "enable_sherlock": true,
        "enable_photon": true,
        "enable_harvester": true,
        "enable_daprofiler": true,
        "enable_proton": true,
        "enable_snscrape": true,
        "enable_twint": true,
        "enable_tookie": true,
        "max_workers": 10,
        "async_timeout": 60
    }
}
EOF
```

## Basic Usage

### Simple Search
```bash
# Basic search
python Test_1/main_search.py "John" "Doe"

# With activity and location
python Test_1/main_search.py "John" "Doe" -a "software engineer" -l "San Francisco"

# With email for domain searches
python Test_1/main_search.py "John" "Doe" -e "john.doe@example.com"
```

### Advanced Usage
```bash
# Speed optimized search
python Test_1/main_search.py "John" "Doe" --speed

# Complete search (slower but thorough)
python Test_1/main_search.py "John" "Doe" --complete

# Use only specific tools
python Test_1/main_search.py "John" "Doe" --enable-only sherlock photon

# Disable specific tools
python Test_1/main_search.py "John" "Doe" --disable twint tookie

# Custom output location
python Test_1/main_search.py "John" "Doe" -o results/john_doe_search.json
```

## Testing Individual Tools

### Test Sherlock
```bash
cd sherlock
python sherlock.py johndoe
cd ..
```

### Test Photon
```bash
cd Photon
python photon.py -u "https://example.com" --level 2
cd ..
```

### Test theHarvester
```bash
cd theharvester
python theHarvester.py -d example.com -b google
cd ..
```

## Troubleshooting

### Common Issues and Solutions

1. **Import Errors**
   ```bash
   # Ensure you're in the right directory
   cd /path/to/search_methods_2
   
   # Add to Python path
   export PYTHONPATH="${PYTHONPATH}:${PWD}"
   ```

2. **Tool Not Found**
   ```bash
   # Check if tool is properly installed
   python -c "import sherlock; print('Sherlock OK')"
   
   # Reinstall specific tool
   pip install --force-reinstall sherlock
   ```

3. **Timeout Issues**
   ```python
   # Edit osint_config.json
   {
       "scraper": {
           "async_timeout": 120,  # Increase timeout
           "individual_timeout": {
               "sherlock": 60,
               "photon": 60
           }
       }
   }
   ```

4. **Memory Issues**
   ```bash
   # Reduce parallel workers
   python Test_1/main_search.py "John" "Doe" --speed
   
   # Or edit config
   "max_workers": 5  # Reduce from 10
   ```

5. **SSL/Certificate Errors**
   ```python
   # In osint_config.json
   {
       "security": {
           "ssl_verify": false  # Temporary fix
       }
   }
   ```

## Performance Monitoring

### Enable Debug Logging
```bash
# Set environment variable
export OSINT_LOGGING_LOG_LEVEL=DEBUG
python Test_1/main_search.py "John" "Doe"
```

### Monitor Resource Usage
```bash
# Install monitoring tools
pip install psutil memory-profiler

# Run with memory profiling
python -m memory_profiler Test_1/main_search.py "John" "Doe"
```

## Example Python Script

```python
import asyncio
from Test_1.scraper_orchestrator import ScraperOrchestrator, SearchQuery
from Test_1.config_module import Config

async def run_search():
    # Create config
    config = Config()
    config.optimize_for_speed()  # Or optimize_for_completeness()
    
    # Create orchestrator
    orchestrator = ScraperOrchestrator(config)
    
    # Create search query
    query = SearchQuery(
        first_name="John",
        last_name="Doe",
        activity="CEO",
        location="New York",
        additional_info={
            'domain': 'example.com'
        }
    )
    
    # Run search
    results = await orchestrator.search(query, timeout=60)
    
    # Process results
    for result in results:
        print(f"{result.source}: Found {len(result.urls)} URLs")
        if result.success:
            print(f"  Data: {result.data}")
        else:
            print(f"  Error: {result.error}")
    
    # Get summary
    summary = orchestrator.get_summary()
    print(f"\nTotal URLs found: {summary['total_urls_found']}")

# Run
asyncio.run(run_search())
```

## Security Best Practices

1. **Use VPN**: Always use a VPN when running OSINT searches
2. **Rate Limiting**: Don't remove delays between requests
3. **Rotate User Agents**: The config includes user agent rotation
4. **Respect robots.txt**: Keep `respect_robots_txt: true` in config
5. **Legal Compliance**: Only search public information

## Output Files

After a search, you'll get:
- `osint_results_[name]_[timestamp].json` - Full results
- `osint_results_[name]_[timestamp]_urls.txt` - List of all URLs
- `osint_scraper.log` - Debug log (if enabled)

## Next Steps

1. Review the results JSON file
2. Use the URLs for deeper investigation
3. Cross-reference data between different tools
4. Export findings to your reporting format
5. Consider implementing additional post-processing