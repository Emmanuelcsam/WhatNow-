#!/usr/bin/env python3
"""
Simplified Production Test - Focus on Core Optimizations
Tests the essential optimizations without problematic external APIs
"""

import sys
import time
import json
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_enhanced_background_search():
    """Test the enhanced background search with production optimizations"""
    print("=" * 80)
    print("🔍 ENHANCED BACKGROUND SEARCH TEST")
    print("=" * 80)
    
    test_profile = {
        'name': 'John Developer',
        'location': 'Baltimore, MD',
        'activity': 'technology meetups',
        'interests': ['programming', 'AI', 'networking'],
        'social_handles': {
            'github': 'johndoe',
            'linkedin': 'john-developer',
            'twitter': 'johndev'
        }
    }
    
    try:
        from searchmethods.enhanced_background_search import EnhancedBackgroundSearchService
        
        print(f"👤 Testing enhanced search for: {test_profile['name']}")
        print(f"📍 Location: {test_profile['location']}")
        print(f"🎯 Activity: {test_profile['activity']}")
        print(f"💡 Interests: {', '.join(test_profile['interests'])}")
        
        # Test with fast mode and production optimizations
        config = {
            'FAST_MODE': True,
            'TIMEOUT': 10,
            'PRIVACY_MODE': True,
            'ENABLE_DEEP_SEARCH': True,
            'ENABLE_SOCIAL_SEARCH': True
        }
        
        bg_service = EnhancedBackgroundSearchService(config)
        
        start_time = time.time()
        results = bg_service.perform_enhanced_search(test_profile, timeout=10)
        total_time = time.time() - start_time
        
        print(f"\n⏱️ Total search time: {total_time:.2f} seconds")
        
        metadata = results.get('metadata', {})
        sources_used = metadata.get('sources_used', [])
        total_results = metadata.get('total_results', 0)
        
        print(f"📊 Performance metrics:")
        print(f"   - Sources utilized: {len(sources_used)} ({', '.join(sources_used)})")
        print(f"   - Total data points: {total_results}")
        print(f"   - Fast mode enabled: {metadata.get('fast_mode', False)}")
        print(f"   - Privacy protection: {metadata.get('privacy_mode', True)}")
        print(f"   - Search efficiency: {total_results/total_time:.1f} results/second")
        
        # Show results by category
        raw_results = results.get('raw_results', {})
        print(f"\n📈 Results breakdown:")
        for category, category_results in raw_results.items():
            print(f"   - {category.title()}: {len(category_results)} results")
            
            # Show sample results
            if category_results:
                sample_result = category_results[0]
                print(f"     Sample: {sample_result.title[:60]}...")
        
        # Show summaries
        summaries = results.get('summaries', {})
        print(f"\n📝 Intelligence summaries:")
        for category, summary in summaries.items():
            print(f"   - {category.title()}: {summary}")
        
        # Test performance requirements
        performance_score = 'EXCELLENT'
        if total_time > 15:
            performance_score = 'POOR'
        elif total_time > 10:
            performance_score = 'FAIR'
        elif total_time > 5:
            performance_score = 'GOOD'
        
        print(f"\n🎯 Performance assessment: {performance_score}")
        print(f"   - Speed: {'✅' if total_time <= 10 else '⚠️'} {'Fast' if total_time <= 10 else 'Slow'}")
        print(f"   - Coverage: {'✅' if len(sources_used) >= 3 else '⚠️'} {'Good' if len(sources_used) >= 3 else 'Limited'}")
        print(f"   - Results: {'✅' if total_results >= 5 else '⚠️'} {'Sufficient' if total_results >= 5 else 'Limited'}")
        
        return {
            'status': 'SUCCESS',
            'total_time': total_time,
            'sources_used': len(sources_used),
            'total_results': total_results,
            'performance_score': performance_score
        }
        
    except Exception as e:
        print(f"❌ Enhanced background search test failed: {e}")
        return {'status': 'ERROR', 'error': str(e)}

