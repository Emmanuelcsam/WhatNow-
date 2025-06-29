#!/usr/bin/env python3
"""
Production OSINT and Web Scraping Optimization Test
Tests the performance and effectiveness of different search engines and methods
"""

import sys
import time
import json
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_search_engine_performance():
    """Test different search engines and their performance"""
    print("=" * 80)
    print("🔍 SEARCH ENGINE PERFORMANCE TEST")
    print("=" * 80)
    
    # Test queries
    test_queries = [
        "technology events Baltimore MD",
        "music concerts Washington DC",
        "networking meetups Maryland",
        "art galleries Baltimore events"
    ]
    
    search_engines = []
    
    try:
        # Test DuckDuckGo
        from services.optimized_osint_service import ProductionOSINTService
        
        config = {'TIMEOUT': 5, 'FAST_MODE': True}
        osint_service = ProductionOSINTService(config)
        
        print("🦆 Testing DuckDuckGo Search Engine...")
        ddg_results = []
        ddg_times = []
        
        for query in test_queries:
            start_time = time.time()
            try:
                results = osint_service.search_duckduckgo_optimized(query, max_results=5)
                search_time = time.time() - start_time
                ddg_results.append(len(results))
                ddg_times.append(search_time)
                print(f"   Query: '{query[:30]}...' -> {len(results)} results in {search_time:.2f}s")
            except Exception as e:
                print(f"   Query: '{query[:30]}...' -> FAILED: {e}")
                ddg_results.append(0)
                ddg_times.append(0)
        
        search_engines.append({
            'name': 'DuckDuckGo',
            'total_results': sum(ddg_results),
            'avg_time': sum(ddg_times) / len(ddg_times) if ddg_times else 0,
            'success_rate': len([r for r in ddg_results if r > 0]) / len(ddg_results)
        })
        
    except Exception as e:
        print(f"❌ DuckDuckGo test failed: {e}")
    
    try:
        # Test Alternative Search Engines
        print("\n🔍 Testing Alternative Search Methods...")
        
        from services.enhanced_search_service import EnhancedSearchService
        
        enhanced_search = EnhancedSearchService()
        alt_results = []
        alt_times = []
        
        for query in test_queries:
            start_time = time.time()
            try:
                results = enhanced_search.search_comprehensive(
                    query=query,
                    location={'latitude': 39.2904, 'longitude': -76.6122},
                    max_results=5
                )
                search_time = time.time() - start_time
                alt_results.append(len(results))
                alt_times.append(search_time)
                print(f"   Query: '{query[:30]}...' -> {len(results)} results in {search_time:.2f}s")
            except Exception as e:
                print(f"   Query: '{query[:30]}...' -> FAILED: {e}")
                alt_results.append(0)
                alt_times.append(0)
        
        search_engines.append({
            'name': 'Enhanced Search',
            'total_results': sum(alt_results),
            'avg_time': sum(alt_times) / len(alt_times) if alt_times else 0,
            'success_rate': len([r for r in alt_results if r > 0]) / len(alt_results)
        })
        
    except Exception as e:
        print(f"❌ Enhanced Search test failed: {e}")
    
    # Display Performance Comparison
    print("\n📊 SEARCH ENGINE PERFORMANCE COMPARISON")
    print("-" * 80)
    print(f"{'Engine':<20} {'Total Results':<15} {'Avg Time (s)':<15} {'Success Rate':<15}")
    print("-" * 80)
    
    best_engine = None
    best_score = 0
    
    for engine in search_engines:
        # Calculate composite score (results * success_rate / time)
        if engine['avg_time'] > 0:
            score = (engine['total_results'] * engine['success_rate']) / engine['avg_time']
        else:
            score = 0
        
        if score > best_score:
            best_score = score
            best_engine = engine['name']
        
        print(f"{engine['name']:<20} {engine['total_results']:<15} {engine['avg_time']:<15.2f} {engine['success_rate']:<15.2%}")
    
    if best_engine:
        print(f"\n🏆 Best performing search engine: {best_engine}")
    
    return search_engines

