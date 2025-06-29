"""
ai_integration.py - Optional AI integration for enhanced processing
"""
import json
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import openai
import requests
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

@dataclass
class AIEnhancedInterest:
    """Interest enhanced by AI processing"""
    original_interest: str
    enhanced_category: str
    related_interests: List[str]
    confidence: float
    reasoning: str
    source: str = "ai"

@dataclass
class RelationalInsight:
    """Insight derived from relational AI analysis"""
    source_fact: str
    derived_interest: str
    confidence: float
    reasoning: str
    category: str

class AIProcessor:
    """Base class for AI processors"""
    
    def __init__(self, config):
        self.config = config
        self.enabled = config.ai.enable_ai
        
    def is_available(self) -> bool:
        """Check if AI processor is available"""
        return self.enabled
    
    def process_interests(self, interests: List[Dict], 
                         context: str) -> List[AIEnhancedInterest]:
        """Process interests with AI enhancement"""
        raise NotImplementedError
    
    def generate_relations(self, facts: List[str]) -> List[RelationalInsight]:
        """Generate relational insights from facts"""
        raise NotImplementedError

class OpenAIProcessor(AIProcessor):
    """OpenAI-based processing"""
    
    def __init__(self, config):
        super().__init__(config)
        self.api_key = config.api.openai_api_key
        
        if self.api_key and self.enabled:
            openai.api_key = self.api_key
            self.model = config.ai.openai_model
            self.available = True
        else:
            self.available = False
            if self.enabled:
                logger.warning("OpenAI API key not provided")
    
    def is_available(self) -> bool:
        return self.available
    
    def process_interests(self, interests: List[Dict], 
                         context: str = "") -> List[AIEnhancedInterest]:
        """Enhanced interest extraction using OpenAI"""
        if not self.available:
            return []
        
        try:
            # Prepare prompt
            prompt = self.config.ai.interest_extraction_prompt.format(
                data=json.dumps(interests) + "\n\nContext: " + context[:1000]
            )
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing user interests and hobbies."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            # Parse response
            result = response.choices[0].message.content
            
            try:
                parsed_interests = json.loads(result)
                enhanced_interests = []
                
                for item in parsed_interests:
                    enhanced_interests.append(AIEnhancedInterest(
                        original_interest=item.get('interest', ''),
                        enhanced_category=item.get('category', 'general'),
                        related_interests=item.get('related', []),
                        confidence=item.get('confidence', 0.5),
                        reasoning=item.get('reasoning', '')
                    ))
                
                return enhanced_interests
                
            except json.JSONDecodeError:
                logger.error("Failed to parse OpenAI response as JSON")
                return []
                
        except Exception as e:
            logger.error(f"OpenAI processing error: {e}")
            return []
    
    def generate_relations(self, facts: List[str]) -> List[RelationalInsight]:
        """Generate relational insights using OpenAI"""
        if not self.available or not facts:
            return []
        
        try:
            # Prepare prompt
            prompt = self.config.ai.relation_generation_prompt.format(
                facts=json.dumps(facts[:20])  # Limit facts
            )
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at inferring interests from facts about people."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=800
            )
            
            # Parse response
            result = response.choices[0].message.content
            
            try:
                parsed_relations = json.loads(result)
                insights = []
                
                for item in parsed_relations:
                    insights.append(RelationalInsight(
                        source_fact=item.get('source_fact', ''),
                        derived_interest=item.get('derived_interest', ''),
                        confidence=item.get('confidence', 0.5),
                        reasoning=item.get('reasoning', ''),
                        category=item.get('category', 'general')
                    ))
                
                return insights
                
            except json.JSONDecodeError:
                logger.error("Failed to parse OpenAI relations as JSON")
                return []
                
        except Exception as e:
            logger.error(f"OpenAI relation generation error: {e}")
            return []
    
    def classify_text(self, text: str, categories: List[str]) -> Tuple[str, float]:
        """Classify text into categories"""
        if not self.available:
            return "general", 0.5
        
        try:
            prompt = f"""Classify the following text into one of these categories: {', '.join(categories)}
            
            Text: {text[:500]}
            
            Return only the category name and confidence (0-1) as JSON: {{"category": "...", "confidence": 0.X}}"""
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a text classification expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=50
            )
            
            result = json.loads(response.choices[0].message.content)
            return result['category'], result['confidence']
            
        except Exception as e:
            logger.error(f"OpenAI classification error: {e}")
            return "general", 0.5

