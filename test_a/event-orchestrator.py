"""
event_orchestrator.py - Main orchestrator that coordinates all services
"""
import asyncio
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime
import traceback

from scraper_orchestrator import ScraperOrchestrator, SearchQuery
from data_processor import DataProcessor
from ai_integration import AIIntegration
from eventbrite_service import EventBriteService
from cache_service import CacheService

logger = logging.getLogger(__name__)

class EventOrchestrator:
    """Main orchestrator that coordinates the entire event discovery process"""
    
    def __init__(self, config, cache_service: CacheService):
        self.config = config
        self.cache_service = cache_service
        
        # Initialize all services
        self.scraper = ScraperOrchestrator(config)
        self.data_processor = DataProcessor(config)
        self.ai_integration = AIIntegration(config)
        self.eventbrite_service = EventBriteService(config)
        
        # Processing state
        self.processing_tasks = {}
    
    async def process_search_async(self, search_query: Dict, session_id: str):
        """
        Asynchronously process search request
        
        Args:
            search_query: User search parameters
            session_id: Session ID for status updates
        """
        start_time = time.time()
        
        try:
            # Update status
            await self._update_status(session_id, 'starting', 0, 'Starting search process...')
            
            # Step 1: Create search query object
            query = SearchQuery(
                first_name=search_query['first_name'],
                last_name=search_query['last_name'],
                activity=search_query['activity'],
                location=f"{search_query['location']['city']}, {search_query['location']['region']}"
            )
            
            # Step 2: Web scraping (30% of progress)
            await self._update_status(session_id, 'scraping', 10, 
                                    f'Searching for information about {query.full_name}...')
            
            scraper_results = await self.scraper.search(
                query, 
                timeout=self.config.scraper.max_search_time
            )
            
            if not scraper_results:
                await self._update_status(session_id, 'error', 30, 
                                        'No information found. Please try different search terms.')
                return
            
            # Log scraping summary
            scraper_summary = self.scraper.get_summary()
            logger.info(f"Scraping complete: {scraper_summary}")
            
            await self._update_status(session_id, 'processing', 30, 
                                    f'Found {len(scraper_results)} sources. Processing data...')
            
            # Step 3: Data processing and interest extraction (40% of progress)
            processed_data = self.data_processor.process_scraper_results(
                scraper_results,
                search_query
            )
            
            await self._update_status(session_id, 'processing', 50, 
                                    f'Extracted {len(processed_data.interests)} potential interests...')
            
            # Step 4: AI enhancement (optional, 10% of progress)
            if self.config.ai.enable_ai and self.ai_integration.is_available():
                await self._update_status(session_id, 'ai_processing', 60, 
                                        'Enhancing results with AI...')
                
                try:
                    # Enhance interests
                    enhanced_interests = self.ai_integration.enhance_interests(
                        [{'keyword': i.keyword, 'category': i.category} 
                         for i in processed_data.interests],
                        context=processed_data.raw_text_summary
                    )
                    
                    # Generate relational insights
                    facts = []
                    for indicator in processed_data.activity_indicators[:10]:
                        if isinstance(indicator, dict):
                            facts.append(indicator.get('indicator', ''))
                    
                    relational_insights = self.ai_integration.generate_relational_insights(facts)
                    
                    # Add AI-derived interests
                    for insight in relational_insights:
                        processed_data.interests.append({
                            'keyword': insight.derived_interest,
                            'category': insight.category,
                            'confidence': insight.confidence,
                            'source': 'ai_derived'
                        })
                    
                except Exception as e:
                    logger.error(f"AI enhancement error: {e}")
                    # Continue without AI enhancement
            
            await self._update_status(session_id, 'event_search', 70, 
                                    'Searching for relevant events...')
            
            # Step 5: Get interest keywords for event search
            keywords = self.data_processor.get_interest_keywords(processed_data)
            
            if not keywords:
                # Fallback to activity-based keywords
                keywords = search_query['activity'].split()[:5]
            
            logger.info(f"Searching events with keywords: {keywords}")
            
            # Step 6: Search EventBrite (20% of progress)
            events = self.eventbrite_service.search_events(
                keywords=keywords,
                location_data=search_query['location'],
                interests=[{'keyword': i.keyword, 'category': i.category, 
                           'confidence': i.confidence} 
                          for i in processed_data.interests]
            )
            
            await self._update_status(session_id, 'finalizing', 90, 
                                    f'Found {len(events)} relevant events. Finalizing results...')
            
            # Step 7: Format events for display
            formatted_events = self.eventbrite_service.format_events_for_display(events)
            
            # Step 8: Cache results
            cache_key = f"{search_query['first_name']}_{search_query['last_name']}_{search_query['activity'][:20]}"
            self.cache_service.cache_events(cache_key, formatted_events)
            
            # Update session with results
            session_data = {
                'events': formatted_events,
                'processed_data': {
                    'interests': [
                        {
                            'keyword': i.keyword,
                            'category': i.category,
                            'confidence': i.confidence,
                            'sources': i.sources
                        } for i in processed_data.interests[:10]
                    ],
                    'entities': processed_data.entities,
                    'topics': processed_data.topics[:5],
                    'sentiment': processed_data.sentiment_summary,
                    'key_phrases': processed_data.key_phrases[:10]
                },
                'search_summary': {
                    'total_sources': len(scraper_results),
                    'total_interests': len(processed_data.interests),
                    'total_events': len(events),
                    'processing_time': round(time.time() - start_time, 2),
                    'ai_enhanced': self.config.ai.enable_ai and self.ai_integration.is_available()
                },
                'step': 'complete'
            }
            
            self.cache_service.set(f"session:{session_id}", session_data, ttl=3600)
            
            # Final status update
            await self._update_status(session_id, 'complete', 100, 
                                    f'Search complete! Found {len(events)} events matching your interests.',
                                    complete=True)
            
            logger.info(f"Search completed for session {session_id} in {time.time() - start_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Processing error for session {session_id}: {e}")
            logger.error(traceback.format_exc())
            
            await self._update_status(session_id, 'error', 0, 
                                    f'An error occurred: {str(e)}', 
                                    error=str(e))
    
    async def _update_status(self, session_id: str, status: str, progress: int, 
                           message: str, complete: bool = False, error: str = None):
        """Update processing status in session"""
        try:
            status_data = {
                'status': status,
                'progress': progress,
                'message': message,
                'complete': complete,
                'error': error,
                'updated_at': datetime.now().isoformat()
            }
            
            # Update session
            session_data = self.cache_service.get(f"session:{session_id}") or {}
            session_data['processing_status'] = status_data
            self.cache_service.set(f"session:{session_id}", session_data, ttl=3600)
            
            logger.debug(f"Status update for {session_id}: {status} - {progress}% - {message}")
            
        except Exception as e:
            logger.error(f"Failed to update status: {e}")
    
    def process_search_sync(self, search_query: Dict) -> Dict:
        """
        Synchronous version of search processing
        
        Args:
            search_query: User search parameters
            
        Returns:
            Dictionary with events and processed data
        """
        try:
            # Create search query
            query = SearchQuery(
                first_name=search_query['first_name'],
                last_name=search_query['last_name'],
                activity=search_query['activity'],
                location=f"{search_query['location']['city']}, {search_query['location']['region']}"
            )
            
            # Run scraping
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            scraper_results = loop.run_until_complete(
                self.scraper.search(query, timeout=30)
            )
            
            if not scraper_results:
                return {'events': [], 'error': 'No information found'}
            
            # Process data
            processed_data = self.data_processor.process_scraper_results(
                scraper_results,
                search_query
            )
            
            # Get keywords
            keywords = self.data_processor.get_interest_keywords(processed_data)
            
            # Search events
            events = self.eventbrite_service.search_events(
                keywords=keywords,
                location_data=search_query['location'],
                interests=[{'keyword': i.keyword, 'category': i.category, 
                           'confidence': i.confidence} 
                          for i in processed_data.interests]
            )
            
            # Format results
            return {
                'events': self.eventbrite_service.format_events_for_display(events),
                'processed_data': {
                    'interests': processed_data.interests[:10],
                    'entities': processed_data.entities,
                    'topics': processed_data.topics[:5]
                },
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Sync processing error: {e}")
            return {'events': [], 'error': str(e), 'success': False}
    
    def get_sample_events(self, location_data: Dict) -> List[Dict]:
        """Get sample events for testing without full search"""
        try:
            # Use generic keywords
            keywords = ['music', 'food', 'community', 'arts', 'sports']
            
            events = self.eventbrite_service.search_events(
                keywords=keywords,
                location_data=location_data,
                interests=[],
                radius_miles=25,
                time_window_hours=24
            )
            
            return self.eventbrite_service.format_events_for_display(events)
            
        except Exception as e:
            logger.error(f"Sample events error: {e}")
            return []
    
    def validate_search_input(self, search_query: Dict) -> Tuple[bool, Optional[str]]:
        """Validate search input"""
        # Check required fields
        required = ['first_name', 'last_name', 'activity', 'location']
        for field in required:
            if field not in search_query or not search_query[field]:
                return False, f"Missing required field: {field}"
        
        # Validate name length
        if len(search_query['first_name']) < 2 or len(search_query['last_name']) < 2:
            return False, "Names must be at least 2 characters long"
        
        # Validate activity length
        if len(search_query['activity']) < 10:
            return False, "Activity description must be at least 10 characters long"
        
        # Validate location data
        location = search_query['location']
        if not isinstance(location, dict):
            return False, "Invalid location data"
        
        if 'latitude' not in location or 'longitude' not in location:
            return False, "Location coordinates missing"
        
        return True, None
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old session data"""
        try:
            # This would be implemented with proper session management
            cleaned = self.cache_service.cleanup_expired()
            logger.info(f"Cleaned up {cleaned} expired cache entries")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
