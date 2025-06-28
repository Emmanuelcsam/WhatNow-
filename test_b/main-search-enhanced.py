"""
main_search.py - Enhanced main script for OSINT search orchestration
"""
import asyncio
import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional
import signal
import threading

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Test_1.scraper_orchestrator import ScraperOrchestrator, SearchQuery
from Test_1.config_module import Config

# Setup logging
def setup_logging(config: Config):
    """Setup logging configuration"""
    log_format = config.logging.log_format
    log_level = getattr(logging, config.logging.log_level.upper())
    
    # Console handler
    if config.logging.enable_console_log:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(console_handler)
    
    # File handler
    if config.logging.enable_file_log:
        file_handler = logging.FileHandler(config.logging.log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)
    
    logging.getLogger().setLevel(log_level)

class SearchMonitor:
    """Monitor search progress and provide real-time updates"""
    
    def __init__(self):
        self.start_time = None
        self.scrapers_completed = 0
        self.total_scrapers = 0
        self.current_scraper = None
        self.urls_found = 0
        self.running = False
        self.lock = threading.Lock()
    
    def start(self, total_scrapers: int):
        """Start monitoring"""
        self.start_time = time.time()
        self.total_scrapers = total_scrapers
        self.running = True
        self.scrapers_completed = 0
        self.urls_found = 0
        
        # Start progress thread
        thread = threading.Thread(target=self._progress_loop)
        thread.daemon = True
        thread.start()
    
    def update(self, scraper_name: str, status: str = 'running'):
        """Update current scraper status"""
        with self.lock:
            self.current_scraper = scraper_name
            if status == 'completed':
                self.scrapers_completed += 1
    
    def add_urls(self, count: int):
        """Add to URL count"""
        with self.lock:
            self.urls_found += count
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
    
    def _progress_loop(self):
        """Display progress updates"""
        while self.running:
            elapsed = time.time() - self.start_time
            with self.lock:
                progress = (self.scrapers_completed / self.total_scrapers) * 100
                print(f"\r[{elapsed:.1f}s] Progress: {progress:.1f}% | "
                      f"Scrapers: {self.scrapers_completed}/{self.total_scrapers} | "
                      f"URLs: {self.urls_found} | "
                      f"Current: {self.current_scraper or 'Starting...'}    ", 
                      end='', flush=True)
            time.sleep(0.5)
        print()  # New line after completion

