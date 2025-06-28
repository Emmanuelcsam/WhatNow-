#!/usr/bin/env python3
"""
Deep Person Search Tool
A comprehensive tool for finding information about a person based on their name and location.
"""

import os
import re
import sys
import json
import time
import logging
import requests
import subprocess
from pathlib import Path
from datetime import datetime
from urllib.parse import quote, urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict
import hashlib

# Try to import required libraries
try:
    from bs4 import BeautifulSoup
    from tqdm import tqdm
    import colorama
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError as e:
    print("Installing required dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "beautifulsoup4", "requests", "tqdm", "colorama", "lxml"])
    from bs4 import BeautifulSoup
    from tqdm import tqdm
    import colorama
    from colorama import Fore, Style, init
    init(autoreset=True)

__version__ = "1.0.0"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PersonSearchEngine:
    """Main search engine for finding information about a person."""
    
    def __init__(self, first_name: str, last_name: str, location: str, output_dir: str = "search_results"):
        self.first_name = first_name.strip()
        self.last_name = last_name.strip()
        self.location = location.strip()
        self.full_name = f"{self.first_name} {self.last_name}"
        
        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path(output_dir) / f"{self.first_name}_{self.last_name}_{timestamp}"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Results storage
        self.results = defaultdict(list)
        self.unique_urls = set()
        self.processed_urls = set()
        
        # Search queries variations
        self.search_queries = self._generate_search_queries()
        
        # User agent for requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
    def _generate_search_queries(self) -> List[str]:
        """Generate various search query combinations."""
        queries = [
            f'"{self.full_name}" {self.location}',
            f'"{self.first_name} {self.last_name}" {self.location}',
            f'{self.first_name} {self.last_name} {self.location}',
            f'"{self.full_name}"',
            f'{self.full_name} linkedin',
            f'{self.full_name} facebook',
            f'{self.full_name} twitter',
            f'{self.full_name} instagram',
            f'{self.full_name} contact',
            f'{self.full_name} email',
            f'{self.full_name} phone',
            f'{self.full_name} address {self.location}',
            f'{self.full_name} resume',
            f'{self.full_name} cv',
            f'{self.full_name} bio',
            f'{self.full_name} profile',
        ]
        
        # Add location-specific queries
        location_parts = self.location.split(',')
        if len(location_parts) > 1:
            city = location_parts[0].strip()
            queries.extend([
                f'"{self.full_name}" {city}',
                f'{self.first_name} {self.last_name} {city}'
            ])
            
        return queries
    
    def search_duckduckgo(self, query: str, max_results: int = 30) -> List[Dict]:
        """Search using DuckDuckGo HTML interface."""
        results = []
        try:
            url = f"https://duckduckgo.com/html/?q={quote(query)}"
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find result links
            for result in soup.find_all('div', class_='result__body')[:max_results]:
                link_elem = result.find('a', class_='result__a')
                snippet_elem = result.find('a', class_='result__snippet')
                
                if link_elem:
                    url = link_elem.get('href', '')
                    title = link_elem.get_text(strip=True)
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                    
                    if url and url not in self.unique_urls:
                        self.unique_urls.add(url)
                        results.append({
                            'url': url,
                            'title': title,
                            'snippet': snippet,
                            'source': 'duckduckgo',
                            'query': query
                        })
                        
        except Exception as e:
            logger.error(f"Error searching DuckDuckGo: {e}")
            
        return results
    
    def search_bing(self, query: str, max_results: int = 30) -> List[Dict]:
        """Search using Bing."""
        results = []
        try:
            params = {
                'q': query,
                'count': max_results
            }
            url = f"https://www.bing.com/search?{urlencode(params)}"
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find organic results
            for result in soup.find_all('li', class_='b_algo'):
                link_elem = result.find('h2').find('a') if result.find('h2') else None
                snippet_elem = result.find('div', class_='b_caption')
                
                if link_elem:
                    url = link_elem.get('href', '')
                    title = link_elem.get_text(strip=True)
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                    
                    if url and url not in self.unique_urls:
                        self.unique_urls.add(url)
                        results.append({
                            'url': url,
                            'title': title,
                            'snippet': snippet,
                            'source': 'bing',
                            'query': query
                        })
                        
        except Exception as e:
            logger.error(f"Error searching Bing: {e}")
            
        return results
    
    def search_google(self, query: str, max_results: int = 30) -> List[Dict]:
        """Search using Google (with rate limiting)."""
        results = []
        try:
            # Google search with careful rate limiting
            params = {
                'q': query,
                'num': max_results
            }
            url = f"https://www.google.com/search?{urlencode(params)}"
            
            # Add delay to avoid rate limiting
            time.sleep(2)
            
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find search results
            for g in soup.find_all('div', class_='g'):
                link_elem = g.find('a')
                title_elem = g.find('h3')
                snippet_elem = g.find('span', class_='aCOpRe') or g.find('span', class_='st')
                
                if link_elem and title_elem:
                    url = link_elem.get('href', '')
                    title = title_elem.get_text(strip=True)
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                    
                    if url and url.startswith('http') and url not in self.unique_urls:
                        self.unique_urls.add(url)
                        results.append({
                            'url': url,
                            'title': title,
                            'snippet': snippet,
                            'source': 'google',
                            'query': query
                        })
                        
        except Exception as e:
            logger.error(f"Error searching Google: {e}")
            
        return results
    
    def search_social_media(self) -> Dict[str, List[Dict]]:
        """Search specific social media platforms."""
        social_results = defaultdict(list)
        
        # Platform-specific search URLs
        platforms = {
            'linkedin': f'site:linkedin.com/in "{self.full_name}" {self.location}',
            'facebook': f'site:facebook.com "{self.full_name}" {self.location}',
            'twitter': f'site:twitter.com "{self.full_name}"',
            'instagram': f'site:instagram.com "{self.full_name}"',
            'github': f'site:github.com "{self.full_name}"',
            'youtube': f'site:youtube.com "{self.full_name}"'
        }
        
        print(f"\n{Fore.CYAN}Searching social media platforms...{Style.RESET_ALL}")
        
        for platform, query in platforms.items():
            results = self.search_duckduckgo(query, max_results=10)
            if results:
                social_results[platform].extend(results)
                print(f"{Fore.GREEN}✓{Style.RESET_ALL} Found {len(results)} results on {platform}")
            
        return social_results
    
    def search_people_directories(self) -> List[Dict]:
        """Search people search engines and directories."""
        directory_results = []
        
        # Common people search queries
        directories = [
            f'"{self.full_name}" whitepages {self.location}',
            f'"{self.full_name}" yellowpages {self.location}',
            f'"{self.full_name}" spokeo',
            f'"{self.full_name}" pipl',
            f'"{self.full_name}" truepeoplesearch',
            f'"{self.full_name}" beenverified',
            f'"{self.full_name}" directory {self.location}',
            f'"{self.full_name}" phone directory',
            f'"{self.full_name}" public records {self.location}'
        ]
        
        print(f"\n{Fore.CYAN}Searching people directories...{Style.RESET_ALL}")
        
        for query in directories:
            results = self.search_duckduckgo(query, max_results=5)
            directory_results.extend(results)
            
        return directory_results
    
    def extract_contact_info(self, text: str) -> Dict[str, Set[str]]:
        """Extract potential contact information from text."""
        contact_info = {
            'emails': set(),
            'phones': set(),
            'addresses': set()
        }
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        contact_info['emails'].update(emails)
        
        # Phone pattern (US format)
        phone_patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            r'\(\d{3}\)\s?\d{3}[-.]?\d{4}',
            r'\b\d{3}\s\d{3}\s\d{4}\b'
        ]
        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            contact_info['phones'].update(phones)
        
        # Simple address pattern (this is basic and may need refinement)
        address_pattern = r'\d+\s+[\w\s]+(?:street|st|avenue|ave|road|rd|lane|ln|drive|dr|court|ct|plaza|blvd|boulevard)\b'
        addresses = re.findall(address_pattern, text, re.IGNORECASE)
        contact_info['addresses'].update(addresses)
        
        return contact_info
    
    def analyze_page_content(self, url: str) -> Optional[Dict]:
        """Analyze a webpage for relevant information."""
        if url in self.processed_urls:
            return None
            
        self.processed_urls.add(url)
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            
            # Check if the page contains the person's name
            name_variations = [
                self.full_name.lower(),
                f"{self.first_name.lower()} {self.last_name.lower()}",
                f"{self.last_name.lower()}, {self.first_name.lower()}"
            ]
            
            text_lower = text.lower()
            relevance_score = sum(1 for name in name_variations if name in text_lower)
            
            if relevance_score > 0:
                # Extract contact information
                contact_info = self.extract_contact_info(text)
                
                # Extract title
                title = soup.title.string if soup.title else "No title"
                
                # Extract meta description
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                description = meta_desc.get('content', '') if meta_desc else ''
                
                # Extract relevant paragraphs containing the name
                relevant_paragraphs = []
                for p in soup.find_all('p'):
                    p_text = p.get_text(strip=True)
                    if any(name in p_text.lower() for name in name_variations):
                        relevant_paragraphs.append(p_text)
                
                return {
                    'url': url,
                    'title': title,
                    'description': description,
                    'relevance_score': relevance_score,
                    'contact_info': contact_info,
                    'relevant_paragraphs': relevant_paragraphs[:5],  # Limit to 5 paragraphs
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error analyzing {url}: {e}")
            
        return None
    
    def run_comprehensive_search(self):
        """Run the comprehensive search process."""
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Deep Person Search Tool v{__version__}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"\nSearching for: {Fore.GREEN}{self.full_name}{Style.RESET_ALL}")
        print(f"Location: {Fore.GREEN}{self.location}{Style.RESET_ALL}")
        print(f"Output directory: {Fore.GREEN}{self.output_dir}{Style.RESET_ALL}\n")
        
        all_results = []
        
        # Phase 1: General search queries
        print(f"{Fore.YELLOW}Phase 1: General Search{Style.RESET_ALL}")
        with tqdm(total=len(self.search_queries), desc="Searching") as pbar:
            for query in self.search_queries:
                # Use multiple search engines
                results = []
                results.extend(self.search_duckduckgo(query))
                results.extend(self.search_bing(query))
                
                all_results.extend(results)
                pbar.update(1)
                
        print(f"{Fore.GREEN}✓{Style.RESET_ALL} Found {len(all_results)} general results")
        
        # Phase 2: Social media search
        print(f"\n{Fore.YELLOW}Phase 2: Social Media Search{Style.RESET_ALL}")
        social_results = self.search_social_media()
        for platform, results in social_results.items():
            all_results.extend(results)
            
        # Phase 3: People directories
        print(f"\n{Fore.YELLOW}Phase 3: People Directories{Style.RESET_ALL}")
        directory_results = self.search_people_directories()
        all_results.extend(directory_results)
        print(f"{Fore.GREEN}✓{Style.RESET_ALL} Found {len(directory_results)} directory results")
        
        # Phase 4: Analyze pages
        print(f"\n{Fore.YELLOW}Phase 4: Analyzing Pages{Style.RESET_ALL}")
        analyzed_results = []
        
        # Limit analysis to most relevant results
        urls_to_analyze = [r['url'] for r in all_results[:100]]  # Analyze top 100 URLs
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {executor.submit(self.analyze_page_content, url): url 
                           for url in urls_to_analyze}
            
            with tqdm(total=len(urls_to_analyze), desc="Analyzing pages") as pbar:
                for future in as_completed(future_to_url):
                    result = future.result()
                    if result:
                        analyzed_results.append(result)
                    pbar.update(1)
                    
        print(f"{Fore.GREEN}✓{Style.RESET_ALL} Analyzed {len(analyzed_results)} relevant pages")
        
        # Save results
        self._save_results(all_results, social_results, analyzed_results)
        
        # Generate report
        self._generate_report(all_results, social_results, analyzed_results)
        
        print(f"\n{Fore.GREEN}Search complete!{Style.RESET_ALL}")
        print(f"Results saved to: {Fore.CYAN}{self.output_dir}{Style.RESET_ALL}")
        
    def _save_results(self, all_results: List[Dict], social_results: Dict, analyzed_results: List[Dict]):
        """Save all results to files."""
        # Save raw search results
        with open(self.output_dir / 'search_results.json', 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
            
        # Save social media results
        with open(self.output_dir / 'social_media_results.json', 'w', encoding='utf-8') as f:
            json.dump(social_results, f, indent=2, ensure_ascii=False)
            
        # Save analyzed results
        with open(self.output_dir / 'analyzed_pages.json', 'w', encoding='utf-8') as f:
            json.dump(analyzed_results, f, indent=2, ensure_ascii=False)
            
    def _generate_report(self, all_results: List[Dict], social_results: Dict, analyzed_results: List[Dict]):
        """Generate a comprehensive report."""
        report_path = self.output_dir / 'report.txt'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            # Header
            f.write(f"DEEP PERSON SEARCH REPORT\n")
            f.write(f"{'='*80}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Subject: {self.full_name}\n")
            f.write(f"Location: {self.location}\n")
            f.write(f"{'='*80}\n\n")
            
            # Summary
            f.write(f"SUMMARY\n")
            f.write(f"{'-'*40}\n")
            f.write(f"Total search results: {len(all_results)}\n")
            f.write(f"Pages analyzed: {len(analyzed_results)}\n")
            
            # Social media presence
            f.write(f"\nSOCIAL MEDIA PRESENCE\n")
            f.write(f"{'-'*40}\n")
            for platform, results in social_results.items():
                f.write(f"{platform.capitalize()}: {len(results)} results\n")
                for result in results[:3]:  # Top 3 results per platform
                    f.write(f"  - {result['title']}\n")
                    f.write(f"    {result['url']}\n")
                    
            # Contact information found
            f.write(f"\nCONTACT INFORMATION FOUND\n")
            f.write(f"{'-'*40}\n")
            
            all_emails = set()
            all_phones = set()
            all_addresses = set()
            
            for result in analyzed_results:
                contact = result.get('contact_info', {})
                all_emails.update(contact.get('emails', []))
                all_phones.update(contact.get('phones', []))
                all_addresses.update(contact.get('addresses', []))
                
            if all_emails:
                f.write(f"\nEmails:\n")
                for email in all_emails:
                    f.write(f"  - {email}\n")
                    
            if all_phones:
                f.write(f"\nPhone Numbers:\n")
                for phone in all_phones:
                    f.write(f"  - {phone}\n")
                    
            if all_addresses:
                f.write(f"\nPossible Addresses:\n")
                for address in all_addresses:
                    f.write(f"  - {address}\n")
                    
            # Most relevant pages
            f.write(f"\n\nMOST RELEVANT PAGES\n")
            f.write(f"{'-'*40}\n")
            
            # Sort by relevance score
            sorted_results = sorted(analyzed_results, 
                                  key=lambda x: x.get('relevance_score', 0), 
                                  reverse=True)
            
            for i, result in enumerate(sorted_results[:10], 1):
                f.write(f"\n{i}. {result['title']}\n")
                f.write(f"   URL: {result['url']}\n")
                f.write(f"   Relevance: {result.get('relevance_score', 0)}\n")
                
                if result.get('description'):
                    f.write(f"   Description: {result['description'][:200]}...\n")
                    
                if result.get('relevant_paragraphs'):
                    f.write(f"   Relevant content:\n")
                    for para in result['relevant_paragraphs'][:2]:
                        f.write(f"     {para[:300]}...\n")
                        
            # All URLs found
            f.write(f"\n\nALL URLS FOUND\n")
            f.write(f"{'-'*40}\n")
            
            # Group URLs by domain
            domain_groups = defaultdict(list)
            for result in all_results:
                domain = result['url'].split('/')[2] if '/' in result['url'] else result['url']
                domain_groups[domain].append(result)
                
            for domain, results in sorted(domain_groups.items()):
                f.write(f"\n{domain} ({len(results)} results)\n")
                for result in results[:5]:  # Max 5 per domain
                    f.write(f"  - {result['title'][:80]}...\n")
                    f.write(f"    {result['url']}\n")
                    
        print(f"\n{Fore.GREEN}Report generated: {report_path}{Style.RESET_ALL}")


def main():
    """Main entry point."""
    print(f"{Fore.CYAN}Deep Person Search Tool v{__version__}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    # Get user input
    print("Please provide the following information:\n")
    
    first_name = input(f"{Fore.YELLOW}First Name: {Style.RESET_ALL}").strip()
    if not first_name:
        print(f"{Fore.RED}First name is required!{Style.RESET_ALL}")
        return
        
    last_name = input(f"{Fore.YELLOW}Last Name: {Style.RESET_ALL}").strip()
    if not last_name:
        print(f"{Fore.RED}Last name is required!{Style.RESET_ALL}")
        return
        
    location = input(f"{Fore.YELLOW}Location (e.g., 'New York, NY' or 'London, UK'): {Style.RESET_ALL}").strip()
    if not location:
        print(f"{Fore.RED}Location is required!{Style.RESET_ALL}")
        return
        
    # Confirm search
    print(f"\n{Fore.CYAN}Search Configuration:{Style.RESET_ALL}")
    print(f"Name: {Fore.GREEN}{first_name} {last_name}{Style.RESET_ALL}")
    print(f"Location: {Fore.GREEN}{location}{Style.RESET_ALL}")
    
    confirm = input(f"\n{Fore.YELLOW}Proceed with search? (y/n): {Style.RESET_ALL}").lower()
    if confirm != 'y':
        print("Search cancelled.")
        return
        
    # Run search
    try:
        searcher = PersonSearchEngine(first_name, last_name, location)
        searcher.run_comprehensive_search()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Search interrupted by user.{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}An error occurred: {e}{Style.RESET_ALL}")
        logger.exception("Search error")


if __name__ == "__main__":
    main()
