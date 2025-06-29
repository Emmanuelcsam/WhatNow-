#!/usr/bin/env python3
"""
Test script to search for Emmanuel Sampson
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main_search import PersonSearchEngine

def test_search():
    """Run a test search for Emmanuel Sampson"""
    print("Running test search for Emmanuel Sampson...")
    
    # Create search engine instance
    searcher = PersonSearchEngine(
        first_name="Emmanuel",
        last_name="Sampson",
        location="United States",  # Using a general location
        output_dir="test_search_results"
    )
    
    # Run the comprehensive search
    try:
        searcher.run_comprehensive_search()
        print("\nSearch completed successfully!")
        print(f"Results saved in: {searcher.output_dir}")
        
        # Read and display the report
        report_path = searcher.output_dir / 'report.txt'
        if report_path.exists():
            print("\n" + "="*60)
            print("REPORT PREVIEW:")
            print("="*60)
            with open(report_path, 'r', encoding='utf-8') as f:
                # Show first 100 lines of the report
                lines = f.readlines()
                for line in lines[:100]:
                    print(line.rstrip())
                if len(lines) > 100:
                    print("\n... (truncated, see full report in output directory)")
                    
    except Exception as e:
        print(f"Error during search: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_search()