class OSINTSearcher:
    """Main OSINT search application"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config = Config(config_file)
        setup_logging(self.config)
        self.logger = logging.getLogger(__name__)
        self.orchestrator = ScraperOrchestrator(self.config)
        self.monitor = SearchMonitor()
        self.interrupted = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle interrupt signals"""
        self.logger.info("Received interrupt signal, gracefully shutting down...")
        self.interrupted = True
        self.monitor.stop()
    
    async def search(self, 
                    first_name: str,
                    last_name: str,
                    activity: str = "",
                    location: Optional[str] = None,
                    additional_info: Optional[Dict] = None,
                    output_file: Optional[str] = None) -> Dict:
        """
        Execute OSINT search
        
        Args:
            first_name: Target's first name
            last_name: Target's last name
            activity: Target's activity/profession
            location: Target's location
            additional_info: Additional search parameters
            output_file: File to save results
            
        Returns:
            Dictionary with search results
        """
        # Create search query
        query = SearchQuery(
            first_name=first_name,
            last_name=last_name,
            activity=activity,
            location=location,
            additional_info=additional_info or {}
        )
        
        self.logger.info(f"Starting OSINT search for: {query.full_name}")
        self.logger.info(f"Enabled tools: {', '.join(self.config.get_enabled_tools())}")
        
        # Start monitoring
        enabled_tools = self.config.get_enabled_tools()
        self.monitor.start(len(enabled_tools) + 4)  # +4 for built-in scrapers
        
        # Execute search with monitoring
        try:
            # Create a wrapper to update monitor
            original_scrapers = self.orchestrator.scrapers.copy()
            
            for name, func in original_scrapers.items():
                def create_wrapper(scraper_name, scraper_func):
                    def wrapper(*args, **kwargs):
                        self.monitor.update(scraper_name, 'running')
                        result = scraper_func(*args, **kwargs)
                        if result:
                            self.monitor.add_urls(len(result.urls))
                        self.monitor.update(scraper_name, 'completed')
                        return result
                    return wrapper
                
                self.orchestrator.scrapers[name] = create_wrapper(name, func)
            
            # Run search
            results = await self.orchestrator.search(
                query, 
                timeout=self.config.scraper.async_timeout
            )
            
        except Exception as e:
            self.logger.error(f"Search error: {e}")
            raise
        finally:
            self.monitor.stop()
        
        # Process results
        summary = self.orchestrator.get_summary()
        
        # Compile final results
        final_results = {
            'query': {
                'full_name': query.full_name,
                'first_name': query.first_name,
                'last_name': query.last_name,
                'activity': query.activity,
                'location': query.location,
                'additional_info': query.additional_info
            },
            'summary': summary,
            'results': []
        }
        
        # Add detailed results from each scraper
        for result in results:
            result_data = {
                'source': result.source,
                'success': result.success,
                'urls_found': len(result.urls),
                'execution_time': result.execution_time,
                'data': result.data,
                'urls': result.urls[:10],  # Limit URLs in output
                'error': result.error
            }
            final_results['results'].append(result_data)
        
        # Save results if output file specified
        if output_file:
            self._save_results(final_results, output_file)
        
        # Print summary
        self._print_summary(final_results)
        
        return final_results
    
    def _save_results(self, results: Dict, output_file: str):
        """Save results to file"""
        try:
            # Create output directory if needed
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Save as JSON
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Results saved to: {output_file}")
            
            # Also save URLs to separate file
            urls_file = output_file.replace('.json', '_urls.txt')
            all_urls = self.orchestrator.get_all_urls()
            with open(urls_file, 'w', encoding='utf-8') as f:
                for url in all_urls:
                    f.write(url + '\n')
            
            self.logger.info(f"URLs saved to: {urls_file}")
            
        except Exception as e:
            self.logger.error(f"Error saving results: {e}")
    
    def _print_summary(self, results: Dict):
        """Print search summary"""
        summary = results['summary']
        
        print("\n" + "="*60)
        print("OSINT Search Summary")
        print("="*60)
        print(f"Target: {results['query']['full_name']}")
        print(f"Total execution time: {summary['total_execution_time']:.2f} seconds")
        print(f"Total URLs found: {summary['total_urls_found']}")
        print(f"Successful scrapers: {summary['successful_scrapers']}/{summary['total_scrapers_used']}")
        
        print("\nResults by scraper:")
        print("-"*40)
        
        for scraper_name, scraper_info in summary['scrapers'].items():
            status = "✓" if scraper_info['success'] else "✗"
            print(f"{status} {scraper_name:15} | "
                  f"URLs: {scraper_info['urls_found']:4} | "
                  f"Time: {scraper_info['execution_time']:.1f}s")
            if scraper_info['error']:
                print(f"  └─ Error: {scraper_info['error']}")
        
        print("="*60)

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="OSINT Search Orchestrator - Parallel multi-tool search"
    )
    
    # Required arguments
    parser.add_argument('first_name', help='First name of the target')
    parser.add_argument('last_name', help='Last name of the target')
    
    # Optional arguments
    parser.add_argument('-a', '--activity', default='', 
                       help='Activity/profession of the target')
    parser.add_argument('-l', '--location', 
                       help='Location of the target')
    parser.add_argument('-e', '--email', 
                       help='Email address (for domain searches)')
    parser.add_argument('-d', '--domain', 
                       help='Domain name (for corporate searches)')
    
    # Configuration options
    parser.add_argument('-c', '--config', 
                       help='Configuration file path')
    parser.add_argument('-o', '--output', 
                       help='Output file path (JSON)')
    parser.add_argument('--speed', action='store_true',
                       help='Optimize for speed over completeness')
    parser.add_argument('--complete', action='store_true',
                       help='Optimize for completeness over speed')
    
    # Tool selection
    parser.add_argument('--disable', nargs='+', 
                       choices=['sherlock', 'photon', 'harvester', 'daprofiler',
                               'proton', 'snscrape', 'twint', 'tookie'],
                       help='Disable specific tools')
    parser.add_argument('--enable-only', nargs='+',
                       choices=['sherlock', 'photon', 'harvester', 'daprofiler',
                               'proton', 'snscrape', 'twint', 'tookie'],
                       help='Enable only specific tools')
    
    args = parser.parse_args()
    
    # Initialize searcher
    searcher = OSINTSearcher(args.config)
    
    # Apply optimization settings
    if args.speed:
        searcher.config.optimize_for_speed()
        print("Optimized for speed")
    elif args.complete:
        searcher.config.optimize_for_completeness()
        print("Optimized for completeness")
    
    # Apply tool selection
    if args.enable_only:
        # Disable all tools first
        for attr in dir(searcher.config.scraper):
            if attr.startswith('enable_'):
                setattr(searcher.config.scraper, attr, False)
        
        # Enable only specified tools
        for tool in args.enable_only:
            setattr(searcher.config.scraper, f'enable_{tool}', True)
    
    elif args.disable:
        # Disable specified tools
        for tool in args.disable:
            setattr(searcher.config.scraper, f'enable_{tool}', False)
    
    # Prepare additional info
    additional_info = {}
    if args.email:
        additional_info['email'] = args.email
        if not args.domain:
            additional_info['domain'] = args.email.split('@')[1]
    if args.domain:
        additional_info['domain'] = args.domain
    
    # Generate output filename if not specified
    if not args.output:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = f"{args.first_name}_{args.last_name}".replace(' ', '_')
        args.output = f"osint_results_{safe_name}_{timestamp}.json"
    
    # Execute search
    try:
        results = await searcher.search(
            first_name=args.first_name,
            last_name=args.last_name,
            activity=args.activity,
            location=args.location,
            additional_info=additional_info,
            output_file=args.output
        )
        
        return 0
        
    except KeyboardInterrupt:
        print("\nSearch interrupted by user")
        return 1
    except Exception as e:
        print(f"\nError: {e}")
        return 1

if __name__ == "__main__":
    # Run the async main function
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
