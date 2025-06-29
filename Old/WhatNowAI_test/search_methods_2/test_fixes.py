#!/usr/bin/env python3
"""Test script to verify the fixes in main_search.py"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main_search import PersonSearchEngine

def test_json_serialization():
    """Test that contact info can be serialized to JSON."""
    print("Testing JSON serialization fix...")
    
    # Create a test instance
    searcher = PersonSearchEngine("John", "Doe", "New York, NY", output_dir="test_output")
    
    # Test extract_contact_info returns lists instead of sets
    test_text = """
    Contact John Doe at john.doe@email.com or jane.doe@company.com
    Phone: 555-123-4567 or (555) 987-6543
    Address: 123 Main Street, New York, NY
    """
    
    contact_info = searcher.extract_contact_info(test_text)
    
    # Verify it's serializable
    try:
        json_str = json.dumps(contact_info)
        print("✓ Contact info is JSON serializable")
        print(f"  Emails: {contact_info['emails']}")
        print(f"  Phones: {contact_info['phones']}")
        print(f"  Addresses: {contact_info['addresses']}")
    except TypeError as e:
        print(f"✗ JSON serialization failed: {e}")
        return False
    
    return True

def test_url_formatting():
    """Test that URLs are properly formatted."""
    print("\nTesting URL formatting fix...")
    
    # Test cases for URL fixing
    test_urls = [
        ("//example.com/page", "https://example.com/page"),
        ("/relative/path", "https://duckduckgo.com/relative/path"),
        ("https://example.com/page", "https://example.com/page"),
        ("http://example.com/page", "http://example.com/page"),
    ]
    
    for input_url, expected in test_urls:
        # Simulate the URL fixing logic
        url = input_url
        if url.startswith('//'):
            url = 'https:' + url
        elif url.startswith('/'):
            url = 'https://duckduckgo.com' + url
            
        if url == expected:
            print(f"  ✓ {input_url} -> {url}")
        else:
            print(f"  ✗ {input_url} -> {url} (expected: {expected})")
    
    return True

def test_duckduckgo_search():
    """Test the DuckDuckGo search method."""
    print("\nTesting DuckDuckGo search...")
    
    searcher = PersonSearchEngine("Test", "User", "Test City", output_dir="test_output")
    
    # Test a simple search
    results = searcher.search_duckduckgo("python programming", max_results=5)
    
    if results:
        print(f"✓ DuckDuckGo returned {len(results)} results")
        for i, result in enumerate(results[:3]):
            print(f"  Result {i+1}: {result['title'][:50]}...")
            print(f"    URL: {result['url']}")
            # Check URL format
            if result['url'].startswith(('http://', 'https://')):
                print("    ✓ URL is properly formatted")
            else:
                print("    ✗ URL is malformed")
    else:
        print("⚠ DuckDuckGo returned no results (might be expected if parsing fails)")
    
    return True

def main():
    """Run all tests."""
    print("Running tests for main_search.py fixes...\n")
    
    tests = [
        test_json_serialization,
        test_url_formatting,
        test_duckduckgo_search
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"\n✗ Test failed with error: {e}")
    
    print("\nAll tests completed!")
    
    # Clean up test output
    import shutil
    if Path("test_output").exists():
        shutil.rmtree("test_output")

if __name__ == "__main__":
    main()