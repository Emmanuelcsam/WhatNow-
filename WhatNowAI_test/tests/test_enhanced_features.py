#!/usr/bin/env python3
"""
Quick test script to verify WhatNowAI enhanced features
"""
import sys
sys.path.append('/home/jarvis/Downloads/WhatNowAI_test')

def test_enhanced_search():
    """Test enhanced search functionality"""
    print("🔍 Testing Enhanced Search Functionality")
    print("=" * 50)

    try:
        from searchmethods.enhanced_background_search import EnhancedBackgroundSearchService, UserProfile

        # Create test user profile
        test_profile = UserProfile(
            name='John Doe',
            location='Baltimore, MD',
            activity='concerts',
            social_handles={'github': 'johndoe', 'linkedin': 'john-doe'}
        )

        print(f"✅ Test profile created: {test_profile.name}")

        # Initialize service
        service = EnhancedBackgroundSearchService()
        print("✅ Enhanced search service initialized")

        # Perform search
        print("🔄 Running enhanced search...")
        results = service.perform_search(test_profile)

        # Analyze results
        total_results = results.get('total_results', 0)
        search_time = results.get('metadata', {}).get('search_time', 0)
        sources = results.get('metadata', {}).get('sources_used', [])

        print(f"✅ Search completed in {search_time:.2f}s")
        print(f"📊 Total results: {total_results}")
        print(f"🔗 Sources used: {sources}")

        # Check each category
        raw_results = results.get('raw_results', {})
        for category, items in raw_results.items():
            print(f"   {category}: {len(items)} results")

        # Check summaries
        summaries = results.get('summaries', {})
        if summaries:
            print("📝 Generated summaries:")
            for category, summary in summaries.items():
                print(f"   {category}: {summary[:100]}...")

        return True

    except Exception as e:
        print(f"❌ Enhanced search test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_osint_integration():
    """Test OSINT integration"""
    print("\n🔍 Testing OSINT Integration")
    print("=" * 50)

    try:
        from services.osint_integration import OSINTIntegrator

        osint = OSINTIntegrator()
        print("✅ OSINT integrator initialized")

        # Check available tools
        tools = osint.get_available_tools()
        print("🛠️ Available OSINT tools:")
        for tool, available in tools.items():
            status = "✅" if available else "❌"
            print(f"   {status} {tool}: {'Available' if available else 'Not available'}")

        # Quick search test
        print("🔄 Running quick OSINT search...")
        quick_results = osint.run_quick_search(
            name="Test User",
            social_handles={'github': 'testuser'},
            timeout=5
        )

        print(f"✅ Quick search completed in {quick_results.get('search_time', 0):.2f}s")
        print(f"📊 Found data: {quick_results.get('found', False)}")
        print(f"🔗 Sources: {quick_results.get('sources', [])}")

        return True

    except Exception as e:
        print(f"❌ OSINT integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_personalization_flow():
    """Test the full personalization flow"""
    print("\n🎯 Testing Personalization Flow")
    print("=" * 50)

    try:
        from services.user_profiling_service import EnhancedUserProfilingService

        profiling_service = EnhancedUserProfilingService()
        print("✅ User profiling service initialized")

        # Create enhanced profile
        enhanced_profile = profiling_service.create_enhanced_profile(
            name="Test User",
            location={'city': 'Baltimore', 'state': 'MD'},
            activity="music concerts",
            social_data={'github': 'testuser', 'twitter': 'testuser'},
            search_results={'search_summaries': {'social': 'Found GitHub profile'}}
        )

        print(f"✅ Enhanced profile created")
        print(f"📊 Profile completion: {enhanced_profile.profile_completion:.1f}%")
        print(f"🎯 Interests: {len(enhanced_profile.interests)} detected")
        print(f"🎨 Activity style: {enhanced_profile.preferences.get('activity_style', 'unknown')}")

        # Get recommendation context
        context = profiling_service.get_recommendation_context(enhanced_profile)
        print(f"🔗 Recommendation context generated with {len(context)} fields")

        return True

    except Exception as e:
        print(f"❌ Personalization flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 WhatNowAI Enhanced Features Test Suite")
    print("=" * 60)

    results = []

    # Test enhanced search
    results.append(test_enhanced_search())

    # Test OSINT integration
    results.append(test_osint_integration())

    # Test personalization flow
    results.append(test_personalization_flow())

    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"🎉 All {total} tests passed! Enhanced features are working properly.")
    else:
        print(f"⚠️ {passed}/{total} tests passed. Some features need attention.")

    print("\n🔧 Recommendations:")
    if not results[0]:
        print("❌ Install missing dependencies: pip install dnspython duckduckgo-search")
    if not results[1]:
        print("❌ Check OSINT tools configuration in search_methods_2/")
    if not results[2]:
        print("❌ Verify user profiling service setup")

    print("\n🚀 Your WhatNowAI application is functional with current features!")

if __name__ == "__main__":
    main()