def test_api_integration():
    """Test API integrations"""
    print("\n" + "=" * 80)
    print("🔌 API INTEGRATION TEST")
    print("=" * 80)
    
    test_location = {
        'latitude': 39.2904,
        'longitude': -76.6122,
        'city': 'Baltimore',
        'country': 'US'
    }
    
    api_results = {}
    
    # Test AllEvents.in API
    try:
        print("🎪 Testing Enhanced AllEvents.in API...")
        from services.allevents_service_enhanced import EnhancedAllEventsService
        from config.settings import ALLEVENTS_API_KEY, ALLEVENTS_CONFIG
        
        if ALLEVENTS_API_KEY and ALLEVENTS_API_KEY != '':
            allevents = EnhancedAllEventsService(ALLEVENTS_API_KEY, ALLEVENTS_CONFIG)
            
            start_time = time.time()
            events = allevents.search_events_comprehensive(
                location=test_location,
                user_interests=['technology', 'music'],
                user_activity='networking events',
                max_results=10
            )
            search_time = time.time() - start_time
            
            api_results['AllEvents.in'] = {
                'events_found': len(events),
                'search_time': search_time,
                'status': 'SUCCESS' if events else 'NO_RESULTS'
            }
            
            print(f"   ✅ Found {len(events)} events in {search_time:.2f}s")
            if events:
                print(f"   📝 Sample event: {events[0].title[:50]}...")
        else:
            api_results['AllEvents.in'] = {'status': 'NO_API_KEY'}
            print("   ⚠️ No API key configured")
            
    except Exception as e:
        api_results['AllEvents.in'] = {'status': 'ERROR', 'error': str(e)}
        print(f"   ❌ AllEvents.in test failed: {e}")
    
    # Test NewsAPI
    try:
        print("\n📰 Testing NewsAPI for Event Discovery...")
        from services.newsapi_service import NewsAPIEventService
        from config.settings import NEWSAPI_KEY
        
        if NEWSAPI_KEY and NEWSAPI_KEY != '':
            news_service = NewsAPIEventService(NEWSAPI_KEY)
            
            start_time = time.time()
            news_events = news_service.search_local_events(
                location="Baltimore, MD",
                user_interests=['technology', 'music'],
                user_activity='concerts',
                days_ahead=14
            )
            search_time = time.time() - start_time
            
            api_results['NewsAPI'] = {
                'events_found': len(news_events),
                'search_time': search_time,
                'status': 'SUCCESS' if news_events else 'NO_RESULTS'
            }
            
            print(f"   ✅ Found {len(news_events)} news events in {search_time:.2f}s")
            if news_events:
                print(f"   📝 Sample news: {news_events[0].title[:50]}...")
        else:
            api_results['NewsAPI'] = {'status': 'NO_API_KEY'}
            print("   ⚠️ No API key configured")
            
    except Exception as e:
        api_results['NewsAPI'] = {'status': 'ERROR', 'error': str(e)}
        print(f"   ❌ NewsAPI test failed: {e}")
    
    # Test Ticketmaster
    try:
        print("\n🎫 Testing Ticketmaster API...")
        from services.ticketmaster_service import TicketmasterService
        from config.settings import TICKETMASTER_API_KEY, TICKETMASTER_CONFIG
        
        if TICKETMASTER_API_KEY and TICKETMASTER_API_KEY != '':
            ticketmaster = TicketmasterService(TICKETMASTER_API_KEY, TICKETMASTER_CONFIG)
            
            start_time = time.time()
            tm_events = ticketmaster.search_events_with_ai_ranking(
                location_data=test_location,
                user_interests=['music', 'technology'],
                user_activity='concerts',
                max_results=10
            )
            search_time = time.time() - start_time
            
            api_results['Ticketmaster'] = {
                'events_found': len(tm_events),
                'search_time': search_time,
                'status': 'SUCCESS' if tm_events else 'NO_RESULTS'
            }
            
            print(f"   ✅ Found {len(tm_events)} events in {search_time:.2f}s")
            if tm_events:
                print(f"   📝 Sample event: {tm_events[0].get('name', 'Unknown')[:50]}...")
        else:
            api_results['Ticketmaster'] = {'status': 'NO_API_KEY'}
            print("   ⚠️ No API key configured")
            
    except Exception as e:
        api_results['Ticketmaster'] = {'status': 'ERROR', 'error': str(e)}
        print(f"   ❌ Ticketmaster test failed: {e}")
    
    return api_results

