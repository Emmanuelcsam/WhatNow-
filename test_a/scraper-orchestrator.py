"""
scraper_orchestrator.py - Orchestrates multiple web scraping tools
"""
import asyncio
import concurrent.futures
import logging
import time
import subprocess
import json
import os
import re
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import aiohttp
import pandas as pd
from urllib.parse import quote_plus, urlparse

logger = logging.getLogger(__name__)

@dataclass
class ScraperResult:
    """Result from a single scraper"""
    source: str
    data: Dict
    urls: List[str] = field(default_factory=list)
    raw_text: str = ""
    metadata: Dict = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class SearchQuery:
    """Search query parameters"""
    first_name: str
    last_name: str
    activity: str
    location: Optional[str] = None
    additional_info: Dict = field(default_factory=dict)
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    def get_search_variations(self) -> List[str]:
        """Generate search query variations"""
        variations = [
            self.full_name,
            f'"{self.full_name}"',
            f"{self.full_name} {self.activity}",
            f'"{self.full_name}" {self.activity}',
        ]
        
        if self.location:
            variations.extend([
                f"{self.full_name} {self.location}",
                f'"{self.full_name}" {self.location}',
                f"{self.full_name} {self.activity} {self.location}"
            ])
        
        # Add variations with initials
        if len(self.first_name) > 0:
            initial = self.first_name[0]
            variations.extend([
                f"{initial}. {self.last_name}",
                f"{initial} {self.last_name}"
            ])
        
        return variations

