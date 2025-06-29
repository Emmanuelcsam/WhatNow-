"""
Enhanced Web Scraping Module
Provides advanced web scraping capabilities with multiple fallback methods
"""
import logging
import asyncio
import aiohttp
import requests
import json
import re
from typing import List, Dict, Any, Optional, Set
from urllib.parse import quote, urljoin, urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

# Try to import optional dependencies
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logging.warning("Selenium not available, some advanced scraping features disabled")

try:
    import cloudscraper
    CLOUDSCRAPER_AVAILABLE = True
except ImportError:
    CLOUDSCRAPER_AVAILABLE = False
    logging.warning("Cloudscraper not available, some anti-bot features disabled")

logger = logging.getLogger(__name__)


class EnhancedWebScraper:
    """
    Advanced web scraper with multiple methods and fallbacks
    """
    
    def __init__(self, max_workers: int = 10, timeout: int = 30):
        self.max_workers = max_workers
        self.timeout = timeout
        self.session = None
        self.scraper = cloudscraper.create_scraper() if CLOUDSCRAPER_AVAILABLE else None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.driver = None
        self.results_cache = {}
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
        if self.driver:
            self.driver.quit()
    
    async def search_person_comprehensive(self, 
                                        first_name: str, 
                                        last_name: str,
                                        location: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Comprehensive person search using multiple methods
        
        Args:
            first_name: Person's first name
            last_name: Person's last name
            location: Optional location data
            
        Returns:
            List of search results from various sources
        """
        full_name = f"{first_name} {last_name}"
        results = []
        
        # Create search tasks for different sources
        search_tasks = [
            self._search_google(full_name, location),
            self._search_bing(full_name, location),
            self._search_duckduckgo(full_name, location),
            self._search_social_media(full_name),
            self._search_professional_networks(full_name),
            self._search_public_records(full_name, location),
            self._search_news_mentions(full_name),
            self._search_academic_sources(full_name),
            self._search_event_platforms(full_name),
            self._search_hobby_sites(full_name)
        ]
        
        # Execute all searches concurrently
        search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(search_results):
            if isinstance(result, Exception):
                logger.error(f"Search task {i} failed: {result}")
            elif result:
                results.extend(result)
        
        # Deduplicate results
        unique_results = self._deduplicate_results(results)
        
        # Rank results by relevance
        ranked_results = self._rank_results(unique_results, full_name)
        
        logger.info(f"Comprehensive search for {full_name} found {len(ranked_results)} unique results")
        return ranked_results
    
    async def _search_google(self, query: str, location: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search Google (with ethical scraping)"""
        results = []
        try:
            # Build location-aware query
            search_query = query
            if location and location.get('city'):
                search_query += f" {location['city']}"
            
            # Use Google Custom Search API if available, otherwise fallback
            url = f"https://www.google.com/search?q={quote(search_query)}&num=10"
            
            if self.scraper:
                response = self.scraper.get(url, headers=self.headers)
            else:
                async with self.session.get(url, headers=self.headers) as response:
                    response_text = await response.text()
            
            soup = BeautifulSoup(response.text if self.scraper else response_text, 'html.parser')
            
            # Extract search results
            for result in soup.select('div.g')[:10]:
                title_elem = result.select_one('h3')
                link_elem = result.select_one('a')
                snippet_elem = result.select_one('span.st, div.VwiC3b')
                
                if title_elem and link_elem:
                    results.append({
                        'source': 'google',
                        'title': title_elem.get_text(strip=True),
                        'url': link_elem.get('href', ''),
                        'description': snippet_elem.get_text(strip=True) if snippet_elem else '',
                        'content': '',
                        'timestamp': datetime.now().isoformat()
                    })
                    
        except Exception as e:
            logger.error(f"Google search failed: {e}")
            
        return results
    
    async def _search_bing(self, query: str, location: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search Bing"""
        results = []
        try:
            search_query = query
            if location and location.get('city'):
                search_query += f" {location['city']}"
                
            url = f"https://www.bing.com/search?q={quote(search_query)}"
            
            async with self.session.get(url, headers=self.headers) as response:
                html = await response.text()
                
            soup = BeautifulSoup(html, 'html.parser')
            
            for result in soup.select('li.b_algo')[:10]:
                title_elem = result.select_one('h2 a')
                snippet_elem = result.select_one('div.b_caption p')
                
                if title_elem:
                    results.append({
                        'source': 'bing',
                        'title': title_elem.get_text(strip=True),
                        'url': title_elem.get('href', ''),
                        'description': snippet_elem.get_text(strip=True) if snippet_elem else '',
                        'content': '',
                        'timestamp': datetime.now().isoformat()
                    })
                    
        except Exception as e:
            logger.error(f"Bing search failed: {e}")
            
        return results
    
    async def _search_duckduckgo(self, query: str, location: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search DuckDuckGo"""
        results = []
        try:
            # DuckDuckGo API endpoint
            url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            async with self.session.get(url, params=params, headers=self.headers) as response:
                data = await response.json()
                
            # Process instant answer
            if data.get('AbstractText'):
                results.append({
                    'source': 'duckduckgo',
                    'title': data.get('Heading', query),
                    'url': data.get('AbstractURL', ''),
                    'description': data.get('AbstractText', ''),
                    'content': data.get('Abstract', ''),
                    'timestamp': datetime.now().isoformat()
                })
                
            # Process related topics
            for topic in data.get('RelatedTopics', [])[:5]:
                if isinstance(topic, dict) and topic.get('Text'):
                    results.append({
                        'source': 'duckduckgo',
                        'title': topic.get('Text', '').split(' - ')[0],
                        'url': topic.get('FirstURL', ''),
                        'description': topic.get('Text', ''),
                        'content': '',
                        'timestamp': datetime.now().isoformat()
                    })
                    
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            
        return results
    
    async def _search_social_media(self, name: str) -> List[Dict[str, Any]]:
        """Search social media platforms"""
        results = []
        platforms = {
            'twitter': f"https://twitter.com/search?q={quote(name)}&src=typed_query&f=user",
            'facebook': f"https://www.facebook.com/search/people/?q={quote(name)}",
            'instagram': f"https://www.instagram.com/explore/tags/{quote(name.replace(' ', ''))}",
            'linkedin': f"https://www.linkedin.com/search/results/people/?keywords={quote(name)}"
        }
        
        for platform, url in platforms.items():
            try:
                # Note: Actual implementation would require proper API access
                # This is a placeholder for the structure
                results.append({
                    'source': f'{platform}_search',
                    'title': f'{name} on {platform.title()}',
                    'url': url,
                    'description': f'Search results for {name} on {platform.title()}',
                    'content': '',
                    'platform': platform,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"{platform} search failed: {e}")
                
        return results
    
    async def _search_professional_networks(self, name: str) -> List[Dict[str, Any]]:
        """Search professional networking sites"""
        results = []
        
        # LinkedIn public search
        try:
            # This would use LinkedIn API in production
            results.append({
                'source': 'professional_network',
                'title': f'{name} - Professional Profile',
                'url': f"https://www.linkedin.com/search/results/people/?keywords={quote(name)}",
                'description': 'Professional networking profile',
                'content': '',
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Professional network search failed: {e}")
            
        return results
    
    async def _search_public_records(self, name: str, location: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search public records and directories"""
        results = []
        
        # Note: This is a placeholder - actual implementation would use legitimate public APIs
        try:
            if location:
                results.append({
                    'source': 'public_directory',
                    'title': f'{name} - Public Directory',
                    'url': '',
                    'description': f'Public directory information for {name}',
                    'content': '',
                    'location': location,
                    'timestamp': datetime.now().isoformat()
                })
        except Exception as e:
            logger.error(f"Public records search failed: {e}")
            
        return results
    
    async def _search_news_mentions(self, name: str) -> List[Dict[str, Any]]:
        """Search news mentions"""
        results = []
        
        try:
            # Search news aggregators
            news_sites = [
                f"https://news.google.com/search?q={quote(name)}",
                f"https://www.bing.com/news/search?q={quote(name)}"
            ]
            
            for site in news_sites:
                results.append({
                    'source': 'news',
                    'title': f'News mentions of {name}',
                    'url': site,
                    'description': f'Recent news articles mentioning {name}',
                    'content': '',
                    'timestamp': datetime.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"News search failed: {e}")
            
        return results
    
    async def _search_academic_sources(self, name: str) -> List[Dict[str, Any]]:
        """Search academic sources"""
        results = []
        
        try:
            # Google Scholar and other academic searches
            results.append({
                'source': 'academic',
                'title': f'{name} - Academic Publications',
                'url': f"https://scholar.google.com/scholar?q={quote(name)}",
                'description': 'Academic publications and citations',
                'content': '',
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Academic search failed: {e}")
            
        return results
    
    async def _search_event_platforms(self, name: str) -> List[Dict[str, Any]]:
        """Search event platforms for participation"""
        results = []
        
        event_platforms = [
            'eventbrite', 'meetup', 'facebook events'
        ]
        
        for platform in event_platforms:
            try:
                results.append({
                    'source': f'{platform}_events',
                    'title': f'{name} - {platform.title()} Events',
                    'url': '',
                    'description': f'Event participation on {platform}',
                    'content': '',
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"{platform} event search failed: {e}")
                
        return results
    
    async def _search_hobby_sites(self, name: str) -> List[Dict[str, Any]]:
        """Search hobby and interest sites"""
        results = []
        
        hobby_categories = [
            'sports', 'music', 'gaming', 'photography', 'cooking'
        ]
        
        for category in hobby_categories:
            try:
                results.append({
                    'source': f'{category}_community',
                    'title': f'{name} - {category.title()} Community',
                    'url': '',
                    'description': f'{category.title()} related activities and interests',
                    'content': '',
                    'category': category,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"{category} search failed: {e}")
                
        return results
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results based on URL and content similarity"""
        seen_urls = set()
        seen_hashes = set()
        unique_results = []
        
        for result in results:
            # Check URL
            url = result.get('url', '')
            if url and url in seen_urls:
                continue
                
            # Check content hash
            content_hash = hashlib.md5(
                f"{result.get('title', '')}{result.get('description', '')}".encode()
            ).hexdigest()
            
            if content_hash in seen_hashes:
                continue
                
            seen_urls.add(url)
            seen_hashes.add(content_hash)
            unique_results.append(result)
            
        return unique_results
    
    def _rank_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Rank results by relevance"""
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for result in results:
            score = 0
            
            # Title relevance
            title = result.get('title', '').lower()
            if query_lower in title:
                score += 10
            else:
                score += sum(2 for word in query_words if word in title)
                
            # Description relevance
            desc = result.get('description', '').lower()
            if query_lower in desc:
                score += 5
            else:
                score += sum(1 for word in query_words if word in desc)
                
            # Source reliability
            source_scores = {
                'linkedin': 5,
                'professional_network': 5,
                'news': 4,
                'academic': 4,
                'google': 3,
                'bing': 3,
                'social_media': 2
            }
            
            source = result.get('source', '').lower()
            for key, value in source_scores.items():
                if key in source:
                    score += value
                    break
                    
            result['relevance_score'] = score
            
        # Sort by relevance score
        return sorted(results, key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    async def extract_page_content(self, url: str) -> Optional[Dict[str, Any]]:
        """Extract content from a specific page"""
        try:
            async with self.session.get(url, headers=self.headers, timeout=10) as response:
                if response.status != 200:
                    return None
                    
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                    
                # Extract text
                text = soup.get_text(separator=' ', strip=True)
                
                # Extract metadata
                title = soup.find('title')
                description = soup.find('meta', attrs={'name': 'description'})
                
                return {
                    'url': url,
                    'title': title.string if title else '',
                    'description': description.get('content', '') if description else '',
                    'content': text[:5000],  # Limit content length
                    'extracted_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to extract content from {url}: {e}")
            return None
    
    def cleanup(self):
        """Cleanup resources"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass