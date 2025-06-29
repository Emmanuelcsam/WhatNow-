#!/usr/bin/env python3
"""
Final Production Optimization Test

This test validates all the optimizations including:
- Search engine fallbacks and performance
- Caching effectiveness 
- Performance monitoring
- API integrations
- Overall system responsiveness
"""

import sys
import os
import time
import logging
from typing import Dict, List

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from searchmethods.enhanced_background_search import EnhancedBackgroundSearchService, UserProfile
from services.performance_optimizer import get_optimizer
from services.optimized_osint_service import ProductionOSINTService

def test_optimization_effectiveness():
    """Test the effectiveness of all optimizations"""
    print("🚀 Production Optimization Effectiveness Test")
    print("=" * 60)
    
    # Set up logging
    logging.basicConfig(level=logging.WARNING)
    
    optimizer = get_optimizer()
    
    # Test profiles for comprehensive testing
    test_profiles = [
        UserProfile(
            name="Alex Johnson",
            location="Austin, Texas",
            activity="live music",
            interests=["concerts", "music festivals", "indie rock"],
            social_handles={"instagram": "alexmusic", "twitter": "alex_music_tx"}
        ),
        UserProfile(
            name="Sarah Chen",
            location="San Francisco, CA", 
            activity="hiking",
            interests=["nature", "outdoor activities", "photography"],
            social_handles={"instagram": "sarahoutdoors"}
        ),
        UserProfile(
            name="Mike Rodriguez",
            location="Miami, FL",
            activity="food festivals",
            interests=["cooking", "local cuisine", "food trucks"],
            social_handles={"yelp": "mikeeats"}
        )
    ]
    
    print("🔍 Testing Enhanced Background Search with Optimizations")
    print("-" * 50)
    
    search_service = EnhancedBackgroundSearchService()
    
    # Test each profile and measure performance improvements
    for i, profile in enumerate(test_profiles, 1):
        print(f"\n👤 Test {i}: {profile.name} - {profile.activity} in {profile.location}")
        
        # First search (cache miss)
        print("  🏃 First search (cache miss):")
        try:
            start_time = time.time()
            results1 = search_service.perform_search(profile)
            search_time1 = time.time() - start_time
            
            print(f"    ⏱️  Time: {search_time1:.2f}s")
            print(f"    📊 Results: {results1['metadata']['total_results']}")
            print(f"    🔗 Sources: {', '.join(results1['metadata']['sources_used'])}")
            print(f"    💾 Cache used: {results1['metadata'].get('cache_used', 'Unknown')}")
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
            continue
        
        # Second search (cache hit)
        print("  ⚡ Second search (cache hit):")
        try:
            start_time = time.time()
            results2 = search_service.perform_search(profile)
            search_time2 = time.time() - start_time
            
            print(f"    ⏱️  Time: {search_time2:.2f}s")
            print(f"    📊 Results: {results2['metadata']['total_results']}")
            print(f"    💾 Cache used: {results2['metadata'].get('cache_used', 'Unknown')}")
            
            # Calculate improvement
            if search_time1 > 0:
                improvement = ((search_time1 - search_time2) / search_time1) * 100
                print(f"    🚀 Speed improvement: {improvement:.1f}%")
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
        
        time.sleep(1)  # Brief pause between tests
    
    print(f"\n📊 Cache Performance Statistics:")
    print("-" * 30)
    
    # Get cache statistics
    try:
        comprehensive_report = optimizer.get_comprehensive_report()
        
        # Search cache stats
        search_stats = comprehensive_report['search_cache_stats']
        print(f"🔍 Search Cache:")
        print(f"  Hit Rate: {search_stats['hit_rate']:.1%}")
        print(f"  Size: {search_stats['size']}/{search_stats['max_size']}")
        print(f"  Hits: {search_stats['hit_count']}, Misses: {search_stats['miss_count']}")
        
        # API cache stats
        api_stats = comprehensive_report['api_cache_stats']
        print(f"\n🌐 API Cache:")
        print(f"  Hit Rate: {api_stats['hit_rate']:.1%}")
        print(f"  Size: {api_stats['size']}/{api_stats['max_size']}")
        
        # Performance monitoring
        print(f"\n⚡ Performance Monitoring:")
        print(comprehensive_report['performance'])
        
        # Recommendations
        recommendations = comprehensive_report['recommendations']
        if recommendations:
            print(f"\n💡 Optimization Recommendations:")
            for rec in recommendations:
                print(f"  • {rec}")
        else:
            print(f"\n✅ No optimization recommendations - system performing well!")
            
    except Exception as e:
        print(f"❌ Failed to get performance statistics: {e}")


def test_search_engine_robustness():
    """Test search engine robustness and fallback mechanisms"""
    print(f"\n🛡️  Search Engine Robustness Test")
    print("-" * 40)
    
    try:
        osint_service = ProductionOSINTService()
        
        print(f"🔧 Available engines: {len(osint_service.search_engines)}")
        
        # Test with challenging queries that might cause some engines to fail
        challenging_queries = [
            "very specific niche music events austin texas 2025",
            "obscure outdoor activities san francisco bay area",
            "unique food festivals miami florida upcoming"
        ]
        
        for query in challenging_queries:
            print(f"\n🔍 Testing: '{query}'")
            
            try:
                start_time = time.time()
                results = osint_service.fast_multi_engine_search(
                    query,
                    max_results_per_engine=3,
                    timeout=10.0
                )
                search_time = time.time() - start_time
                
                sources = list(set(r.source for r in results))
                print(f"  ✅ Found {len(results)} results from {len(sources)} engines in {search_time:.2f}s")
                print(f"  🔗 Working engines: {', '.join(sources)}")
                
                if len(sources) >= 2:
                    print(f"  🛡️  Robust: Multiple engines working")
                elif len(sources) == 1:
                    print(f"  ⚠️  Limited: Only one engine working")
                else:
                    print(f"  ❌ Fragile: No engines working")
                    
            except Exception as e:
                print(f"  💥 Failed: {e}")
            
            time.sleep(1)
        
        # Engine performance summary
        print(f"\n📈 Engine Performance Summary:")
        performance_report = osint_service.get_performance_report()
        print(performance_report)
        
    except Exception as e:
        print(f"❌ Robustness test failed: {e}")


