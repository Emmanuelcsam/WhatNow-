#!/usr/bin/env python3
"""
Quick Search Engine Performance Test
"""

import sys
import os
import time
import logging

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.optimized_osint_service import ProductionOSINTService

def quick_engine_test():
    """Quick test of search engines"""
    print("🔍 Quick Search Engine Test")
    print("-" * 40)
    
    # Setup logging
    logging.basicConfig(level=logging.WARNING)
    
    try:
        osint_service = ProductionOSINTService()
        
        print(f"✅ Initialized {len(osint_service.search_engines)} search engines")
        
        # Test each engine with a simple query
        test_query = "music events Austin"
        
        for engine in osint_service.search_engines:
            print(f"\n🔍 Testing {engine.name}...")
            
            try:
                start_time = time.time()
                results = engine.search(test_query, max_results=2)
                search_time = time.time() - start_time
                
                print(f"  ✅ Found {len(results)} results in {search_time:.2f}s")
                
                if results:
                    sample = results[0]
                    print(f"  📄 Sample: {sample.title[:50]}...")
                
                # Performance metrics
                perf = engine.performance
                print(f"  📊 Success rate: {perf.success_rate:.1%}")
                print(f"  ⏱️  Avg time: {perf.avg_response_time:.2f}s")
                print(f"  🔗 Available: {perf.is_available}")
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
            
            time.sleep(1)  # Rate limiting
        
        # Test multi-engine search
        print(f"\n🚀 Testing multi-engine search...")
        
        try:
            start_time = time.time()
            results = osint_service.fast_multi_engine_search(test_query, max_results_per_engine=2, timeout=8.0)
            search_time = time.time() - start_time
            
            sources = list(set(r.source for r in results))
            print(f"  ✅ Found {len(results)} results from {len(sources)} sources in {search_time:.2f}s")
            print(f"  🔗 Sources: {', '.join(sources)}")
            
            for i, result in enumerate(results[:3]):
                print(f"    {i+1}. {result.title[:40]}... (Score: {result.relevance_score:.2f})")
        
        except Exception as e:
            print(f"  ❌ Multi-engine error: {e}")
        
        # Performance report
        print(f"\n📊 Performance Report:")
        performance_report = osint_service.get_performance_report()
        print(performance_report)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    quick_engine_test()
