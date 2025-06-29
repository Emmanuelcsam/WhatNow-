#!/usr/bin/env python3
"""
Search Engine Fallback Test and Performance Optimization

Tests which search engines work best and implements intelligent fallback mechanisms.
"""

import sys
import os
import time
import logging
from typing import Dict, List

# Add current directory to path  
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.optimized_osint_service import ProductionOSINTService

def test_search_engine_fallbacks():
    """Test search engine fallback mechanisms"""
    print("🔍 Testing Search Engine Fallback Mechanisms")
    print("=" * 60)
    
    # Set up minimal logging
    logging.basicConfig(level=logging.ERROR)
    
    try:
        osint_service = ProductionOSINTService()
        
        print(f"✅ Initialized with {len(osint_service.search_engines)} search engines")
        
        # Print available engines
        print("\n🌐 Available Search Engines:")
        for i, engine in enumerate(osint_service.search_engines, 1):
            print(f"  {i}. {engine.name}")
        
        # Test queries that should return results
        test_queries = [
            "music events Austin Texas",
            "hiking San Francisco",
            "food festivals Miami", 
            "tech meetups Seattle",
            "art galleries Boston"
        ]
        
        engine_performance = {}
        
        print(f"\n🔬 Testing Individual Engines:")
        print("-" * 40)
        
        # Test each engine individually
        for engine in osint_service.search_engines:
            print(f"\n🔍 Testing {engine.name}...")
            
            successes = 0
            total_time = 0
            total_results = 0
            
            for query in test_queries[:3]:  # Test with first 3 queries
                try:
                    start_time = time.time()
                    results = engine.search(query, max_results=3)
                    search_time = time.time() - start_time
                    
                    if results:
                        successes += 1
                        total_results += len(results)
                        print(f"  ✅ '{query}' → {len(results)} results in {search_time:.2f}s")
                        
                        # Show a sample result
                        if results:
                            sample = results[0]
                            print(f"     Sample: {sample.title[:50]}...")
                    else:
                        print(f"  ❌ '{query}' → No results in {search_time:.2f}s")
                    
                    total_time += search_time
                    time.sleep(0.5)  # Short delay between queries
                    
                except Exception as e:
                    print(f"  💥 '{query}' → Error: {str(e)[:50]}...")
            
            # Calculate performance metrics
            success_rate = successes / len(test_queries[:3])
            avg_time = total_time / len(test_queries[:3])
            avg_results = total_results / max(successes, 1)
            
            engine_performance[engine.name] = {
                'success_rate': success_rate,
                'avg_time': avg_time,
                'avg_results': avg_results,
                'working': success_rate > 0.3
            }
            
            status = "🟢" if success_rate > 0.7 else "🟡" if success_rate > 0.3 else "🔴"
            print(f"  {status} Performance: {success_rate:.1%} success, {avg_time:.2f}s avg")
        
        print(f"\n🚀 Testing Multi-Engine Fallback:")
        print("-" * 40)
        
        # Test multi-engine search with fallback
        for query in test_queries[:2]:  # Test with 2 queries
            print(f"\n🔍 Multi-engine search: '{query}'")
            
            try:
                start_time = time.time()
                results = osint_service.fast_multi_engine_search(
                    query, 
                    max_results_per_engine=3,
                    timeout=8.0
                )
                search_time = time.time() - start_time
                
                sources = list(set(r.source for r in results))
                print(f"  ✅ Found {len(results)} results from {len(sources)} sources in {search_time:.2f}s")
                print(f"  🔗 Sources used: {', '.join(sources)}")
                
                # Show top results
                for i, result in enumerate(results[:3]):
                    print(f"    {i+1}. {result.title[:45]}... (Score: {result.relevance_score:.2f})")
                
            except Exception as e:
                print(f"  ❌ Multi-engine search failed: {e}")
        
        # Generate recommendations
        print(f"\n💡 Search Engine Recommendations:")
        print("-" * 40)
        
        # Rank engines by performance
        working_engines = [(name, perf) for name, perf in engine_performance.items() if perf['working']]
        working_engines.sort(key=lambda x: (x[1]['success_rate'], -x[1]['avg_time']), reverse=True)
        
        if working_engines:
            print(f"✅ Best performing engines:")
            for i, (name, perf) in enumerate(working_engines[:3], 1):
                print(f"  {i}. {name}: {perf['success_rate']:.1%} success, {perf['avg_time']:.2f}s avg")
            
            failed_engines = [name for name, perf in engine_performance.items() if not perf['working']]
            if failed_engines:
                print(f"\n⚠️  Engines needing attention: {', '.join(failed_engines)}")
        else:
            print("❌ No engines are working properly - this needs immediate attention!")
        
        # Performance report
        print(f"\n📊 Overall Performance Report:")
        performance_report = osint_service.get_performance_report()
        print(performance_report)
        
        return engine_performance
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return {}


def test_production_search_with_profile():
    """Test the production search with a real user profile"""
    print(f"\n🎯 Testing Production Search with User Profile:")
    print("-" * 50)
    
    osint_service = ProductionOSINTService()
    
    # Test profile
    test_profile = {
        'name': 'Alex Johnson',
        'location': 'Austin, Texas',
        'activity': 'live music',
        'interests': ['concerts', 'music festivals', 'indie rock']
    }
    
    print(f"👤 Profile: {test_profile['name']} - {test_profile['activity']} in {test_profile['location']}")
    
    try:
        start_time = time.time()
        results = osint_service.perform_fast_osint_search(test_profile, timeout=15.0)
        search_time = time.time() - start_time
        
        print(f"⏱️  Search completed in {search_time:.2f}s")
        print(f"📊 Results: {results['filtered_count']}/{results['total_found']} relevant")
        print(f"🔗 Sources: {', '.join(results['sources_used'])}")
        print(f"🔍 Queries: {results['queries_executed']}")
        
        # Show top results
        print(f"\n🎯 Top Results:")
        for i, result in enumerate(results['results'][:5]):
            print(f"  {i+1}. {result.title[:50]}...")
            print(f"     Score: {result.relevance_score:.2f} | Source: {result.source}")
        
        # Performance summary
        if 'performance_summary' in results:
            print(f"\n📈 Engine Performance Summary:")
            for engine, stats in results['performance_summary'].items():
                if stats['is_available']:
                    print(f"  ✅ {engine}: {stats['success_rate']:.1%} success")
                else:
                    print(f"  ❌ {engine}: unavailable")
        
    except Exception as e:
        print(f"❌ Production search failed: {e}")


def main():
    """Run search engine fallback tests"""
    print("🚀 Search Engine Fallback and Performance Testing")
    print("=" * 60)
    
    # Test search engine fallbacks
    engine_performance = test_search_engine_fallbacks()
    
    # Test production search
    test_production_search_with_profile()
    
    print(f"\n✅ Testing completed!")
    
    # Summary
    if engine_performance:
        working_count = sum(1 for perf in engine_performance.values() if perf['working'])
        total_count = len(engine_performance)
        print(f"📊 Summary: {working_count}/{total_count} search engines are working properly")
        
        if working_count >= 2:
            print("✅ Sufficient fallback mechanisms are in place")
        else:
            print("⚠️  Consider adding more search engines for better fallback support")
    
    print("\n🎯 Next steps:")
    print("  1. Monitor search engine performance regularly")
    print("  2. Add more search engines if needed")
    print("  3. Implement intelligent engine selection based on query type")
    print("  4. Consider caching successful queries to reduce load")


if __name__ == "__main__":
    main()