def test_osint_optimization():
    """Test OSINT optimization and fallback mechanisms"""
    print("\n" + "=" * 80)
    print("🛡️ OSINT OPTIMIZATION TEST")
    print("=" * 80)
    
    try:
        from services.osint_integration import OSINTIntegrator
        
        print("🔧 Testing OSINT tool availability...")
        
        integrator = OSINTIntegrator()
        
        # Check available tools
        print(f"✅ OSINT Integrator initialized successfully")
        print(f"   - OSINT Engine available: {integrator.osint_engine is not None}")
        print(f"   - OSINT Utils available: {integrator.osint_utils is not None}")
        
        # Test a quick search with timeout
        print(f"\n🔍 Testing fast OSINT search (5s timeout)...")
        
        start_time = time.time()
        results = integrator.search_person_osint(
            first_name="John",
            last_name="Doe",
            location="Baltimore, MD",
            timeout=5  # Fast timeout for production
        )
        search_time = time.time() - start_time
        
        total_osint_results = sum(len(category_results) for category_results in results.values())
        
        print(f"⏱️ OSINT search completed in {search_time:.2f}s")
        print(f"📊 OSINT results:")
        for category, category_results in results.items():
            print(f"   - {category}: {len(category_results)} results")
        
        print(f"🎯 OSINT performance:")
        print(f"   - Speed: {'✅' if search_time <= 5 else '⚠️'} {'Fast' if search_time <= 5 else 'Slow'}")
        print(f"   - Results: {'✅' if total_osint_results > 0 else '⚠️'} {'Found data' if total_osint_results > 0 else 'No results'}")
        
        return {
            'status': 'SUCCESS',
            'search_time': search_time,
            'total_results': total_osint_results,
            'categories': len(results)
        }
        
    except Exception as e:
        print(f"❌ OSINT optimization test failed: {e}")
        return {'status': 'ERROR', 'error': str(e)}

def test_search_engine_fallbacks():
    """Test search engine fallback mechanisms"""
    print("\n" + "=" * 80)
    print("🔄 SEARCH ENGINE FALLBACK TEST")
    print("=" * 80)
    
    try:
        from services.enhanced_search_service import EnhancedSearchService
        
        search_service = EnhancedSearchService()
        
        test_queries = [
            "tech events Baltimore",
            "music concerts Maryland",
            "networking meetups DC"
        ]
        
        print("🔍 Testing search engine fallback mechanisms...")
        
        total_results = 0
        total_time = 0
        successful_queries = 0
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n🔎 Query {i}: '{query}'")
            
            start_time = time.time()
            try:
                results = search_service.search_comprehensive(
                    query=query,
                    location={'latitude': 39.2904, 'longitude': -76.6122},
                    max_results=5
                )
                query_time = time.time() - start_time
                
                print(f"   ✅ Found {len(results)} results in {query_time:.2f}s")
                
                if results:
                    sample_result = results[0]
                    print(f"   📝 Sample: {sample_result.title[:50]}...")
                    print(f"   🌐 Source: {sample_result.source}")
                
                total_results += len(results)
                total_time += query_time
                if len(results) > 0:
                    successful_queries += 1
                
            except Exception as e:
                query_time = time.time() - start_time
                print(f"   ❌ Query failed: {e}")
                total_time += query_time
        
        success_rate = successful_queries / len(test_queries) if test_queries else 0
        avg_time = total_time / len(test_queries) if test_queries else 0
        
        print(f"\n📊 Search engine performance:")
        print(f"   - Success rate: {success_rate:.1%} ({successful_queries}/{len(test_queries)} queries)")
        print(f"   - Average time: {avg_time:.2f}s per query")
        print(f"   - Total results: {total_results}")
        print(f"   - Results per query: {total_results/len(test_queries):.1f}")
        
        performance_rating = 'EXCELLENT' if success_rate >= 0.8 else 'GOOD' if success_rate >= 0.5 else 'POOR'
        
        print(f"🎯 Fallback system rating: {performance_rating}")
        
        return {
            'status': 'SUCCESS',
            'success_rate': success_rate,
            'avg_time': avg_time,
            'total_results': total_results,
            'performance_rating': performance_rating
        }
        
    except Exception as e:
        print(f"❌ Search engine fallback test failed: {e}")
        return {'status': 'ERROR', 'error': str(e)}

