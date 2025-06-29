"""
Enhanced Integration Service
Orchestrates all services for comprehensive user profiling and event discovery
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import os

# Import all our services
from .advanced_profiling_service import AdvancedProfilingService, UserProfile
from .enhanced_web_scraper import EnhancedWebScraper
from .fallback_event_service import FallbackEventService
from .ai_relation_detector import AIRelationDetector
from .dns_resolver import resolve_domain, is_dns_available

# Import existing services with error handling
try:
    from .ticketmaster_service import TicketmasterService
except ImportError:
    TicketmasterService = None
    
try:
    from .allevents_service_enhanced import AllEventsEnhancedService
except ImportError:
    AllEventsEnhancedService = None
    
try:
    from .optimized_osint_service import OptimizedOSINTService
except ImportError:
    OptimizedOSINTService = None

logger = logging.getLogger(__name__)


class EnhancedIntegrationService:
    """
    Master integration service that orchestrates all components
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize integration service with configuration
        
        Args:
            config: Configuration dictionary with API keys and settings
        """
        self.config = config
        
        # Initialize core services
        self.profiling_service = AdvancedProfilingService()
        self.fallback_event_service = FallbackEventService()
        
        # Initialize AI services if API key available
        openai_key = config.get('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY')
        self.ai_detector = AIRelationDetector(openai_key)
        
        # Initialize optional services
        self.ticketmaster_service = None
        if TicketmasterService and config.get('TICKETMASTER_API_KEY'):
            try:
                self.ticketmaster_service = TicketmasterService(
                    config['TICKETMASTER_API_KEY']
                )
            except Exception as e:
                logger.error(f"Failed to initialize Ticketmaster: {e}")
                
        self.allevents_service = None
        if AllEventsEnhancedService and config.get('ALLEVENTS_API_KEY'):
            try:
                self.allevents_service = AllEventsEnhancedService(
                    config['ALLEVENTS_API_KEY']
                )
            except Exception as e:
                logger.error(f"Failed to initialize AllEvents: {e}")
                
        # Log service status
        self._log_service_status()
        
    def _log_service_status(self):
        """Log the status of all services"""
        services = {
            'DNS Resolution': is_dns_available(),
            'Profiling Service': True,
            'AI Relation Detection': self.ai_detector.openai_client is not None,
            'Ticketmaster API': self.ticketmaster_service is not None,
            'AllEvents API': self.allevents_service is not None,
            'Fallback Events': True,
            'Web Scraping': True
        }
        
        logger.info("=== Service Status ===")
        for service, status in services.items():
            logger.info(f"{service}: {'✓ Active' if status else '✗ Inactive'}")
        logger.info("====================")
        
    async def process_user_request(self, 
                                 user_data: Dict[str, Any],
                                 location_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a user request with full profiling and event discovery
        
        Args:
            user_data: User information (name, activity request)
            location_data: Location information
            
        Returns:
            Complete response with profile and events
        """
        try:
            start_time = datetime.now()
            
            # Step 1: Web scraping for user data
            logger.info(f"Starting comprehensive search for {user_data.get('first_name')} {user_data.get('last_name')}")
            
            search_results = await self._perform_web_search(user_data, location_data)
            
            # Step 2: Create enhanced profile
            user_profile = self.profiling_service.create_enhanced_profile(
                user_data,
                search_results,
                location_data
            )
            
            # Step 3: Enhance profile with AI
            if self.ai_detector:
                enhanced_profile_dict = self.ai_detector.enhance_user_profile(
                    self.profiling_service.export_profile(user_profile),
                    search_results
                )
                # Update the profile object
                for key, value in enhanced_profile_dict.items():
                    if hasattr(user_profile, key):
                        setattr(user_profile, key, value)
            
            # Step 4: Discover events
            events = await self._discover_events(user_profile, location_data)
            
            # Step 5: Generate recommendations
            recommendations = self._generate_recommendations(user_profile, events)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'success': True,
                'user_profile': self.profiling_service.export_profile(user_profile),
                'events': events,
                'recommendations': recommendations,
                'search_results_count': len(search_results),
                'processing_time': processing_time,
                'services_used': self._get_services_used()
            }
            
        except Exception as e:
            logger.error(f"Error in user request processing: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_events': self._get_fallback_events(location_data)
            }
            
    async def _perform_web_search(self, 
                                user_data: Dict[str, Any],
                                location_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform comprehensive web search for user data"""
        results = []
        
        try:
            async with EnhancedWebScraper() as scraper:
                # Search for the person
                search_results = await scraper.search_person_comprehensive(
                    user_data.get('first_name', ''),
                    user_data.get('last_name', ''),
                    location_data
                )
                
                results.extend(search_results)
                
                # If we have an activity request, search for that too
                if user_data.get('activity'):
                    activity = user_data['activity']
                    activity_results = await scraper._search_google(
                        f"{activity} {location_data.get('city', '')}"
                    )
                    results.extend(activity_results[:5])
                    
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            
        # Try OSINT service if available
        if OptimizedOSINTService:
            try:
                osint_service = OptimizedOSINTService()
                osint_results = osint_service.search_person(
                    f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}"
                )
                results.extend(osint_results)
            except Exception as e:
                logger.error(f"OSINT search failed: {e}")
                
        return results
        
    async def _discover_events(self, 
                             user_profile: UserProfile,
                             location_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Discover events using all available services"""
        all_events = []
        
        lat = location_data.get('latitude')
        lon = location_data.get('longitude')
        
        if not lat or not lon:
            logger.error("No location coordinates available")
            return []
            
        # Prepare user interests for searching
        user_interests = user_profile.interests[:10]  # Top 10 interests
        
        # Try primary event services
        if self.ticketmaster_service:
            try:
                tm_events = await self._get_ticketmaster_events(
                    lat, lon, user_interests, user_profile
                )
                all_events.extend(tm_events)
            except Exception as e:
                logger.error(f"Ticketmaster search failed: {e}")
                
        if self.allevents_service:
            try:
                ae_events = self.allevents_service.search_events_comprehensive(
                    lat, lon, user_interests=user_interests
                )
                all_events.extend(ae_events)
            except Exception as e:
                logger.error(f"AllEvents search failed: {e}")
                
        # Always use fallback service for additional events
        try:
            fallback_events = self.fallback_event_service.search_events(
                lat, lon, user_interests=user_interests
            )
            all_events.extend(fallback_events)
        except Exception as e:
            logger.error(f"Fallback event search failed: {e}")
            
        # Score and rank events using AI
        if self.ai_detector and all_events:
            profile_dict = self.profiling_service.export_profile(user_profile)
            for event in all_events:
                event['ai_relevance_score'] = self.ai_detector.score_event_relevance(
                    event, profile_dict
                )
                
            # Sort by AI relevance score
            all_events.sort(key=lambda x: x.get('ai_relevance_score', 0), reverse=True)
            
        # Deduplicate and return top events
        unique_events = self._deduplicate_events(all_events)
        return unique_events[:50]  # Return top 50 events
        
    async def _get_ticketmaster_events(self, 
                                     lat: float, 
                                     lon: float,
                                     interests: List[str],
                                     profile: UserProfile) -> List[Dict[str, Any]]:
        """Get events from Ticketmaster with personalization"""
        # This would call the actual Ticketmaster service
        # For now, return empty list if service not available
        if not self.ticketmaster_service:
            return []
            
        # Convert profile to format expected by Ticketmaster
        personalization_data = {
            'interests': profile.interests,
            'preferences': profile.preferences,
            'personality_traits': profile.personality_traits
        }
        
        return self.ticketmaster_service.search_events_personalized(
            lat, lon, 
            user_interests=interests,
            personalization_data=personalization_data
        )
        
    def _generate_recommendations(self, 
                                profile: UserProfile,
                                events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate personalized recommendations"""
        recommendations = []
        
        # Get AI-generated recommendations if available
        if self.fallback_event_service:
            profile_dict = self.profiling_service.export_profile(profile)
            ai_recommendations = self.fallback_event_service.generate_recommendations(
                profile_dict,
                {'city': profile.location.get('city', 'Your area')}
            )
            recommendations.extend(ai_recommendations)
            
        # Add interest-based recommendations
        interest_connections = self.ai_detector.generate_interest_connections(
            profile.interests[:10]
        )
        
        for interest, related in interest_connections.items():
            if related:
                recommendations.append({
                    'type': 'interest_expansion',
                    'title': f"Explore {related[0]} based on your interest in {interest}",
                    'related_interests': related[:3],
                    'confidence': 0.7
                })
                
        return recommendations[:10]
        
    def _deduplicate_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate events"""
        seen = set()
        unique_events = []
        
        for event in events:
            # Create a unique key
            key = f"{event.get('name', '').lower()[:30]}_{event.get('date', '')[:10]}"
            
            if key not in seen:
                seen.add(key)
                unique_events.append(event)
                
        return unique_events
        
    def _get_fallback_events(self, location_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get basic fallback events when main processing fails"""
        try:
            return self.fallback_event_service.search_events(
                location_data.get('latitude', 0),
                location_data.get('longitude', 0)
            )[:10]
        except:
            return []
            
    def _get_services_used(self) -> List[str]:
        """Get list of services that were used"""
        services = ['profiling', 'web_scraping', 'fallback_events']
        
        if self.ai_detector and self.ai_detector.openai_client:
            services.append('ai_enhancement')
        if self.ticketmaster_service:
            services.append('ticketmaster')
        if self.allevents_service:
            services.append('allevents')
        if is_dns_available():
            services.append('dns_resolution')
            
        return services