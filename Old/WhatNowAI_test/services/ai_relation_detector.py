"""
AI-Powered Relation Detection Service
Uses AI to detect relationships between data points and infer user interests
"""
import logging
import json
import re
from typing import List, Dict, Any, Set, Tuple
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

# Try to import OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available, using fallback methods")


class AIRelationDetector:
    """
    AI-powered service for detecting relationships in data and inferring interests
    """
    
    def __init__(self, openai_api_key: str = None):
        self.openai_client = None
        if OPENAI_AVAILABLE and openai_api_key:
            try:
                self.openai_client = OpenAI(api_key=openai_api_key)
                logger.info("OpenAI client initialized for relation detection")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                
        # Fallback relation mappings
        self.relation_map = self._load_relation_mappings()
        self.interest_inference_rules = self._load_inference_rules()
        
    def _load_relation_mappings(self) -> Dict[str, List[str]]:
        """Load predefined relation mappings"""
        return {
            # Pet ownership to interests
            'dog': ['animals', 'pets', 'outdoors', 'walking', 'parks', 'dog parks', 'pet care'],
            'cat': ['animals', 'pets', 'indoor activities', 'pet care'],
            'pet': ['animals', 'veterinary', 'pet stores', 'animal welfare'],
            
            # Sports to related interests
            'football': ['sports', 'team sports', 'athletics', 'fitness', 'sports bars', 'game watching'],
            'basketball': ['sports', 'team sports', 'athletics', 'fitness', 'indoor sports'],
            'tennis': ['sports', 'individual sports', 'fitness', 'country clubs', 'racquet sports'],
            'golf': ['sports', 'golf courses', 'country clubs', 'outdoor activities'],
            'yoga': ['wellness', 'fitness', 'mindfulness', 'health', 'meditation'],
            'gym': ['fitness', 'health', 'wellness', 'exercise', 'personal training'],
            
            # Music to related interests
            'guitar': ['music', 'instruments', 'concerts', 'live music', 'music stores', 'bands'],
            'piano': ['music', 'instruments', 'classical music', 'concerts', 'recitals'],
            'concert': ['music', 'live entertainment', 'nightlife', 'social events'],
            'festival': ['music', 'outdoor events', 'social gatherings', 'food', 'arts'],
            
            # Professional to related interests
            'developer': ['technology', 'programming', 'tech meetups', 'hackathons', 'conferences'],
            'teacher': ['education', 'workshops', 'learning', 'community service', 'youth activities'],
            'artist': ['arts', 'galleries', 'exhibitions', 'creative workshops', 'art supplies'],
            'chef': ['cooking', 'restaurants', 'food events', 'culinary arts', 'farmers markets'],
            
            # Hobbies to related interests
            'photography': ['arts', 'outdoors', 'travel', 'galleries', 'camera equipment'],
            'painting': ['arts', 'art supplies', 'galleries', 'workshops', 'creative spaces'],
            'gardening': ['outdoors', 'nature', 'farmers markets', 'home improvement', 'sustainability'],
            'reading': ['books', 'libraries', 'book clubs', 'literary events', 'cafes'],
            'gaming': ['video games', 'technology', 'esports', 'gaming cafes', 'conventions'],
            
            # Lifestyle to related interests
            'vegan': ['plant-based food', 'health', 'sustainability', 'farmers markets', 'specialty restaurants'],
            'fitness': ['gym', 'health', 'sports', 'wellness', 'active lifestyle'],
            'travel': ['tourism', 'culture', 'adventure', 'photography', 'food'],
            'foodie': ['restaurants', 'cooking', 'food festivals', 'wine tasting', 'culinary events']
        }
        
    def _load_inference_rules(self) -> List[Dict[str, Any]]:
        """Load inference rules for detecting interests"""
        return [
            {
                'pattern': r'owns?\s+a?\s*(\w+)',
                'category': 'ownership',
                'inference': 'pet_owner'
            },
            {
                'pattern': r'plays?\s+(\w+)',
                'category': 'activity',
                'inference': 'active_person'
            },
            {
                'pattern': r'loves?\s+(\w+)',
                'category': 'preference',
                'inference': 'enthusiast'
            },
            {
                'pattern': r'works?\s+(?:as|at|in)\s+(\w+)',
                'category': 'profession',
                'inference': 'professional'
            },
            {
                'pattern': r'studies?\s+(\w+)',
                'category': 'education',
                'inference': 'student'
            },
            {
                'pattern': r'member\s+of\s+(\w+)',
                'category': 'membership',
                'inference': 'community_member'
            }
        ]
        
    async def detect_relations_ai(self, 
                                text_data: List[str],
                                known_interests: List[str] = None) -> Dict[str, Any]:
        """
        Use AI to detect relationships and infer interests from text data
        
        Args:
            text_data: List of text snippets about the user
            known_interests: Already identified interests
            
        Returns:
            Dictionary of detected relations and inferred interests
        """
        if not self.openai_client:
            # Fall back to rule-based detection
            return self.detect_relations_fallback(text_data, known_interests)
            
        try:
            # Prepare the prompt
            text_combined = ' '.join(text_data[:10])  # Limit to prevent token overflow
            
            prompt = f"""Analyze the following text about a person and extract:
1. Their interests and hobbies
2. Related activities they might enjoy
3. Personality traits
4. Potential event preferences

Text: {text_combined}

Known interests: {', '.join(known_interests or [])}

Provide a JSON response with:
{{
    "interests": ["list of interests"],
    "related_interests": ["interests inferred from the text"],
    "personality_traits": ["list of traits"],
    "event_preferences": ["types of events they might enjoy"],
    "confidence": 0.0-1.0
}}"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing text to understand people's interests and preferences."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse the response
            result = json.loads(response.choices[0].message.content)
            
            return {
                'interests': result.get('interests', []),
                'related_interests': result.get('related_interests', []),
                'personality_traits': result.get('personality_traits', []),
                'event_preferences': result.get('event_preferences', []),
                'confidence': result.get('confidence', 0.7),
                'method': 'ai'
            }
            
        except Exception as e:
            logger.error(f"AI relation detection failed: {e}")
            return self.detect_relations_fallback(text_data, known_interests)
            
    def detect_relations_fallback(self, 
                                text_data: List[str],
                                known_interests: List[str] = None) -> Dict[str, Any]:
        """
        Fallback method for detecting relations using rules
        
        Args:
            text_data: List of text snippets
            known_interests: Already identified interests
            
        Returns:
            Dictionary of detected relations
        """
        detected_interests = set()
        related_interests = set()
        personality_traits = set()
        event_preferences = set()
        
        # Process each text snippet
        for text in text_data:
            text_lower = text.lower()
            
            # Apply inference rules
            for rule in self.interest_inference_rules:
                matches = re.findall(rule['pattern'], text_lower)
                for match in matches:
                    detected_interests.add(match)
                    
                    # Look up related interests
                    if match in self.relation_map:
                        related_interests.update(self.relation_map[match])
                        
            # Detect personality traits
            traits = self._detect_personality_traits(text_lower)
            personality_traits.update(traits)
            
            # Infer event preferences
            events = self._infer_event_preferences(text_lower, detected_interests)
            event_preferences.update(events)
            
        # Expand interests based on known patterns
        if known_interests:
            for interest in known_interests:
                if interest.lower() in self.relation_map:
                    related_interests.update(self.relation_map[interest.lower()])
                    
        return {
            'interests': list(detected_interests),
            'related_interests': list(related_interests),
            'personality_traits': list(personality_traits),
            'event_preferences': list(event_preferences),
            'confidence': 0.6,
            'method': 'rule_based'
        }
        
    def _detect_personality_traits(self, text: str) -> Set[str]:
        """Detect personality traits from text"""
        traits = set()
        
        trait_keywords = {
            'outgoing': ['social', 'friends', 'party', 'gathering', 'meetup'],
            'creative': ['create', 'design', 'art', 'music', 'write'],
            'active': ['run', 'exercise', 'sport', 'gym', 'fitness'],
            'intellectual': ['read', 'study', 'research', 'learn', 'book'],
            'adventurous': ['travel', 'explore', 'adventure', 'new'],
            'family-oriented': ['family', 'kids', 'children', 'parent'],
            'professional': ['work', 'career', 'business', 'professional'],
            'social': ['friends', 'social', 'community', 'group'],
            'nature-lover': ['nature', 'outdoor', 'hiking', 'camping'],
            'tech-savvy': ['technology', 'computer', 'programming', 'tech']
        }
        
        for trait, keywords in trait_keywords.items():
            if any(keyword in text for keyword in keywords):
                traits.add(trait)
                
        return traits
        
    def _infer_event_preferences(self, text: str, interests: Set[str]) -> Set[str]:
        """Infer event preferences from text and interests"""
        preferences = set()
        
        # Map interests to event types
        interest_to_events = {
            'music': ['concerts', 'music festivals', 'live performances'],
            'sports': ['sports games', 'tournaments', 'athletic events'],
            'art': ['art exhibitions', 'gallery openings', 'art workshops'],
            'food': ['food festivals', 'restaurant events', 'cooking classes'],
            'technology': ['tech meetups', 'hackathons', 'conferences'],
            'fitness': ['fitness classes', 'sports events', 'wellness workshops'],
            'social': ['social gatherings', 'networking events', 'parties'],
            'education': ['workshops', 'seminars', 'lectures'],
            'outdoor': ['outdoor activities', 'nature events', 'adventure sports'],
            'family': ['family events', 'kid-friendly activities', 'community events']
        }
        
        # Check text for direct mentions
        for interest, events in interest_to_events.items():
            if interest in text or interest in interests:
                preferences.update(events)
                
        # Add time-based preferences
        if 'morning' in text:
            preferences.add('morning activities')
        if 'evening' in text or 'night' in text:
            preferences.add('evening events')
        if 'weekend' in text:
            preferences.add('weekend events')
            
        return preferences
        
    def enhance_user_profile(self, 
                           profile: Dict[str, Any],
                           search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Enhance user profile with AI-detected relations
        
        Args:
            profile: Current user profile
            search_results: Search results about the user
            
        Returns:
            Enhanced profile with additional insights
        """
        # Extract text from search results
        text_data = []
        for result in search_results[:20]:  # Limit to prevent overload
            text_data.append(
                f"{result.get('title', '')} {result.get('description', '')} {result.get('content', '')}"
            )
            
        # Detect relations
        if text_data:
            relations = self.detect_relations_fallback(
                text_data, 
                profile.get('interests', [])
            )
            
            # Merge with existing profile
            existing_interests = set(profile.get('interests', []))
            new_interests = set(relations.get('interests', []))
            related_interests = set(relations.get('related_interests', []))
            
            # Update profile
            profile['interests'] = list(existing_interests | new_interests | related_interests)[:30]
            profile['personality_traits'] = list(set(
                profile.get('personality_traits', []) + 
                relations.get('personality_traits', [])
            ))[:15]
            profile['event_preferences'] = relations.get('event_preferences', [])[:20]
            profile['ai_confidence'] = relations.get('confidence', 0.5)
            profile['enhancement_method'] = relations.get('method', 'unknown')
            
        return profile
        
    def generate_interest_connections(self, interests: List[str]) -> Dict[str, List[str]]:
        """
        Generate a graph of connected interests
        
        Args:
            interests: List of user interests
            
        Returns:
            Dictionary mapping interests to related interests
        """
        connections = defaultdict(list)
        
        for interest in interests:
            interest_lower = interest.lower()
            
            # Direct mappings
            if interest_lower in self.relation_map:
                connections[interest].extend(self.relation_map[interest_lower])
                
            # Find related interests through similarity
            for key, related in self.relation_map.items():
                if interest_lower in key or key in interest_lower:
                    connections[interest].extend(related)
                    
            # Remove duplicates and self-references
            connections[interest] = list(set(
                conn for conn in connections[interest] 
                if conn.lower() != interest_lower
            ))[:10]
            
        return dict(connections)
        
    def score_event_relevance(self, 
                            event: Dict[str, Any],
                            user_profile: Dict[str, Any]) -> float:
        """
        Score an event's relevance to a user profile using AI insights
        
        Args:
            event: Event information
            user_profile: User profile with interests
            
        Returns:
            Relevance score (0-1)
        """
        score = 0.0
        
        # Extract event text
        event_text = f"{event.get('name', '')} {event.get('description', '')} {event.get('type', '')}".lower()
        
        # Check direct interest matches
        user_interests = [i.lower() for i in user_profile.get('interests', [])]
        for interest in user_interests:
            if interest in event_text:
                score += 0.3
                
        # Check related interests
        for interest in user_interests:
            if interest in self.relation_map:
                for related in self.relation_map[interest]:
                    if related.lower() in event_text:
                        score += 0.1
                        
        # Check event preferences
        event_prefs = [p.lower() for p in user_profile.get('event_preferences', [])]
        for pref in event_prefs:
            if pref in event_text:
                score += 0.2
                
        # Personality trait alignment
        traits = user_profile.get('personality_traits', [])
        if 'social' in traits and 'social' in event_text:
            score += 0.1
        if 'active' in traits and any(word in event_text for word in ['sport', 'fitness', 'active']):
            score += 0.1
        if 'creative' in traits and any(word in event_text for word in ['art', 'music', 'creative']):
            score += 0.1
            
        # Time preference alignment
        if 'morning' in user_profile.get('activity_times', []) and 'morning' in event_text:
            score += 0.05
        if 'evening' in user_profile.get('activity_times', []) and 'evening' in event_text:
            score += 0.05
            
        return min(score, 1.0)