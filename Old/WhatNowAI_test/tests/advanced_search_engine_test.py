#!/usr/bin/env python3
"""
Advanced Search Engine Performance Test

This script tests and optimizes the search engine performance with additional fallback mechanisms,
validates OSINT integration, and tests which search engines work best beyond DuckDuckGo.
"""

import sys
import os
import time
import asyncio
import concurrent.futures
from typing import Dict, List, Any
import logging

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.optimized_osint_service import ProductionOSINTService
from services.newsapi_service import NewsAPIEventService  
from services.allevents_service_enhanced import EnhancedAllEventsService
from searchmethods.enhanced_background_search import EnhancedBackgroundSearchService, UserProfile
from config.settings import NEWSAPI_KEY, ALLEVENTS_API_KEY


def setup_logging():
    """Setup detailed logging for test"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Reduce noise from some loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)


def test_individual_search_engines():
    """Test each search engine individually"""
    print("\n" + "="*50)
    print("INDIVIDUAL SEARCH ENGINE TESTING")
    print("="*50)
    
    osint_service = ProductionOSINTService()
    test_queries = [
        "music events New York",
        "hiking groups San Francisco", 
        "tech meetups Austin",
        "art galleries Boston",
        "food festivals Chicago"
    ]
    
    results_summary = {}
    
    for engine in osint_service.search_engines:
        print(f"\n🔍 Testing {engine.name}...")
        engine_results = []
        
        for query in test_queries:
            try:
                start_time = time.time()
                results = engine.search(query, max_results=3)
                search_time = time.time() - start_time
                
                engine_results.append({
                    'query': query,
                    'results_count': len(results),
                    'search_time': search_time,
                    'success': len(results) > 0
                })
                
                print(f"  Query: '{query}' → {len(results)} results in {search_time:.2f}s")
                
                # Show sample result
                if results:
                    sample = results[0]
                    print(f"    Sample: {sample.title[:60]}...")
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"  Query: '{query}' → ERROR: {e}")
                engine_results.append({
                    'query': query,
                    'results_count': 0,
                    'search_time': 0,
                    'success': False,
                    'error': str(e)
                })
        
        # Calculate statistics
        successful_searches = [r for r in engine_results if r['success']]
        success_rate = len(successful_searches) / len(engine_results) if engine_results else 0
        avg_time = sum(r['search_time'] for r in successful_searches) / len(successful_searches) if successful_searches else 0
        avg_results = sum(r['results_count'] for r in successful_searches) / len(successful_searches) if successful_searches else 0
        
        results_summary[engine.name] = {
            'success_rate': success_rate,
            'avg_time': avg_time,
            'avg_results': avg_results,
            'total_tests': len(engine_results),
            'performance_score': engine.performance.success_rate
        }
        
        print(f"  📊 Summary: {success_rate:.1%} success, {avg_time:.2f}s avg, {avg_results:.1f} results avg")
    
    return results_summary


def test_multi_engine_fallback():
    """Test multi-engine fallback mechanisms"""
    print("\n" + "="*50)
    print("MULTI-ENGINE FALLBACK TESTING")
    print("="*50)
    
    osint_service = ProductionOSINTService()
    
    test_scenarios = [
        "live music Denver this weekend",
        "outdoor activities Portland Oregon",
        "food trucks Miami events",
        "coding bootcamp meetups Seattle",
        "vintage car shows Los Angeles"
    ]
    
    for scenario in test_scenarios:
        print(f"\n🚀 Testing: '{scenario}'")
        
        try:
            start_time = time.time()
            results = osint_service.fast_multi_engine_search(
                scenario, 
                max_results_per_engine=3,
                timeout=8.0
            )
            search_time = time.time() - start_time
            
            print(f"  Results: {len(results)} found in {search_time:.2f}s")
            
            # Show sources used
            sources = list(set(r.source for r in results))
            print(f"  Sources: {', '.join(sources)}")
            
            # Show sample results
            for i, result in enumerate(results[:3]):
                print(f"    {i+1}. {result.title[:50]}... (Score: {result.relevance_score:.2f})")
            
        except Exception as e:
            print(f"  ERROR: {e}")
        
        time.sleep(1)


def test_production_osint_integration():
    """Test the full production OSINT integration"""
    print("\n" + "="*50)
    print("PRODUCTION OSINT INTEGRATION TEST")
    print("="*50)
    
    test_profiles = [
        {
            'name': 'Alex Johnson',
            'location': 'Austin, Texas',
            'activity': 'live music',
            'interests': ['concerts', 'indie rock', 'music festivals']
        },
        {
            'name': 'Sarah Chen',
            'location': 'San Francisco, CA',
            'activity': 'hiking',
            'interests': ['nature', 'outdoor activities', 'photography']
        },
        {
            'name': 'Mike Rodriguez',
            'location': 'Miami, FL',
            'activity': 'food festivals',
            'interests': ['cooking', 'local cuisine', 'food trucks']
        }
    ]
    
    osint_service = ProductionOSINTService()
    
    for profile in test_profiles:
        print(f"\n👤 Testing profile: {profile['name']} in {profile['location']}")
        
        try:
            start_time = time.time()
            results = osint_service.perform_fast_osint_search(profile, timeout=10.0)
            search_time = time.time() - start_time
            
            print(f"  📊 Results: {results['filtered_count']}/{results['total_found']} relevant")
            print(f"  ⏱️  Time: {search_time:.2f}s ({results['queries_executed']} queries)")
            print(f"  🔗 Sources: {', '.join(results['sources_used'])}")
            
            # Show top results
            for i, result in enumerate(results['results'][:3]):
                print(f"    {i+1}. {result.title[:50]}... (Relevance: {result.relevance_score:.2f})")
            
        except Exception as e:
            print(f"  ERROR: {e}")
        
        time.sleep(1)


def test_enhanced_background_search():
    """Test the enhanced background search service"""
    print("\n" + "="*50)
    print("ENHANCED BACKGROUND SEARCH INTEGRATION TEST")
    print("="*50)
    
    search_service = EnhancedBackgroundSearchService()
    
    test_profiles = [
        UserProfile(
            name="Jessica Taylor",
            location="Seattle, WA",
            activity="tech meetups",
            interests=["programming", "AI", "networking"],
            social_handles={"github": "jessicatech", "linkedin": "jessica-taylor-dev"}
        ),
        UserProfile(
            name="David Kim",
            location="Portland, OR",
            activity="craft beer",
            interests=["brewing", "local beer", "beer festivals"],
            social_handles={"instagram": "davidbrews"}
        )
    ]
    
    for profile in test_profiles:
        print(f"\n👤 Testing: {profile.name} - {profile.activity} in {profile.location}")
        
        try:
            start_time = time.time()
            results = search_service.perform_search(profile)
            search_time = time.time() - start_time
            
            print(f"  ⏱️  Search completed in {search_time:.2f}s")
            print(f"  📊 Total results: {results['metadata']['total_results']}")
            print(f"  🔗 Sources used: {', '.join(results['metadata']['sources_used'])}")
            print(f"  🚀 Fast mode: {results['metadata']['fast_mode']}")
            print(f"  📰 NewsAPI available: {results['metadata']['news_api_available']}")
            
            # Show summaries
            print("  📋 Summaries:")
            for category, summary in results['summaries'].items():
                print(f"    {category}: {summary}")
            
            # Show sample results from each category
            for category, category_results in results['raw_results'].items():
                if category_results:
                    print(f"  🔍 {category.title()} sample:")
                    sample = category_results[0]
                    print(f"    {sample.title[:60]}...")
            
        except Exception as e:
            print(f"  ERROR: {e}")
        
        time.sleep(1)


def test_newsapi_integration():
    """Test NewsAPI integration"""
    print("\n" + "="*50)
    print("NEWSAPI INTEGRATION TEST")
    print("="*50)
    
    if not NEWSAPI_KEY:
        print("❌ NewsAPI key not configured")
        return
    
    try:
        news_service = NewsAPIEventService(NEWSAPI_KEY)
        
        test_locations = ["New York, NY", "Los Angeles, CA", "Chicago, IL"]
        
        for location in test_locations:
            print(f"\n📍 Testing location: {location}")
            
            try:
                events = news_service.search_local_events(
                    location=location,
                    user_interests=["music", "food"],
                    user_activity="events",
                    days_ahead=7
                )
                
                print(f"  Found {len(events)} events")
                
                for i, event in enumerate(events[:3]):
                    print(f"    {i+1}. {event.title[:50]}... (Score: {event.confidence_score:.2f})")
                
            except Exception as e:
                print(f"  ERROR: {e}")
            
            time.sleep(1)
    
    except Exception as e:
        print(f"❌ NewsAPI test failed: {e}")


def test_allevents_api():
    """Test AllEvents API integration"""
    print("\n" + "="*50)
    print("ALLEVENTS API INTEGRATION TEST")
    print("="*50)
    
    if not ALLEVENTS_API_KEY:
        print("❌ AllEvents API key not configured")
        return
    
    try:
        allevents_service = EnhancedAllEventsService(ALLEVENTS_API_KEY)
        
        test_cities = ["New York", "San Francisco", "Austin"]
        
        for city in test_cities:
            print(f"\n🏙️  Testing city: {city}")
            
            try:
                events = allevents_service.search_events_by_location(
                    location=city,
                    category="music",
                    limit=5
                )
                
                print(f"  Found {len(events)} events")
                
                for i, event in enumerate(events[:3]):
                    print(f"    {i+1}. {event.get('title', 'No title')[:50]}...")
                
            except Exception as e:
                print(f"  ERROR: {e}")
            
            time.sleep(1)
    
    except Exception as e:
        print(f"❌ AllEvents test failed: {e}")


def generate_performance_report(engine_results):
    """Generate a comprehensive performance report"""
    print("\n" + "="*50)
    print("COMPREHENSIVE PERFORMANCE REPORT")
    print("="*50)
    
    # Rank engines by performance
    ranked_engines = sorted(
        engine_results.items(),
        key=lambda x: (x[1]['success_rate'], -x[1]['avg_time'], x[1]['avg_results']),
        reverse=True
    )
    
    print("\n🏆 Search Engine Rankings:")
    for i, (engine, stats) in enumerate(ranked_engines, 1):
        status = "🟢" if stats['success_rate'] > 0.7 else "🟡" if stats['success_rate'] > 0.3 else "🔴"
        print(f"  {i}. {status} {engine}")
        print(f"     Success Rate: {stats['success_rate']:.1%}")
        print(f"     Avg Time: {stats['avg_time']:.2f}s")
        print(f"     Avg Results: {stats['avg_results']:.1f}")
    
    # Recommendations
    print("\n💡 Recommendations:")
    
    best_engine = ranked_engines[0]
    if best_engine[1]['success_rate'] > 0.8:
        print(f"  ✅ Primary engine: {best_engine[0]} (excellent performance)")
    else:
        print(f"  ⚠️  Primary engine: {best_engine[0]} (acceptable but needs monitoring)")
    
    working_engines = [name for name, stats in ranked_engines if stats['success_rate'] > 0.5]
    print(f"  🔄 Fallback engines: {', '.join(working_engines[1:])}")
    
    failed_engines = [name for name, stats in ranked_engines if stats['success_rate'] < 0.3]
    if failed_engines:
        print(f"  ❌ Problematic engines: {', '.join(failed_engines)}")
        print("     Consider debugging these engines or adding more alternatives")


def main():
    """Run all advanced search engine tests"""
    print("🚀 Starting Advanced Search Engine Performance Testing...")
    setup_logging()
    
    try:
        # Test individual search engines
        engine_results = test_individual_search_engines()
        
        # Test multi-engine fallback
        test_multi_engine_fallback()
        
        # Test production OSINT integration
        test_production_osint_integration()
        
        # Test enhanced background search
        test_enhanced_background_search()
        
        # Test NewsAPI integration
        test_newsapi_integration()
        
        # Test AllEvents API
        test_allevents_api()
        
        # Generate performance report
        generate_performance_report(engine_results)
        
        print("\n✅ Advanced testing completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Testing failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
