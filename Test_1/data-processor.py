"""
data_processor.py - Process and filter scraped data to extract user interests
"""
import re
import logging
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from collections import Counter, defaultdict
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.chunk import ne_chunk
from nltk.tag import pos_tag
import spacy
from textblob import TextBlob
import yake
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)
    nltk.download('maxent_ne_chunker', quiet=True)
    nltk.download('words', quiet=True)
except:
    pass

logger = logging.getLogger(__name__)

@dataclass
class Interest:
    """Represents a user interest"""
    keyword: str
    category: str
    confidence: float
    sources: List[str] = field(default_factory=list)
    related_terms: List[str] = field(default_factory=list)
    context: str = ""
    frequency: int = 1

@dataclass
class ProcessedData:
    """Processed data with extracted interests"""
    interests: List[Interest]
    entities: Dict[str, List[str]]  # person, organization, location, etc.
    topics: List[str]
    sentiment_summary: Dict[str, float]
    key_phrases: List[str]
    activity_indicators: List[str]
    raw_text_summary: str

class InterestExtractor:
    """Extract interests from text data"""
    
    # Interest categories and their keywords
    INTEREST_CATEGORIES = {
        'music': {
            'keywords': ['music', 'concert', 'band', 'song', 'album', 'guitar', 'piano', 
                        'singer', 'musician', 'festival', 'spotify', 'soundcloud', 'DJ'],
            'patterns': [r'plays?\s+\w+', r'listen(s|ing)?\s+to', r'fan\s+of']
        },
        'sports': {
            'keywords': ['sports', 'football', 'basketball', 'baseball', 'soccer', 'tennis',
                        'running', 'gym', 'fitness', 'workout', 'athlete', 'team', 'game'],
            'patterns': [r'plays?\s+\w+\s+sport', r'watches?\s+\w+', r'fan\s+of\s+\w+']
        },
        'technology': {
            'keywords': ['technology', 'programming', 'coding', 'software', 'hardware', 
                        'computer', 'AI', 'machine learning', 'developer', 'engineer',
                        'startup', 'tech', 'digital', 'innovation'],
            'patterns': [r'works?\s+with\s+\w+', r'develops?\s+\w+', r'codes?\s+in\s+\w+']
        },
        'arts': {
            'keywords': ['art', 'painting', 'drawing', 'photography', 'design', 'creative',
                        'artist', 'gallery', 'museum', 'exhibition', 'sculpture', 'craft'],
            'patterns': [r'creates?\s+\w+', r'designs?\s+\w+', r'exhibits?\s+at']
        },
        'food': {
            'keywords': ['food', 'cooking', 'recipe', 'restaurant', 'chef', 'cuisine',
                        'dining', 'foodie', 'culinary', 'baking', 'wine', 'coffee'],
            'patterns': [r'cooks?\s+\w+', r'loves?\s+\w+\s+food', r'dines?\s+at']
        },
        'travel': {
            'keywords': ['travel', 'vacation', 'trip', 'journey', 'destination', 'tourist',
                        'explore', 'adventure', 'flight', 'hotel', 'backpacking'],
            'patterns': [r'travels?\s+to', r'visited\s+\w+', r'explores?\s+\w+']
        },
        'education': {
            'keywords': ['education', 'learning', 'study', 'university', 'college', 'course',
                        'degree', 'student', 'teacher', 'professor', 'academic', 'research'],
            'patterns': [r'studies?\s+\w+', r'teaches?\s+\w+', r'graduated\s+from']
        },
        'business': {
            'keywords': ['business', 'entrepreneur', 'startup', 'company', 'CEO', 'founder',
                        'marketing', 'sales', 'investment', 'finance', 'management'],
            'patterns': [r'founded\s+\w+', r'works?\s+at\s+\w+', r'manages?\s+\w+']
        },
        'health': {
            'keywords': ['health', 'wellness', 'fitness', 'yoga', 'meditation', 'medical',
                        'doctor', 'nurse', 'therapy', 'mental health', 'nutrition'],
            'patterns': [r'practices?\s+\w+', r'focuses?\s+on\s+health']
        },
        'entertainment': {
            'keywords': ['movie', 'film', 'TV', 'television', 'show', 'series', 'netflix',
                        'theater', 'comedy', 'drama', 'entertainment', 'celebrity'],
            'patterns': [r'watches?\s+\w+', r'fan\s+of\s+\w+', r'follows?\s+\w+']
        },
        'nature': {
            'keywords': ['nature', 'outdoor', 'hiking', 'camping', 'mountain', 'beach',
                        'park', 'wildlife', 'environment', 'sustainability', 'green'],
            'patterns': [r'hikes?\s+at', r'camps?\s+at', r'explores?\s+nature']
        },
        'community': {
            'keywords': ['community', 'volunteer', 'charity', 'nonprofit', 'social', 'cause',
                        'activism', 'movement', 'organization', 'group', 'club'],
            'patterns': [r'volunteers?\s+at', r'supports?\s+\w+', r'member\s+of']
        }
    }
    
    # Activity indicators
    ACTIVITY_PATTERNS = {
        'professional': ['works at', 'employed by', 'CEO of', 'founder of', 'manager at'],
        'educational': ['studies at', 'graduated from', 'alumni of', 'degree in'],
        'creative': ['creates', 'designs', 'writes', 'performs', 'produces'],
        'social': ['member of', 'attends', 'participates in', 'joins', 'connects with'],
        'recreational': ['enjoys', 'loves', 'passionate about', 'interested in', 'fan of']
    }
    
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
        # Try to load spaCy model
        try:
            self.nlp = spacy.load('en_core_web_sm')
            self.use_spacy = True
        except:
            logger.warning("spaCy model not found, using NLTK only")
            self.use_spacy = False
        
        # Initialize keyword extractor
        self.kw_extractor = yake.KeywordExtractor(
            lan="en",
            n=3,  # max ngram size
            dedupLim=0.7,
            top=20,
            features=None
        )
    
    def extract_interests(self, text: str, source: str = "unknown") -> List[Interest]:
        """Extract interests from text"""
        interests = []
        text_lower = text.lower()
        
        # Category-based extraction
        for category, data in self.INTEREST_CATEGORIES.items():
            category_score = 0
            found_keywords = []
            
            # Check keywords
            for keyword in data['keywords']:
                if keyword in text_lower:
                    category_score += text_lower.count(keyword)
                    found_keywords.append(keyword)
            
            # Check patterns
            for pattern in data['patterns']:
                matches = re.findall(pattern, text_lower)
                category_score += len(matches)
                found_keywords.extend(matches)
            
            # Create interest if score is significant
            if category_score > 0:
                confidence = min(1.0, category_score / 10)  # Normalize confidence
                
                for keyword in set(found_keywords):
                    interests.append(Interest(
                        keyword=keyword,
                        category=category,
                        confidence=confidence,
                        sources=[source],
                        context=self._extract_context(text, keyword),
                        frequency=text_lower.count(keyword)
                    ))
        
        # Extract additional interests using NLP
        nlp_interests = self._extract_interests_nlp(text, source)
        interests.extend(nlp_interests)
        
        # Merge similar interests
        interests = self._merge_similar_interests(interests)
        
        return interests
    
    def _extract_interests_nlp(self, text: str, source: str) -> List[Interest]:
        """Extract interests using NLP techniques"""
        interests = []
        
        # Extract keywords using YAKE
        try:
            keywords = self.kw_extractor.extract_keywords(text)
            for kw, score in keywords[:10]:  # Top 10 keywords
                # Determine category
                category = self._categorize_keyword(kw)
                if category:
                    interests.append(Interest(
                        keyword=kw,
                        category=category,
                        confidence=1.0 - score,  # YAKE score is inverse
                        sources=[source],
                        context=self._extract_context(text, kw)
                    ))
        except Exception as e:
            logger.error(f"Keyword extraction error: {e}")
        
        # Use spaCy for entity and phrase extraction
        if self.use_spacy:
            try:
                doc = self.nlp(text[:1000000])  # Limit text length for performance
                
                # Extract noun phrases
                for chunk in doc.noun_chunks:
                    if len(chunk.text.split()) > 1 and len(chunk.text) < 50:
                        category = self._categorize_keyword(chunk.text)
                        if category:
                            interests.append(Interest(
                                keyword=chunk.text,
                                category=category,
                                confidence=0.7,
                                sources=[source],
                                context=self._extract_context(text, chunk.text)
                            ))
            except Exception as e:
                logger.error(f"spaCy processing error: {e}")
        
        return interests
    
    def _categorize_keyword(self, keyword: str) -> Optional[str]:
        """Categorize a keyword into interest categories"""
        keyword_lower = keyword.lower()
        
        # Check each category
        best_category = None
        best_score = 0
        
        for category, data in self.INTEREST_CATEGORIES.items():
            score = 0
            for cat_keyword in data['keywords']:
                if cat_keyword in keyword_lower:
                    score += 1
                elif keyword_lower in cat_keyword:
                    score += 0.5
            
            if score > best_score:
                best_score = score
                best_category = category
        
        return best_category if best_score > 0 else 'general'
    
    def _extract_context(self, text: str, keyword: str, window: int = 50) -> str:
        """Extract context around keyword"""
        keyword_lower = keyword.lower()
        text_lower = text.lower()
        
        index = text_lower.find(keyword_lower)
        if index == -1:
            return ""
        
        start = max(0, index - window)
        end = min(len(text), index + len(keyword) + window)
        
        context = text[start:end]
        return f"...{context}..." if start > 0 or end < len(text) else context
    
    def _merge_similar_interests(self, interests: List[Interest]) -> List[Interest]:
        """Merge similar interests"""
        merged = {}
        
        for interest in interests:
            key = (interest.keyword.lower(), interest.category)
            
            if key in merged:
                # Merge with existing
                existing = merged[key]
                existing.confidence = max(existing.confidence, interest.confidence)
                existing.sources.extend(interest.sources)
                existing.sources = list(set(existing.sources))
                existing.frequency += interest.frequency
                
                # Update context if new one is longer
                if len(interest.context) > len(existing.context):
                    existing.context = interest.context
            else:
                merged[key] = interest
        
        return list(merged.values())