def test_fast_osint_crawling():
    """Test fast minimal OSINT crawling"""
    print("\n" + "=" * 80)
    print("🕷️ FAST OSINT CRAWLING TEST")
    print("=" * 80)
    
    test_profile = {
        'name': 'John Doe',
        'location': 'Baltimore, MD',
        'activity': 'technology meetups',
        'interests': ['programming', 'AI', 'networking']
    }
    
    try:
        from searchmethods.enhanced_background_search import EnhancedBackgroundSearchService
        
        print(f"🔍 Testing fast OSINT crawl for: {test_profile['name']}")
        print(f"📍 Location: {test_profile['location']}")
        print(f"🎯 Activity: {test_profile['activity']}")
        print(f"💡 Interests: {', '.join(test_profile['interests'])}")
        
        # Test with fast mode enabled
        bg_service = EnhancedBackgroundSearchService({'FAST_MODE': True, 'TIMEOUT': 15})
        
        start_time = time.time()
        results = bg_service.perform_enhanced_search(test_profile, timeout=15)
        total_time = time.time() - start_time
        
        print(f"\n⏱️ Total search time: {total_time:.2f} seconds")
        print(f"📊 Search performance:")
        
        metadata = results.get('metadata', {})
        sources_used = metadata.get('sources_used', [])
        total_results = metadata.get('total_results', 0)
        
        print(f"   - Sources used: {len(sources_used)} ({', '.join(sources_used)})")
        print(f"   - Total results: {total_results}")
        print(f"   - Fast mode: {metadata.get('fast_mode', False)}")
        print(f"   - Privacy mode: {metadata.get('privacy_mode', True)}")
        
        # Show results by category
        raw_results = results.get('raw_results', {})
        print(f"\n📈 Results by category:")
        for category, category_results in raw_results.items():
            print(f"   - {category}: {len(category_results)} results")
        
        # Show summaries
        summaries = results.get('summaries', {})
        print(f"\n📝 Search summaries:")
        for category, summary in summaries.items():
            print(f"   - {category}: {summary}")
        
        return {
            'total_time': total_time,
            'sources_used': len(sources_used),
            'total_results': total_results,
            'categories': len(raw_results),
            'status': 'SUCCESS'
        }
        
    except Exception as e:
        print(f"❌ Fast OSINT crawling test failed: {e}")
        return {'status': 'ERROR', 'error': str(e)}

def test_data_filtering_and_correlation():
    """Test data filtering and correlation with user interests"""
    print("\n" + "=" * 80)
    print("🎯 DATA FILTERING & CORRELATION TEST")
    print("=" * 80)
    
    # Test user with specific interests
    test_user = {
        'name': 'Alice Tech',
        'location': 'Washington DC',
        'activity': 'tech conferences',
        'interests': ['artificial intelligence', 'machine learning', 'python programming']
    }
    
    try:
        print(f"👤 Testing correlation for user: {test_user['name']}")
        print(f"🎯 Interests: {', '.join(test_user['interests'])}")
        print(f"🎪 Preferred activity: {test_user['activity']}")
        
        # Test comprehensive search with filtering
        from services.enhanced_search_service import EnhancedSearchService
        
        search_service = EnhancedSearchService()
        
        # Build query from user interests and activity
        query = f"{test_user['activity']} {' '.join(test_user['interests'])}"
        
        start_time = time.time()
        search_results = search_service.search_comprehensive(
            query=query,
            location={'latitude': 38.9072, 'longitude': -77.0369},  # DC coordinates
            user_interests=test_user['interests'],
            max_results=15
        )
        search_time = time.time() - start_time
        
        print(f"\n⏱️ Search completed in {search_time:.2f} seconds")
        print(f"📊 Found {len(search_results)} results")
        
        # Analyze correlation quality
        correlation_scores = []
        interest_keywords = set()
        for interest in test_user['interests']:
            interest_keywords.update(interest.lower().split())
        activity_keywords = set(test_user['activity'].lower().split())
        all_keywords = interest_keywords.union(activity_keywords)
        
        print(f"\n🔍 Analyzing correlation with keywords: {', '.join(all_keywords)}")
        
        for i, result in enumerate(search_results[:5]):  # Analyze top 5 results
            result_text = f"{result.title} {result.content}".lower()
            
            matches = sum(1 for keyword in all_keywords if keyword in result_text)
            correlation_score = matches / len(all_keywords) if all_keywords else 0
            correlation_scores.append(correlation_score)
            
            print(f"   Result {i+1}: {result.title[:50]}...")
            print(f"      Correlation score: {correlation_score:.2f} ({matches}/{len(all_keywords)} keywords)")
            print(f"      Relevance score: {result.relevance_score:.2f}")
            print(f"      Source: {result.source}")
        
        avg_correlation = sum(correlation_scores) / len(correlation_scores) if correlation_scores else 0
        
        print(f"\n📈 Overall correlation analysis:")
        print(f"   - Average correlation score: {avg_correlation:.2f}")
        print(f"   - Correlation quality: {'Excellent' if avg_correlation > 0.7 else 'Good' if avg_correlation > 0.4 else 'Needs improvement'}")
        
        return {
            'search_time': search_time,
            'results_found': len(search_results),
            'avg_correlation': avg_correlation,
            'correlation_quality': 'excellent' if avg_correlation > 0.7 else 'good' if avg_correlation > 0.4 else 'poor',
            'status': 'SUCCESS'
        }
        
    except Exception as e:
        print(f"❌ Data filtering test failed: {e}")
        return {'status': 'ERROR', 'error': str(e)}

