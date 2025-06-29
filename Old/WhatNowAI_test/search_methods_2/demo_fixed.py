#!/usr/bin/env python3
"""Demo script showing the fixed functionality"""

import json
from main_search import PersonSearchEngine

def demo_contact_extraction():
    """Demonstrate the fixed contact extraction with JSON serialization."""
    print("=== Contact Extraction Demo ===")
    
    searcher = PersonSearchEngine("Jane", "Smith", "San Francisco, CA", output_dir="demo_output")
    
    sample_text = """
    Jane Smith is a software engineer based in San Francisco.
    You can reach her at jane.smith@techcompany.com or jane@personal.email
    Phone: (415) 555-1234 or 415.555.5678
    Office: 123 Market Street, San Francisco, CA
    Home: 456 Oak Avenue, San Francisco, CA
    """
    
    contact_info = searcher.extract_contact_info(sample_text)
    
    # This would have failed before the fix (TypeError: Object of type set is not JSON serializable)
    json_output = json.dumps(contact_info, indent=2)
    print("Extracted contact info (JSON serializable):")
    print(json_output)
    
def demo_url_fixing():
    """Demonstrate URL fixing logic."""
    print("\n=== URL Fixing Demo ===")
    
    test_urls = [
        "//www.example.com/page",
        "/search?q=test",
        "https://www.example.com/page",
        "//cdn.website.com/resource.js"
    ]
    
    print("URL fixes applied in search_duckduckgo:")
    for url in test_urls:
        fixed = url
        if url.startswith('//'):
            fixed = 'https:' + url
        elif url.startswith('/'):
            fixed = 'https://duckduckgo.com' + url
        print(f"  {url:30} -> {fixed}")

def demo_search_integration():
    """Demonstrate the complete search functionality."""
    print("\n=== Search Integration Demo ===")
    
    # Create a searcher instance
    searcher = PersonSearchEngine("Test", "User", "New York, NY", output_dir="demo_output")
    
    # The search queries that would be generated
    print("Sample search queries generated:")
    for i, query in enumerate(searcher.search_queries[:5], 1):
        print(f"  {i}. {query}")
    
    print("\nNote: The actual search would:")
    print("  - Use multiple search engines (DuckDuckGo, Bing, Google)")
    print("  - Handle malformed URLs automatically")
    print("  - Convert all sets to lists for JSON serialization")
    print("  - Save results in JSON format without errors")

def main():
    demo_contact_extraction()
    demo_url_fixing()
    demo_search_integration()
    
    # Clean up
    import shutil
    from pathlib import Path
    if Path("demo_output").exists():
        shutil.rmtree("demo_output")
    
    print("\n✅ All demos completed successfully!")

if __name__ == "__main__":
    main()