class DataProcessor:
    """Main data processing and filtering class"""
    
    def __init__(self, config):
        self.config = config
        self.interest_extractor = InterestExtractor()
        self.stop_words = set(stopwords.words('english'))
    
    def process_scraper_results(self, scraper_results: List, 
                               search_query: Dict) -> ProcessedData:
        """
        Process all scraper results to extract interests and relevant data
        
        Args:
            scraper_results: List of ScraperResult objects
            search_query: Original search query
            
        Returns:
            ProcessedData object with extracted interests
        """
        all_text = []
        all_interests = []
        entities = defaultdict(list)
        sentiment_scores = []
        
        # Process each scraper result
        for result in scraper_results:
            if not result.success:
                continue
            
            # Extract text from result
            text = self._extract_text_from_result(result)
            if text:
                all_text.append(text)
                
                # Extract interests
                interests = self.interest_extractor.extract_interests(
                    text, 
                    source=result.source
                )
                all_interests.extend(interests)
                
                # Extract entities
                result_entities = self._extract_entities(text)
                for entity_type, entity_list in result_entities.items():
                    entities[entity_type].extend(entity_list)
                
                # Analyze sentiment
                sentiment = self._analyze_sentiment(text)
                sentiment_scores.append(sentiment)
        
        # Combine and process all text
        combined_text = ' '.join(all_text)
        
        # Extract key phrases
        key_phrases = self._extract_key_phrases(combined_text)
        
        # Extract activity indicators
        activity_indicators = self._extract_activity_indicators(combined_text)
        
        # Extract topics
        topics = self._extract_topics(combined_text)
        
        # Filter and rank interests
        filtered_interests = self._filter_interests(
            all_interests, 
            search_query
        )
        
        # Calculate sentiment summary
        sentiment_summary = self._calculate_sentiment_summary(sentiment_scores)
        
        # Deduplicate entities
        for entity_type in entities:
            entities[entity_type] = list(set(entities[entity_type]))
        
        return ProcessedData(
            interests=filtered_interests,
            entities=dict(entities),
            topics=topics,
            sentiment_summary=sentiment_summary,
            key_phrases=key_phrases,
            activity_indicators=activity_indicators,
            raw_text_summary=self._create_text_summary(combined_text)
        )
    
    def _extract_text_from_result(self, result) -> str:
        """Extract all text from a scraper result"""
        texts = []
        
        # Add raw text if available
        if result.raw_text:
            texts.append(result.raw_text)
        
        # Extract text from data structure
        def extract_recursive(obj):
            if isinstance(obj, str):
                return obj
            elif isinstance(obj, dict):
                return ' '.join(extract_recursive(v) for v in obj.values())
            elif isinstance(obj, list):
                return ' '.join(extract_recursive(item) for item in obj)
            else:
                return str(obj)
        
        texts.append(extract_recursive(result.data))
        
        return ' '.join(texts)
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from text"""
        entities = defaultdict(list)
        
        try:
            # Use NLTK for entity extraction
            tokens = word_tokenize(text[:5000])  # Limit for performance
            pos_tags = pos_tag(tokens)
            chunks = ne_chunk(pos_tags, binary=False)
            
            for chunk in chunks:
                if hasattr(chunk, 'label'):
                    entity_type = chunk.label()
                    entity_text = ' '.join(c[0] for c in chunk)
                    
                    # Map to our categories
                    if entity_type == 'PERSON':
                        entities['person'].append(entity_text)
                    elif entity_type in ['ORGANIZATION', 'FACILITY']:
                        entities['organization'].append(entity_text)
                    elif entity_type in ['GPE', 'LOCATION']:
                        entities['location'].append(entity_text)
        except Exception as e:
            logger.error(f"Entity extraction error: {e}")
        
        return dict(entities)
    
    def _analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of text"""
        try:
            blob = TextBlob(text[:5000])  # Limit for performance
            return {
                'polarity': blob.sentiment.polarity,
                'subjectivity': blob.sentiment.subjectivity
            }
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {'polarity': 0.0, 'subjectivity': 0.0}
    
    def _extract_key_phrases(self, text: str, max_phrases: int = 20) -> List[str]:
        """Extract key phrases using TF-IDF"""
        try:
            # Preprocess text
            sentences = sent_tokenize(text[:10000])
            
            if len(sentences) < 3:
                return []
            
            # Use TF-IDF
            vectorizer = TfidfVectorizer(
                max_features=100,
                ngram_range=(1, 3),
                stop_words='english'
            )
            
            tfidf_matrix = vectorizer.fit_transform(sentences)
            feature_names = vectorizer.get_feature_names_out()
            
            # Get top features
            scores = tfidf_matrix.sum(axis=0).A1
            top_indices = scores.argsort()[-max_phrases:][::-1]
            
            return [feature_names[i] for i in top_indices]
            
        except Exception as e:
            logger.error(f"Key phrase extraction error: {e}")
            return []
    
    def _extract_activity_indicators(self, text: str) -> List[str]:
        """Extract activity indicators from text"""
        indicators = []
        text_lower = text.lower()
        
        for category, patterns in InterestExtractor.ACTIVITY_PATTERNS.items():
            for pattern in patterns:
                if pattern in text_lower:
                    # Extract the full context
                    matches = re.findall(f"{pattern}[^.!?]*", text_lower)
                    for match in matches[:3]:  # Limit matches per pattern
                        indicators.append({
                            'category': category,
                            'indicator': match.strip(),
                            'pattern': pattern
                        })
        
        return indicators
    
    def _extract_topics(self, text: str, num_topics: int = 5) -> List[str]:
        """Extract main topics using clustering"""
        try:
            # Extract sentences
            sentences = sent_tokenize(text[:10000])
            
            if len(sentences) < num_topics:
                return []
            
            # Vectorize sentences
            vectorizer = TfidfVectorizer(
                max_features=50,
                stop_words='english'
            )
            
            X = vectorizer.fit_transform(sentences)
            
            # Cluster sentences
            kmeans = KMeans(n_clusters=min(num_topics, len(sentences)))
            kmeans.fit(X)
            
            # Get top terms for each cluster
            feature_names = vectorizer.get_feature_names_out()
            topics = []
            
            for i in range(kmeans.n_clusters):
                # Get top terms for this cluster
                cluster_center = kmeans.cluster_centers_[i]
                top_indices = cluster_center.argsort()[-5:][::-1]
                top_terms = [feature_names[idx] for idx in top_indices]
                topics.append(' '.join(top_terms))
            
            return topics
            
        except Exception as e:
            logger.error(f"Topic extraction error: {e}")
            return []
    
    def _filter_interests(self, interests: List[Interest], 
                         search_query: Dict) -> List[Interest]:
        """Filter and rank interests based on relevance"""
        # Filter by confidence
        filtered = [i for i in interests 
                   if i.confidence >= self.config.ai.interest_extraction_confidence]
        
        # Boost interests related to the search activity
        if 'activity' in search_query:
            activity_lower = search_query['activity'].lower()
            for interest in filtered:
                if activity_lower in interest.keyword.lower():
                    interest.confidence *= 1.5
                elif interest.keyword.lower() in activity_lower:
                    interest.confidence *= 1.2
        
        # Sort by confidence and frequency
        filtered.sort(key=lambda x: (x.confidence * x.frequency), reverse=True)
        
        # Limit to max interests
        return filtered[:self.config.ai.max_interests_to_extract]
    
    def _calculate_sentiment_summary(self, sentiments: List[Dict]) -> Dict[str, float]:
        """Calculate overall sentiment summary"""
        if not sentiments:
            return {'polarity': 0.0, 'subjectivity': 0.0, 'overall': 'neutral'}
        
        avg_polarity = np.mean([s['polarity'] for s in sentiments])
        avg_subjectivity = np.mean([s['subjectivity'] for s in sentiments])
        
        # Determine overall sentiment
        if avg_polarity > 0.1:
            overall = 'positive'
        elif avg_polarity < -0.1:
            overall = 'negative'
        else:
            overall = 'neutral'
        
        return {
            'polarity': float(avg_polarity),
            'subjectivity': float(avg_subjectivity),
            'overall': overall
        }
    
    def _create_text_summary(self, text: str, max_length: int = 500) -> str:
        """Create a brief summary of the text"""
        if len(text) <= max_length:
            return text
        
        # Simple extractive summarization
        sentences = sent_tokenize(text)
        if not sentences:
            return text[:max_length]
        
        # Take first few sentences
        summary = []
        total_length = 0
        
        for sentence in sentences:
            if total_length + len(sentence) <= max_length:
                summary.append(sentence)
                total_length += len(sentence)
            else:
                break
        
        return ' '.join(summary)
    
    def filter_interests_by_location(self, interests: List[Interest], 
                                   location: str) -> List[Interest]:
        """Filter interests based on location relevance"""
        # This could be enhanced with location-specific interest weighting
        # For now, return all interests
        return interests
    
    def get_interest_keywords(self, processed_data: ProcessedData) -> List[str]:
        """Get keywords for EventBrite search"""
        keywords = []
        
        # Add high-confidence interest keywords
        for interest in processed_data.interests:
            if interest.confidence >= 0.7:
                keywords.append(interest.keyword)
                keywords.extend(interest.related_terms[:2])
        
        # Add top key phrases
        keywords.extend(processed_data.key_phrases[:5])
        
        # Add activity indicators
        for indicator in processed_data.activity_indicators[:3]:
            if isinstance(indicator, dict):
                keywords.append(indicator.get('pattern', ''))
        
        # Remove duplicates and clean
        keywords = list(set(k.strip() for k in keywords if k.strip()))
        
        return keywords[:20]  # Limit to top 20 keywords