def main():
    """Run all optimization tests"""
    print("🚀 WhatNowAI Production Optimization Test Suite")
    print("=" * 80)
    
    test_results = {}
    
    # Test 1: Search Engine Performance
    test_results['search_engines'] = test_search_engine_performance()
    
    # Test 2: API Integration
    test_results['api_integration'] = test_api_integration()
    
    # Test 3: Fast OSINT Crawling
    test_results['osint_crawling'] = test_fast_osint_crawling()
    
    # Test 4: Data Filtering and Correlation
    test_results['data_correlation'] = test_data_filtering_and_correlation()
    
    # Generate Final Report
    print("\n" + "=" * 80)
    print("📋 FINAL OPTIMIZATION REPORT")
    print("=" * 80)
    
    # Search Engine Analysis
    if test_results.get('search_engines'):
        print("\n🔍 Search Engine Optimization:")
        engines = test_results['search_engines']
        if isinstance(engines, list) and engines:
            best_engine = max(engines, key=lambda x: x.get('total_results', 0) * x.get('success_rate', 0))
            print(f"   - Best performing engine: {best_engine['name']}")
            print(f"   - Recommended for production: {best_engine['name']}")
        else:
            print("   - No search engines tested successfully")
    
    # API Integration Analysis
    if test_results.get('api_integration'):
        print("\n🔌 API Integration Status:")
        apis = test_results['api_integration']
        working_apis = [name for name, data in apis.items() if data.get('status') == 'SUCCESS']
        print(f"   - Working APIs: {len(working_apis)}/{len(apis)}")
        if working_apis:
            print(f"   - Active: {', '.join(working_apis)}")
        
        total_events = sum(data.get('events_found', 0) for data in apis.values() if isinstance(data, dict))
        print(f"   - Total events discoverable: {total_events}")
    
    # OSINT Analysis
    if test_results.get('osint_crawling'):
        osint_data = test_results['osint_crawling']
        if osint_data.get('status') == 'SUCCESS':
            print(f"\n🕷️ OSINT Crawling Performance:")
            print(f"   - Search time: {osint_data.get('total_time', 0):.2f}s")
            print(f"   - Sources utilized: {osint_data.get('sources_used', 0)}")
            print(f"   - Data points found: {osint_data.get('total_results', 0)}")
            print(f"   - Categories covered: {osint_data.get('categories', 0)}")
        else:
            print(f"\n🕷️ OSINT Crawling: {osint_data.get('status', 'UNKNOWN')}")
    
    # Correlation Analysis
    if test_results.get('data_correlation'):
        corr_data = test_results['data_correlation']
        if corr_data.get('status') == 'SUCCESS':
            print(f"\n🎯 Data Correlation Quality:")
            print(f"   - Correlation score: {corr_data.get('avg_correlation', 0):.2f}")
            print(f"   - Quality rating: {corr_data.get('correlation_quality', 'unknown').title()}")
            print(f"   - Results relevant to user: {corr_data.get('results_found', 0)}")
        else:
            print(f"\n🎯 Data Correlation: {corr_data.get('status', 'UNKNOWN')}")
    
    # Overall Recommendations
    print("\n🎯 OPTIMIZATION RECOMMENDATIONS:")
    
    # Check if DuckDuckGo is failing
    if test_results.get('search_engines'):
        engines = test_results['search_engines']
        ddg_engine = next((e for e in engines if e.get('name') == 'DuckDuckGo'), None)
        if ddg_engine and ddg_engine.get('success_rate', 0) < 0.5:
            print("   ⚠️ DuckDuckGo showing low success rate - consider implementing fallback search engines")
    
    # Check API coverage
    if test_results.get('api_integration'):
        working_apis = len([data for data in test_results['api_integration'].values() 
                           if data.get('status') == 'SUCCESS'])
        if working_apis < 2:
            print("   ⚠️ Limited API coverage - configure additional event APIs for better results")
    
    # Check OSINT performance
    if test_results.get('osint_crawling', {}).get('total_time', 0) > 20:
        print("   ⚠️ OSINT crawling is slow - consider reducing timeout or optimizing search scope")
    
    # Check correlation quality
    if test_results.get('data_correlation', {}).get('avg_correlation', 0) < 0.4:
        print("   ⚠️ Data correlation needs improvement - enhance keyword matching and filtering")
    
    print("\n✅ Optimization testing completed!")

if __name__ == "__main__":
    main()