def test_data_filtering_accuracy():
    """Test data filtering and interest correlation"""
    print("\n" + "=" * 80)
    print("🎯 DATA FILTERING ACCURACY TEST")
    print("=" * 80)
    
    # Test specific user interests
    test_cases = [
        {
            'name': 'Tech Professional',
            'interests': ['python', 'machine learning', 'software development'],
            'activity': 'programming meetups',
            'expected_keywords': ['python', 'programming', 'software', 'tech', 'development', 'ml', 'ai']
        },
        {
            'name': 'Music Enthusiast',
            'interests': ['jazz', 'live music', 'concerts'],
            'activity': 'music events',
            'expected_keywords': ['jazz', 'music', 'concert', 'live', 'performance', 'band']
        }
    ]
    
    try:
        from services.enhanced_search_service import EnhancedSearchService
        
        search_service = EnhancedSearchService()
        
        correlation_scores = []
        
        for test_case in test_cases:
            print(f"\n👤 Testing: {test_case['name']}")
            print(f"🎯 Interests: {', '.join(test_case['interests'])}")
            print(f"🎪 Activity: {test_case['activity']}")
            
            # Build search query
            query = f"{test_case['activity']} {' '.join(test_case['interests'])}"
            
            start_time = time.time()
            results = search_service.search_comprehensive(
                query=query,
                user_interests=test_case['interests'],
                max_results=10
            )
            search_time = time.time() - start_time
            
            print(f"   ⏱️ Search time: {search_time:.2f}s")
            print(f"   📊 Results found: {len(results)}")
            
            # Analyze correlation
            if results:
                expected_keywords = set(test_case['expected_keywords'])
                matches_found = []
                
                for result in results[:3]:  # Check top 3 results
                    result_text = f"{result.title} {result.content}".lower()
                    matches = [kw for kw in expected_keywords if kw in result_text]
                    matches_found.extend(matches)
                    
                    print(f"   📝 Result: {result.title[:40]}...")
                    print(f"      Matches: {', '.join(matches) if matches else 'None'}")
                
                # Calculate correlation score
                unique_matches = set(matches_found)
                correlation_score = len(unique_matches) / len(expected_keywords)
                correlation_scores.append(correlation_score)
                
                print(f"   🎯 Correlation score: {correlation_score:.2f} ({len(unique_matches)}/{len(expected_keywords)} keywords)")
            else:
                print(f"   ⚠️ No results found")
                correlation_scores.append(0)
        
        # Overall correlation analysis
        avg_correlation = sum(correlation_scores) / len(correlation_scores) if correlation_scores else 0
        
        print(f"\n📈 Overall filtering accuracy:")
        print(f"   - Average correlation: {avg_correlation:.2f}")
        print(f"   - Accuracy rating: {'Excellent' if avg_correlation >= 0.7 else 'Good' if avg_correlation >= 0.4 else 'Needs improvement'}")
        
        return {
            'status': 'SUCCESS',
            'avg_correlation': avg_correlation,
            'test_cases': len(test_cases),
            'accuracy_rating': 'excellent' if avg_correlation >= 0.7 else 'good' if avg_correlation >= 0.4 else 'poor'
        }
        
    except Exception as e:
        print(f"❌ Data filtering test failed: {e}")
        return {'status': 'ERROR', 'error': str(e)}

def main():
    """Run simplified production optimization tests"""
    print("🚀 WhatNowAI Production Optimization - Core Tests")
    print("=" * 80)
    
    test_results = {}
    
    # Test 1: Enhanced Background Search
    test_results['background_search'] = test_enhanced_background_search()
    
    # Test 2: OSINT Optimization
    test_results['osint_optimization'] = test_osint_optimization()
    
    # Test 3: Search Engine Fallbacks
    test_results['search_fallbacks'] = test_search_engine_fallbacks()
    
    # Test 4: Data Filtering Accuracy
    test_results['data_filtering'] = test_data_filtering_accuracy()
    
    # Generate summary report
    print("\n" + "=" * 80)
    print("📋 PRODUCTION OPTIMIZATION SUMMARY")
    print("=" * 80)
    
    total_tests = len(test_results)
    successful_tests = sum(1 for result in test_results.values() if result.get('status') == 'SUCCESS')
    
    print(f"\n🎯 Test Results: {successful_tests}/{total_tests} passed")
    
    for test_name, result in test_results.items():
        status_icon = "✅" if result.get('status') == 'SUCCESS' else "❌"
        print(f"   {status_icon} {test_name.replace('_', ' ').title()}")
    
    # Performance summary
    if test_results.get('background_search', {}).get('status') == 'SUCCESS':
        bg_result = test_results['background_search']
        print(f"\n⚡ Performance Highlights:")
        print(f"   - Background search: {bg_result.get('total_time', 0):.2f}s")
        print(f"   - Data sources: {bg_result.get('sources_used', 0)}")
        print(f"   - Results found: {bg_result.get('total_results', 0)}")
    
    if test_results.get('data_filtering', {}).get('status') == 'SUCCESS':
        filter_result = test_results['data_filtering']
        print(f"   - Filtering accuracy: {filter_result.get('avg_correlation', 0):.2f}")
    
    # Recommendations
    print(f"\n🎯 Optimization Status:")
    
    if successful_tests >= total_tests * 0.8:
        print("   🎉 System is well-optimized for production use!")
    elif successful_tests >= total_tests * 0.6:
        print("   ⚠️ System is functional but needs some optimization")
    else:
        print("   🚨 System needs significant optimization before production")
    
    # Specific recommendations
    bg_time = test_results.get('background_search', {}).get('total_time', 0)
    if bg_time > 10:
        print("   💡 Consider reducing search timeout for faster response")
    
    search_success = test_results.get('search_fallbacks', {}).get('success_rate', 0)
    if search_success < 0.7:
        print("   💡 Consider implementing additional search engine fallbacks")
    
    filter_accuracy = test_results.get('data_filtering', {}).get('avg_correlation', 0)
    if filter_accuracy < 0.5:
        print("   💡 Improve keyword matching and result filtering algorithms")
    
    print("\n✅ Core optimization testing completed!")

if __name__ == "__main__":
    main()
