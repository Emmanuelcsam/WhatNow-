#!/usr/bin/env python3
"""
Ultra-Fast Search Engine Test - Just check what's working
"""

import sys
import os
import time
import logging

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def ultra_fast_test():
    print("⚡ Ultra-Fast Search Engine Test")
    print("-" * 40)
    
    # Suppress most logging
    logging.basicConfig(level=logging.CRITICAL)
    
    try:
        from services.optimized_osint_service import ProductionOSINTService
        
        osint_service = ProductionOSINTService()
        print(f"✅ Loaded {len(osint_service.search_engines)} search engines")
        
        # List available engines
        for i, engine in enumerate(osint_service.search_engines, 1):
            print(f"  {i}. {engine.name}")
        
        # Quick test with one query
        test_query = "events Austin"
        print(f"\n🔍 Testing query: '{test_query}'")
        
        try:
            start_time = time.time()
            results = osint_service.fast_multi_engine_search(
                test_query, 
                max_results_per_engine=2,
                timeout=5.0
            )
            search_time = time.time() - start_time
            
            print(f"⏱️  Search completed in {search_time:.2f}s")
            print(f"📊 Found {len(results)} total results")
            
            if results:
                sources = list(set(r.source for r in results))
                print(f"🔗 Sources: {', '.join(sources)}")
                
                print(f"\n📄 Sample results:")
                for i, result in enumerate(results[:3]):
                    print(f"  {i+1}. {result.title[:45]}... ({result.source})")
            else:
                print("❌ No results found")
                
        except Exception as e:
            print(f"❌ Search failed: {e}")
        
        # Show performance
        print(f"\n📊 Engine Performance:")
        for engine in osint_service.search_engines:
            perf = engine.performance
            status = "✅" if perf.is_available else "❌"
            print(f"  {status} {engine.name}: {perf.success_rate:.1%} success, {perf.total_requests} requests")
            
    except Exception as e:
        print(f"💥 Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    ultra_fast_test()