class HuggingFaceProcessor(AIProcessor):
    """HuggingFace-based processing"""
    
    def __init__(self, config):
        super().__init__(config)
        self.api_key = config.api.huggingface_api_key
        self.api_url = "https://api-inference.huggingface.co/models/"
        self.model_name = config.ai.huggingface_model
        
        if self.api_key and self.enabled:
            self.headers = {"Authorization": f"Bearer {self.api_key}"}
            self.available = True
            self._initialize_local_models()
        else:
            self.available = False
            if self.enabled:
                logger.warning("HuggingFace API key not provided")
    
    def _initialize_local_models(self):
        """Initialize local models for faster processing"""
        try:
            # Initialize sentence transformer for embeddings
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Initialize zero-shot classifier
            self.classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli"
            )
            
            self.local_models_available = True
        except Exception as e:
            logger.warning(f"Failed to initialize local models: {e}")
            self.local_models_available = False
    
    def is_available(self) -> bool:
        return self.available
    
    def process_interests(self, interests: List[Dict], 
                         context: str = "") -> List[AIEnhancedInterest]:
        """Process interests using HuggingFace models"""
        if not self.available:
            return []
        
        enhanced_interests = []
        
        # Use local models if available
        if hasattr(self, 'local_models_available') and self.local_models_available:
            try:
                # Process each interest
                for interest in interests:
                    interest_text = interest.get('keyword', '')
                    
                    # Classify into categories
                    categories = list(InterestExtractor.INTEREST_CATEGORIES.keys())
                    result = self.classifier(
                        interest_text,
                        candidate_labels=categories,
                        multi_label=False
                    )
                    
                    # Get top category
                    top_category = result['labels'][0]
                    confidence = result['scores'][0]
                    
                    # Find related interests using embeddings
                    related = self._find_related_interests(interest_text, interests)
                    
                    enhanced_interests.append(AIEnhancedInterest(
                        original_interest=interest_text,
                        enhanced_category=top_category,
                        related_interests=related[:5],
                        confidence=confidence,
                        reasoning=f"Classified as {top_category} with {confidence:.2f} confidence"
                    ))
                    
            except Exception as e:
                logger.error(f"Local model processing error: {e}")
                return self._process_with_api(interests, context)
        else:
            return self._process_with_api(interests, context)
        
        return enhanced_interests
    
    def _process_with_api(self, interests: List[Dict], context: str) -> List[AIEnhancedInterest]:
        """Process using HuggingFace API"""
        try:
            # Prepare input
            text = f"Interests: {json.dumps(interests)}\nContext: {context[:500]}"
            
            payload = {
                "inputs": text,
                "parameters": {
                    "max_length": 500,
                    "temperature": 0.3
                }
            }
            
            response = requests.post(
                f"{self.api_url}{self.model_name}",
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                # Process API response
                # This would need specific handling based on the model
                return []
            else:
                logger.error(f"HuggingFace API error: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"HuggingFace API error: {e}")
            return []
    
    def _find_related_interests(self, interest: str, all_interests: List[Dict]) -> List[str]:
        """Find related interests using sentence embeddings"""
        if not hasattr(self, 'sentence_model'):
            return []
        
        try:
            # Get embeddings
            interest_embedding = self.sentence_model.encode([interest])
            other_texts = [i.get('keyword', '') for i in all_interests 
                          if i.get('keyword', '') != interest]
            
            if not other_texts:
                return []
            
            other_embeddings = self.sentence_model.encode(other_texts)
            
            # Calculate similarities
            similarities = cosine_similarity(interest_embedding, other_embeddings)[0]
            
            # Get top similar interests
            top_indices = similarities.argsort()[-5:][::-1]
            related = [other_texts[i] for i in top_indices if similarities[i] > 0.5]
            
            return related
            
        except Exception as e:
            logger.error(f"Embedding similarity error: {e}")
            return []
    
    def generate_relations(self, facts: List[str]) -> List[RelationalInsight]:
        """Generate relations using HuggingFace models"""
        if not self.available:
            return []
        
        insights = []
        
        # Define relation patterns
        relation_patterns = {
            "owns a pet": ["animal lover", "responsible", "caring"],
            "plays sports": ["active lifestyle", "team player", "competitive"],
            "works in tech": ["problem solver", "innovative", "analytical"],
            "volunteers": ["community-minded", "altruistic", "socially conscious"],
            "travels frequently": ["adventurous", "culturally aware", "open-minded"]
        }
        
        try:
            for fact in facts[:10]:  # Limit processing
                fact_lower = fact.lower()
                
                for pattern, derived in relation_patterns.items():
                    if pattern in fact_lower:
                        for interest in derived:
                            insights.append(RelationalInsight(
                                source_fact=fact,
                                derived_interest=interest,
                                confidence=0.7,
                                reasoning=f"People who {pattern} often are {interest}",
                                category=self._categorize_interest(interest)
                            ))
                
                # Use NLP for more complex relations if local models available
                if hasattr(self, 'classifier') and self.classifier:
                    # Check for activity types
                    activities = ["sports", "arts", "technology", "social", "outdoor"]
                    result = self.classifier(fact, candidate_labels=activities)
                    
                    if result['scores'][0] > 0.7:
                        top_activity = result['labels'][0]
                        insights.append(RelationalInsight(
                            source_fact=fact,
                            derived_interest=f"{top_activity} enthusiast",
                            confidence=result['scores'][0],
                            reasoning=f"Detected {top_activity} activity pattern",
                            category=top_activity
                        ))
            
        except Exception as e:
            logger.error(f"Relation generation error: {e}")
        
        return insights
    
    def _categorize_interest(self, interest: str) -> str:
        """Categorize an interest"""
        # Simple keyword-based categorization
        interest_lower = interest.lower()
        
        category_keywords = {
            'sports': ['active', 'competitive', 'athletic'],
            'social': ['community', 'social', 'altruistic'],
            'intellectual': ['analytical', 'innovative', 'problem solver'],
            'creative': ['creative', 'artistic', 'imaginative'],
            'lifestyle': ['adventurous', 'open-minded', 'culturally aware']
        }
        
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in interest_lower:
                    return category
        
        return 'general'

class LocalAIProcessor(AIProcessor):
    """Local AI processing without external APIs"""
    
    def __init__(self, config):
        super().__init__(config)
        self.available = True
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize local models"""
        try:
            # Use smaller, faster models for local processing
            self.classifier = pipeline(
                "zero-shot-classification",
                model="typeform/distilbert-base-uncased-mnli"
            )
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english"
            )
            self.models_loaded = True
        except Exception as e:
            logger.warning(f"Failed to load local models: {e}")
            self.models_loaded = False
    
    def process_interests(self, interests: List[Dict], 
                         context: str = "") -> List[AIEnhancedInterest]:
        """Process interests using local models only"""
        if not self.models_loaded:
            return []
        
        enhanced_interests = []
        categories = ["music", "sports", "technology", "arts", "food", 
                     "travel", "education", "business", "health", "nature"]
        
        try:
            for interest in interests[:20]:  # Limit for performance
                interest_text = interest.get('keyword', '')
                
                # Classify interest
                result = self.classifier(
                    interest_text,
                    candidate_labels=categories,
                    multi_label=False
                )
                
                enhanced_interests.append(AIEnhancedInterest(
                    original_interest=interest_text,
                    enhanced_category=result['labels'][0],
                    related_interests=[],  # Could implement similarity search
                    confidence=result['scores'][0],
                    reasoning="Local classification model"
                ))
        
        except Exception as e:
            logger.error(f"Local AI processing error: {e}")
        
        return enhanced_interests
    
    def generate_relations(self, facts: List[str]) -> List[RelationalInsight]:
        """Generate basic relations using rules"""
        insights = []
        
        # Rule-based relation generation
        rules = {
            "student": ["education events", "learning workshops", "campus activities"],
            "developer": ["tech meetups", "hackathons", "coding workshops"],
            "artist": ["gallery openings", "art workshops", "creative events"],
            "musician": ["concerts", "music festivals", "open mic nights"],
            "fitness": ["sports events", "marathons", "fitness classes"],
            "foodie": ["food festivals", "cooking classes", "restaurant events"]
        }
        
        for fact in facts:
            fact_lower = fact.lower()
            
            for keyword, interests in rules.items():
                if keyword in fact_lower:
                    for interest in interests:
                        insights.append(RelationalInsight(
                            source_fact=fact,
                            derived_interest=interest,
                            confidence=0.6,
                            reasoning=f"Rule-based: {keyword} → {interest}",
                            category="events"
                        ))
        
        return insights

class AIIntegration:
    """Main AI integration class that manages different processors"""
    
    def __init__(self, config):
        self.config = config
        self.processors = {}
        
        # Initialize processors based on configuration
        if config.ai.enable_ai:
            if config.ai.ai_provider == "openai":
                self.processors['openai'] = OpenAIProcessor(config)
            elif config.ai.ai_provider == "huggingface":
                self.processors['huggingface'] = HuggingFaceProcessor(config)
            else:  # local
                self.processors['local'] = LocalAIProcessor(config)
        
        # Always have local processor as fallback
        if 'local' not in self.processors:
            self.processors['local'] = LocalAIProcessor(config)
    
    def get_active_processor(self) -> Optional[AIProcessor]:
        """Get the active AI processor"""
        # Try configured provider first
        provider = self.config.ai.ai_provider
        if provider in self.processors and self.processors[provider].is_available():
            return self.processors[provider]
        
        # Fallback to any available processor
        for processor in self.processors.values():
            if processor.is_available():
                return processor
        
        return None
    
    def enhance_interests(self, interests: List[Dict], 
                         context: str = "") -> List[AIEnhancedInterest]:
        """Enhance interests using AI"""
        processor = self.get_active_processor()
        if processor:
            return processor.process_interests(interests, context)
        return []
    
    def generate_relational_insights(self, facts: List[str]) -> List[RelationalInsight]:
        """Generate insights from facts"""
        processor = self.get_active_processor()
        if processor:
            return processor.generate_relations(facts)
        return []
    
    def is_available(self) -> bool:
        """Check if any AI processor is available"""
        return any(p.is_available() for p in self.processors.values())
    
    def get_status(self) -> Dict[str, bool]:
        """Get status of all processors"""
        return {
            name: processor.is_available() 
            for name, processor in self.processors.items()
        }