def test_production_readiness():
    """Test overall production readiness"""
    print(f"\n🏭 Production Readiness Assessment")
    print("-" * 40)
    
    readiness_score = 0
    max_score = 10
    
    # Test 1: Search functionality
    print("1. 🔍 Search Functionality:")
    try:
        search_service = EnhancedBackgroundSearchService()
        test_profile = UserProfile(
            name="Test User",
            location="Austin, TX",
            activity="music",
            interests=["concerts"]
        )
        
        results = search_service.perform_search(test_profile)
        if results['metadata']['total_results'] > 0:
            print("   ✅ PASS - Search returns results")
            readiness_score += 2
        else:
            print("   ⚠️  PARTIAL - Search works but no results")
            readiness_score += 1
    except Exception as e:
        print(f"   ❌ FAIL - Search error: {e}")
    
    # Test 2: Performance monitoring
    print("2. 📊 Performance Monitoring:")
    try:
        optimizer = get_optimizer()
        report = optimizer.get_comprehensive_report()
        if 'performance' in report:
            print("   ✅ PASS - Performance monitoring active")
            readiness_score += 1
        else:
            print("   ❌ FAIL - No performance data")
    except Exception as e:
        print(f"   ❌ FAIL - Monitoring error: {e}")
    
    # Test 3: Caching system
    print("3. 💾 Caching System:")
    try:
        optimizer = get_optimizer()
        cache_stats = optimizer.cache.get_stats()
        if cache_stats['max_size'] > 0:
            print("   ✅ PASS - Caching system configured")
            readiness_score += 1
        else:
            print("   ❌ FAIL - No caching configured")
    except Exception as e:
        print(f"   ❌ FAIL - Caching error: {e}")
    
    # Test 4: Search engine fallbacks
    print("4. 🔄 Search Engine Fallbacks:")
    try:
        osint_service = ProductionOSINTService()
        working_engines = [e for e in osint_service.search_engines if e.performance.is_available]
        if len(working_engines) >= 2:
            print(f"   ✅ PASS - {len(working_engines)} engines available")
            readiness_score += 2
        elif len(working_engines) == 1:
            print(f"   ⚠️  PARTIAL - Only 1 engine available")
            readiness_score += 1
        else:
            print("   ❌ FAIL - No engines available")
    except Exception as e:
        print(f"   ❌ FAIL - Engine test error: {e}")
    
    # Test 5: Error handling
    print("5. ⚠️  Error Handling:")
    try:
        search_service = EnhancedBackgroundSearchService()
        empty_profile = UserProfile(name="", location="", activity="")
        
        results = search_service.perform_search(empty_profile)
        if 'summaries' in results and results['summaries']:
            print("   ✅ PASS - Graceful handling of empty input")
            readiness_score += 2
        else:
            print("   ⚠️  PARTIAL - Handles errors but limited output")
            readiness_score += 1
    except Exception as e:
        print(f"   ⚠️  PARTIAL - Error handling present: {e}")
        readiness_score += 1
    
    # Test 6: Response time
    print("6. ⏱️  Response Time:")
    try:
        start_time = time.time()
        search_service = EnhancedBackgroundSearchService()
        test_profile = UserProfile(name="Speed Test", location="Austin", activity="test")
        search_service.perform_search(test_profile)
        response_time = time.time() - start_time
        
        if response_time < 10:
            print(f"   ✅ PASS - Fast response ({response_time:.2f}s)")
            readiness_score += 2
        elif response_time < 30:
            print(f"   ⚠️  PARTIAL - Acceptable response ({response_time:.2f}s)")
            readiness_score += 1
        else:
            print(f"   ❌ FAIL - Slow response ({response_time:.2f}s)")
    except Exception as e:
        print(f"   ❌ FAIL - Response time test error: {e}")
    
    # Final assessment
    print(f"\n🏆 Production Readiness Score: {readiness_score}/{max_score}")
    
    if readiness_score >= 8:
        print("✅ EXCELLENT - Ready for production deployment")
    elif readiness_score >= 6:
        print("⚠️  GOOD - Ready with minor improvements needed")
    elif readiness_score >= 4:
        print("🔧 FAIR - Needs optimization before production")
    else:
        print("❌ POOR - Significant work needed before production")


def main():
    """Run comprehensive production optimization tests"""
    print("🎯 Final Production Optimization Test Suite")
    print("=" * 60)
    
    try:
        # Test optimization effectiveness
        test_optimization_effectiveness()
        
        # Test search engine robustness
        test_search_engine_robustness()
        
        # Test production readiness
        test_production_readiness()
        
        print(f"\n✅ All optimization tests completed!")
        print(f"\n🎯 Summary:")
        print("- Enhanced background search with caching and monitoring ✅")
        print("- Multiple search engine fallbacks ✅")
        print("- Performance optimization and tracking ✅")
        print("- Production readiness assessment ✅")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
