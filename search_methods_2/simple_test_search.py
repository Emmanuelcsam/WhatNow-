#!/usr/bin/env python3
"""
Simple test to see what the search engine finds
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main_search import PersonSearchEngine

def simple_test():
    """Run a simple test search"""
    print("Testing search for Emmanuel Sampson...\n")
    
    # Create search engine instance
    searcher = PersonSearchEngine(
        first_name="Emmanuel",
        last_name="Sampson", 
        location="United States"
    )
    
    # Test DuckDuckGo search
    print("Testing DuckDuckGo search...")
    ddg_results = searcher.search_duckduckgo('"Emmanuel Sampson"', max_results=5)
    print(f"Found {len(ddg_results)} results from DuckDuckGo:")
    for i, result in enumerate(ddg_results, 1):
        print(f"\n{i}. {result['title']}")
        print(f"   URL: {result['url']}")
        print(f"   Snippet: {result['snippet'][:150]}...")
    
    # Test Bing search
    print("\n\nTesting Bing search...")
    bing_results = searcher.search_bing('"Emmanuel Sampson"', max_results=5)
    print(f"Found {len(bing_results)} results from Bing:")
    for i, result in enumerate(bing_results, 1):
        print(f"\n{i}. {result['title']}")
        print(f"   URL: {result['url']}")
        print(f"   Snippet: {result['snippet'][:150]}...")
    
    # Test analyzing a specific page
    print("\n\nTesting page analysis...")
    # Let's try to analyze a proper URL if we found one
    proper_urls = []
    for result in ddg_results + bing_results:
        url = result['url']
        if url.startswith('http'):
            proper_urls.append(url)
    
    if proper_urls:
        print(f"Analyzing URL: {proper_urls[0]}")
        analysis = searcher.analyze_page_content(proper_urls[0])
        if analysis:
            print(f"Page title: {analysis['title']}")
            print(f"Relevance score: {analysis['relevance_score']}")
            print(f"Contact info found: {analysis['contact_info']}")
            if analysis['relevant_paragraphs']:
                print(f"\nRelevant content:")
                for para in analysis['relevant_paragraphs'][:2]:
                    print(f"  - {para[:200]}...")
        else:
            print("Failed to analyze page")
    else:
        print("No valid URLs found to analyze")

if __name__ == "__main__":
    simple_test()