class ScraperOrchestrator:
    """Orchestrates multiple web scraping tools"""
    
    def __init__(self, config):
        self.config = config
        self.results = []
        self.processed_urls = set()
        self.start_time = None
        self.scrapers = self._initialize_scrapers()
    
    def _initialize_scrapers(self) -> Dict:
        """Initialize available scrapers"""
        scrapers = {}
        
        # Built-in scrapers (always available)
        scrapers['google_search'] = self._scrape_google_search
        scrapers['duckduckgo'] = self._scrape_duckduckgo
        scrapers['bing'] = self._scrape_bing
        scrapers['social_media'] = self._scrape_social_media
        
        # Tool-based scrapers (check availability)
        if self.config.scraper.enable_sherlock and self._check_tool_available('sherlock'):
            scrapers['sherlock'] = self._scrape_with_sherlock
        
        if self.config.scraper.enable_photon and self._check_tool_available('photon'):
            scrapers['photon'] = self._scrape_with_photon
        
        if self.config.scraper.enable_harvester and self._check_tool_available('theHarvester'):
            scrapers['theharvester'] = self._scrape_with_harvester
        
        return scrapers
    
    def _check_tool_available(self, tool_name: str) -> bool:
        """Check if external tool is available"""
        try:
            result = subprocess.run([tool_name, '--help'], 
                                  capture_output=True, 
                                  timeout=5)
            return result.returncode == 0
        except:
            logger.warning(f"Tool {tool_name} not available")
            return False
    
    async def search(self, query: SearchQuery, timeout: int = 60) -> List[ScraperResult]:
        """
        Execute search across all scrapers with timeout
        
        Args:
            query: Search query parameters
            timeout: Maximum time in seconds
            
        Returns:
            List of scraper results
        """
        self.start_time = time.time()
        self.results = []
        self.processed_urls = set()
        
        try:
            # Run scrapers concurrently with timeout
            await asyncio.wait_for(
                self._run_all_scrapers(query),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.warning(f"Search timeout after {timeout} seconds")
        except Exception as e:
            logger.error(f"Search error: {e}")
        
        # Post-process results
        self._deduplicate_results()
        self._enrich_results()
        
        return self.results
    
    async def _run_all_scrapers(self, query: SearchQuery):
        """Run all scrapers concurrently"""
        tasks = []
        
        # Create tasks for each scraper
        for name, scraper_func in self.scrapers.items():
            if asyncio.iscoroutinefunction(scraper_func):
                task = scraper_func(query)
            else:
                # Wrap sync functions
                task = asyncio.create_task(
                    asyncio.to_thread(scraper_func, query)
                )
            tasks.append(task)
        
        # Run all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            scraper_name = list(self.scrapers.keys())[i]
            if isinstance(result, Exception):
                logger.error(f"Scraper {scraper_name} failed: {result}")
                self.results.append(ScraperResult(
                    source=scraper_name,
                    data={},
                    success=False,
                    error=str(result),
                    execution_time=time.time() - self.start_time
                ))
            elif result:
                self.results.append(result)
    
    def _scrape_google_search(self, query: SearchQuery) -> ScraperResult:
        """Scrape Google search results"""
        start_time = time.time()
        urls = []
        data = {'search_results': []}
        
        try:
            headers = {
                'User-Agent': self.config.scraper.user_agent,
                'Accept-Language': 'en-US,en;q=0.9'
            }
            
            for search_query in query.get_search_variations()[:3]:  # Limit variations
                search_url = f"https://www.google.com/search?q={quote_plus(search_query)}"
                
                response = requests.get(search_url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract search results
                for result in soup.select('div.g')[:self.config.scraper.max_results_per_source]:
                    title_elem = result.select_one('h3')
                    link_elem = result.select_one('a')
                    snippet_elem = result.select_one('span.aCOpRe')
                    
                    if title_elem and link_elem:
                        url = link_elem.get('href', '')
                        if url and url not in self.processed_urls:
                            self.processed_urls.add(url)
                            urls.append(url)
                            
                            data['search_results'].append({
                                'title': title_elem.get_text(strip=True),
                                'url': url,
                                'snippet': snippet_elem.get_text(strip=True) if snippet_elem else '',
                                'query': search_query
                            })
                
                # Rate limiting
                time.sleep(1)
            
            return ScraperResult(
                source='google_search',
                data=data,
                urls=urls,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Google search error: {e}")
            return ScraperResult(
                source='google_search',
                data=data,
                urls=urls,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def _scrape_duckduckgo(self, query: SearchQuery) -> ScraperResult:
        """Scrape DuckDuckGo search results"""
        start_time = time.time()
        urls = []
        data = {'search_results': []}
        
        try:
            headers = {'User-Agent': self.config.scraper.user_agent}
            
            for search_query in query.get_search_variations()[:2]:
                search_url = f"https://duckduckgo.com/html/?q={quote_plus(search_query)}"
                
                response = requests.get(search_url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract results
                for result in soup.select('div.result')[:self.config.scraper.max_results_per_source]:
                    title_elem = result.select_one('a.result__a')
                    snippet_elem = result.select_one('a.result__snippet')
                    
                    if title_elem:
                        url = title_elem.get('href', '')
                        if url and url not in self.processed_urls:
                            self.processed_urls.add(url)
                            urls.append(url)
                            
                            data['search_results'].append({
                                'title': title_elem.get_text(strip=True),
                                'url': url,
                                'snippet': snippet_elem.get_text(strip=True) if snippet_elem else '',
                                'query': search_query
                            })
            
            return ScraperResult(
                source='duckduckgo',
                data=data,
                urls=urls,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return ScraperResult(
                source='duckduckgo',
                data=data,
                urls=urls,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def _scrape_bing(self, query: SearchQuery) -> ScraperResult:
        """Scrape Bing search results"""
        start_time = time.time()
        urls = []
        data = {'search_results': []}
        
        try:
            headers = {'User-Agent': self.config.scraper.user_agent}
            
            search_query = query.get_search_variations()[0]
            search_url = f"https://www.bing.com/search?q={quote_plus(search_query)}"
            
            response = requests.get(search_url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract results
            for result in soup.select('li.b_algo')[:self.config.scraper.max_results_per_source]:
                title_elem = result.select_one('h2 a')
                snippet_elem = result.select_one('div.b_caption p')
                
                if title_elem:
                    url = title_elem.get('href', '')
                    if url and url not in self.processed_urls:
                        self.processed_urls.add(url)
                        urls.append(url)
                        
                        data['search_results'].append({
                            'title': title_elem.get_text(strip=True),
                            'url': url,
                            'snippet': snippet_elem.get_text(strip=True) if snippet_elem else '',
                            'query': search_query
                        })
            
            return ScraperResult(
                source='bing',
                data=data,
                urls=urls,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Bing search error: {e}")
            return ScraperResult(
                source='bing',
                data=data,
                urls=urls,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def _scrape_social_media(self, query: SearchQuery) -> ScraperResult:
        """Scrape social media platforms"""
        start_time = time.time()
        data = {'profiles': {}}
        urls = []
        
        # Social media search URLs
        platforms = {
            'linkedin': f'site:linkedin.com/in "{query.full_name}"',
            'twitter': f'site:twitter.com "{query.full_name}"',
            'facebook': f'site:facebook.com "{query.full_name}"',
            'instagram': f'site:instagram.com "{query.full_name}"',
            'github': f'site:github.com "{query.full_name}"'
        }
        
        for platform, search_query in platforms.items():
            try:
                # Use Google to search social media
                search_url = f"https://www.google.com/search?q={quote_plus(search_query)}"
                headers = {'User-Agent': self.config.scraper.user_agent}
                
                response = requests.get(search_url, headers=headers, timeout=5)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract first result
                first_result = soup.select_one('div.g a')
                if first_result:
                    url = first_result.get('href', '')
                    if url and platform in url:
                        urls.append(url)
                        data['profiles'][platform] = {
                            'url': url,
                            'found': True
                        }
                    else:
                        data['profiles'][platform] = {'found': False}
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                logger.debug(f"Social media search error for {platform}: {e}")
                data['profiles'][platform] = {'found': False, 'error': str(e)}
        
        return ScraperResult(
            source='social_media',
            data=data,
            urls=urls,
            execution_time=time.time() - start_time
        )
    
    def _scrape_with_sherlock(self, query: SearchQuery) -> ScraperResult:
        """Use Sherlock tool for username search"""
        start_time = time.time()
        data = {'sherlock_results': {}}
        urls = []
        
        try:
            # Prepare username variations
            usernames = [
                f"{query.first_name}{query.last_name}".lower(),
                f"{query.first_name}.{query.last_name}".lower(),
                f"{query.first_name}_{query.last_name}".lower(),
                f"{query.first_name[0]}{query.last_name}".lower()
            ]
            
            for username in usernames[:2]:  # Limit to avoid timeout
                cmd = ['sherlock', username, '--print-found', '--no-color']
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
                
                if result.returncode == 0:
                    # Parse output
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if line.startswith('[+]') and 'http' in line:
                            # Extract URL
                            match = re.search(r'(https?://\S+)', line)
                            if match:
                                url = match.group(1)
                                urls.append(url)
                                
                                # Extract platform name
                                platform = urlparse(url).netloc.replace('www.', '')
                                data['sherlock_results'][platform] = {
                                    'username': username,
                                    'url': url
                                }
            
            return ScraperResult(
                source='sherlock',
                data=data,
                urls=urls,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Sherlock error: {e}")
            return ScraperResult(
                source='sherlock',
                data=data,
                urls=urls,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def _scrape_with_photon(self, query: SearchQuery) -> ScraperResult:
        """Use Photon for deep web crawling"""
        # This would integrate with photon.py
        # Placeholder for now
        return ScraperResult(
            source='photon',
            data={},
            urls=[],
            success=False,
            error="Photon integration pending"
        )
    
    def _scrape_with_harvester(self, query: SearchQuery) -> ScraperResult:
        """Use theHarvester for information gathering"""
        # This would integrate with theHarvester.py
        # Placeholder for now
        return ScraperResult(
            source='theharvester',
            data={},
            urls=[],
            success=False,
            error="theHarvester integration pending"
        )
    
    def _deduplicate_results(self):
        """Remove duplicate URLs and data from results"""
        seen_urls = set()
        unique_results = []
        
        for result in self.results:
            # Deduplicate URLs within each result
            unique_urls = []
            for url in result.urls:
                if url not in seen_urls:
                    seen_urls.add(url)
                    unique_urls.append(url)
            result.urls = unique_urls
            
            unique_results.append(result)
        
        self.results = unique_results
    
    def _enrich_results(self):
        """Enrich results with additional metadata"""
        total_urls = sum(len(r.urls) for r in self.results)
        total_time = time.time() - self.start_time
        
        # Add summary metadata
        for result in self.results:
            result.metadata.update({
                'total_urls_found': total_urls,
                'total_execution_time': total_time,
                'search_depth': self.config.scraper.search_depth
            })
    
    async def fetch_url_content(self, url: str) -> Optional[str]:
        """Fetch and extract text content from URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Remove script and style elements
                        for script in soup(['script', 'style']):
                            script.decompose()
                        
                        # Get text
                        text = soup.get_text()
                        lines = (line.strip() for line in text.splitlines())
                        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                        text = ' '.join(chunk for chunk in chunks if chunk)
                        
                        return text[:5000]  # Limit text length
        except Exception as e:
            logger.debug(f"Failed to fetch {url}: {e}")
        
        return None
    
    def get_all_urls(self) -> List[str]:
        """Get all unique URLs from results"""
        urls = set()
        for result in self.results:
            urls.update(result.urls)
        return list(urls)
    
    def get_summary(self) -> Dict:
        """Get summary of scraping results"""
        summary = {
            'total_scrapers_used': len(self.results),
            'successful_scrapers': sum(1 for r in self.results if r.success),
            'total_urls_found': len(self.get_all_urls()),
            'total_execution_time': time.time() - self.start_time if self.start_time else 0,
            'scrapers': {}
        }
        
        for result in self.results:
            summary['scrapers'][result.source] = {
                'success': result.success,
                'urls_found': len(result.urls),
                'execution_time': result.execution_time,
                'error': result.error
            }
        
        return summary
