"""
Keyword Matching Engine for ChatNShop Intent Classification

This module provides a high-performance keyword matching engine that processes user input
and matches against keyword dictionaries to determine user intents.

Features:
- Case-insensitive matching
- Partial word matching
- Special character and punctuation handling
- Confidence scoring for multiple matches
- Performance optimized for <50ms processing
- Efficient data structures (tries, hash maps)
- Cached text preprocessing
- Early termination on good matches

Author: AI Development Team
Version: 1.1.0 (Optimized)
"""

import re
import time
import logging
from typing import Dict, List, Tuple, Optional, Set, Any
from dataclasses import dataclass
from collections import defaultdict, Counter
import unicodedata
from pathlib import Path

# Import keyword loader
try:
    from .intent_system.keywords.loader import KeywordLoader
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    from intent_system.keywords.loader import KeywordLoader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class KeywordMatch:
    """Represents a keyword match result."""
    keyword: str
    intent_name: str
    match_type: str  # 'exact', 'partial', 'fuzzy'
    confidence: float
    start_pos: int
    end_pos: int
    priority_weight: float = 1.0


@dataclass
class MatchingResult:
    """Represents the result of keyword matching."""
    intent_name: str
    action_code: str
    confidence_score: float
    matched_keywords: List[KeywordMatch]
    processing_time_ms: float
    total_matches: int
    best_match_type: str
    metadata: Dict[str, Any] = None


class TextPreprocessor:
    """Handles text preprocessing for keyword matching."""
    
    def __init__(self):
        # Common punctuation patterns
        self.punctuation_pattern = re.compile(r'[^\w\s]')
        self.whitespace_pattern = re.compile(r'\s+')
        
        # Common contractions and abbreviations
        self.contractions = {
            "don't": "do not", "won't": "will not", "can't": "cannot",
            "n't": " not", "'re": " are", "'ve": " have", "'ll": " will",
            "i'm": "i am", "you're": "you are", "we're": "we are",
            "they're": "they are", "it's": "it is", "that's": "that is"
        }
        
        # Common misspellings and variations
        self.normalizations = {
            "colour": "color", "favour": "favor", "behaviour": "behavior",
            "centre": "center", "theatre": "theater", "realise": "realize",
            "organise": "organize", "analyse": "analyze", "catalogue": "catalog"
        }
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for consistent matching."""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower().strip()
        
        # Handle contractions
        for contraction, expansion in self.contractions.items():
            text = text.replace(contraction, expansion)
        
        # Handle UK/US variations
        for uk_word, us_word in self.normalizations.items():
            text = text.replace(uk_word, us_word)
        
        # Remove special characters but keep spaces
        text = self.punctuation_pattern.sub(' ', text)
        
        # Normalize whitespace
        text = self.whitespace_pattern.sub(' ', text)
        
        # Remove extra spaces
        text = text.strip()
        
        return text
    
    def tokenize(self, text: str) -> List[str]:
        """Tokenize text into words."""
        normalized = self.normalize_text(text)
        return [word for word in normalized.split() if word]
    
    def create_ngrams(self, tokens: List[str], n: int = 2) -> List[str]:
        """Create n-grams from tokens."""
        if len(tokens) < n:
            return tokens
        
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngram = ' '.join(tokens[i:i+n])
            ngrams.append(ngram)
        
        return ngrams


class KeywordTrie:
    """Efficient trie data structure for keyword matching."""
    
    def __init__(self):
        self.root = {}
        self.keywords = set()
    
    def insert(self, keyword: str, metadata: Dict[str, Any] = None):
        """Insert a keyword into the trie."""
        node = self.root
        for char in keyword:
            if char not in node:
                node[char] = {}
            node = node[char]
        
        # Mark end of word and store metadata
        node['$'] = metadata or {}
        self.keywords.add(keyword)
    
    def search(self, text: str) -> List[Tuple[str, Dict[str, Any]]]:
        """Search for keywords in text."""
        results = []
        text_lower = text.lower()
        
        for i in range(len(text_lower)):
            node = self.root
            j = i
            
            while j < len(text_lower) and text_lower[j] in node:
                node = node[text_lower[j]]
                j += 1
                
                if '$' in node:
                    keyword = text_lower[i:j]
                    results.append((keyword, node['$']))
        
        return results
    
    def get_all_keywords(self) -> Set[str]:
        """Get all keywords in the trie."""
        return self.keywords.copy()


class KeywordMatcher:
    """Main keyword matching engine."""
    
    def __init__(self, keyword_loader: Optional[KeywordLoader] = None):
        self.keyword_loader = keyword_loader or KeywordLoader()
        self.preprocessor = TextPreprocessor()
        
        # Data structures for efficient matching
        self.keyword_trie = KeywordTrie()
        self.keyword_hashmap = defaultdict(list)
        self.intent_keywords = defaultdict(list)
        self.priority_weights = {}
        
        # Performance tracking
        self.processing_times = []
        self.match_counts = Counter()
        
        # Load and build data structures
        self._build_matching_structures()
        
        logger.info(f"KeywordMatcher initialized with {len(self.keyword_trie.get_all_keywords())} keywords")
    
    def _build_matching_structures(self):
        """Build efficient data structures for keyword matching."""
        logger.info("Building keyword matching structures...")
        
        # Get all intent definitions
        intent_definitions = self.keyword_loader.get_all_intent_keywords()
        
        for intent_name, intent_data in intent_definitions.items():
            if not intent_data:
                continue
            
            # Process different types of keywords
            keyword_types = [
                'primary_keywords',
                'action_phrases', 
                'misspellings',
                'uk_variations'
            ]
            
            for keyword_type in keyword_types:
                if keyword_type in intent_data:
                    keywords = intent_data[keyword_type]
                    if isinstance(keywords, list):
                        for keyword in keywords:
                            if keyword:
                                # Normalize keyword
                                normalized = self.preprocessor.normalize_text(keyword)
                                
                                # Store in trie
                                metadata = {
                                    'intent_name': intent_name,
                                    'keyword_type': keyword_type,
                                    'original_keyword': keyword,
                                    'priority_weight': intent_data.get('priority_weights', {}).get(keyword, 1.0)
                                }
                                self.keyword_trie.insert(normalized, metadata)
                                
                                # Store in hashmap for exact matches
                                self.keyword_hashmap[normalized].append(metadata)
                                
                                # Store in intent-specific list
                                self.intent_keywords[intent_name].append({
                                    'keyword': normalized,
                                    'type': keyword_type,
                                    'weight': metadata['priority_weight']
                                })
        
        logger.info(f"Built structures for {len(self.intent_keywords)} intents")
    
    def _calculate_confidence_score(self, matches: List[KeywordMatch]) -> float:
        """Calculate confidence score based on matches with improved ranking."""
        if not matches:
            return 0.0
        
        # Base confidence from match types
        match_type_scores = {
            'exact': 1.0,
            'partial': 0.8,
            'fuzzy': 0.6
        }
        
        # Calculate weighted average with specificity boost
        total_weight = 0
        weighted_score = 0
        
        for match in matches:
            weight = match.priority_weight
            score = match_type_scores.get(match.match_type, 0.5)
            
            # Boost for multi-word phrases (more specific)
            specificity_boost = 0.0
            if ' ' in match.keyword:
                specificity_boost = 0.2  # Multi-word phrases are more specific
            
            # Boost for action phrases (more specific)
            if hasattr(match, 'keyword_type') and match.keyword_type == 'action_phrases':
                specificity_boost += 0.15
            
            # Boost for intent-specific keywords
            intent_specificity = self._get_intent_specificity_boost(match.intent_name, match.keyword)
            
            final_score = score + specificity_boost + intent_specificity
            weighted_score += final_score * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        base_confidence = weighted_score / total_weight
        
        # Boost confidence for multiple matches
        match_count_boost = min(0.2, len(matches) * 0.05)
        
        # Boost confidence for exact matches
        exact_match_boost = 0.1 if any(m.match_type == 'exact' for m in matches) else 0
        
        final_confidence = min(1.0, base_confidence + match_count_boost + exact_match_boost)
        
        return round(final_confidence, 3)
    
    def _get_intent_specificity_boost(self, intent_name: str, keyword: str) -> float:
        """Get specificity boost based on intent and keyword combination."""
        # Define high-specificity keyword patterns for each intent
        specificity_patterns = {
            'view_cart': ['show my cart', 'view my cart', 'what\'s in my cart', 'cart contents'],
            'view_profile': ['show my profile', 'view my profile', 'my profile', 'profile information'],
            'add_to_wishlist': ['add to wishlist', 'save to wishlist', 'wishlist'],
            'update_profile': ['update my profile', 'edit my profile', 'change my profile'],
            'view_orders': ['show my orders', 'view my orders', 'order history', 'my orders'],
            'track_order': ['track my order', 'where is my order', 'order status', 'tracking']
        }
        
        # Check if keyword matches high-specificity patterns
        for pattern in specificity_patterns.get(intent_name, []):
            if pattern.lower() in keyword.lower() or keyword.lower() in pattern.lower():
                return 0.3  # High boost for specific patterns
        
        return 0.0
    
    def _find_keyword_matches(self, text: str) -> List[KeywordMatch]:
        """Find all keyword matches in the given text with improved specificity."""
        matches = []
        normalized_text = self.preprocessor.normalize_text(text)
        
        # 1. Multi-word phrase matches first (most specific)
        phrase_matches = self._find_phrase_matches(normalized_text)
        matches.extend(phrase_matches)
        
        # 2. Exact matches using hashmap
        exact_matches = self._find_exact_matches(normalized_text)
        matches.extend(exact_matches)
        
        # 3. If we have good phrase or exact matches, prioritize them
        if len(phrase_matches) >= 1 or len(exact_matches) >= 2:
            return self._deduplicate_matches(matches)
        
        # 4. Partial matches using trie (only if no good exact matches)
        if len(exact_matches) == 0:
            partial_matches = self._find_partial_matches(normalized_text)
            matches.extend(partial_matches)
        
        # 5. N-gram matches for multi-word phrases (only for short texts)
        if len(normalized_text.split()) <= 5:
            tokens = self.preprocessor.tokenize(normalized_text)
            ngram_matches = self._find_ngram_matches(tokens)
            matches.extend(ngram_matches)
        
        # 6. Fuzzy matches only if no other matches found
        if len(matches) == 0:
            fuzzy_matches = self._find_fuzzy_matches(normalized_text)
            matches.extend(fuzzy_matches)
        
        # Remove duplicates and sort by confidence and specificity
        unique_matches = self._deduplicate_matches(matches)
        unique_matches.sort(key=lambda x: (x.confidence, len(x.keyword.split())), reverse=True)
        
        return unique_matches
    
    def _find_phrase_matches(self, text: str) -> List[KeywordMatch]:
        """Find multi-word phrase matches (most specific)."""
        matches = []
        
        # Look for common phrase patterns - EXPANDED AND IMPROVED
        phrase_patterns = [
            # Cart phrases
            'show my cart', 'view my cart', 'what\'s in my cart', 'my shopping cart',
            'show cart contents', 'view cart contents', 'cart summary',
            'what\'s in my basket', 'what did i add', 'my basket',
            'take this out of my basket', 'i don\'t want this anymore',
            'get rid of this', 'don\'t want this',
            'put this in my basket', 'i want to see clothing',
            'empty my basket', 'remove everything', 'start over',
            'delete all', 'quantity 2 please', 'i want 3 of these',
            
            # Profile phrases
            'show my profile', 'view my profile', 'my profile information',
            'update my profile', 'edit my profile', 'change my profile',
            'modify my profile', 'update personal info', 'edit personal info',
            
            # Wishlist phrases
            'add to wishlist', 'save to wishlist', 'save for later',
            'remove from wishlist', 'delete from wishlist', 'unsave this',
            'show my wishlist', 'view my wishlist', 'my wishlist',
            'my saved items', 'saved for later', 'my favorites',
            'add to favorites', 'add to my list', 'delete from favorites',
            'remove from my list', 'remove from saved', 'wishlist items',
            'favorites list',
            
            # Order phrases
            'show my orders', 'view my orders', 'my orders', 'order history',
            'track my order', 'where is my order', 'order status',
            'tracking information', 'package location', 'delivery status',
            
            # Search phrases
            'show me electronics', 'show me clothing', 'show me beauty products',
            'browse electronics', 'browse clothing', 'browse home and garden',
            'what\'s new', 'what\'s popular', 'what\'s trending',
            'new arrivals', 'popular items', 'featured products',
            'i\'m looking for', 'looking for a', 'looking for',
            'what do you have in', 'what\'s in the', 'sports section',
            'electronics please', 'clothing please', 'home decor items',
            'show me what\'s popular', 'browse deals', 'what\'s on sale',
            'what\'s new', 'what\'s trending', 'what\'s on sale',
            'show only red items', 'show items with free shipping',
            'under $50 please', 'only nike products', 'free shipping only',
            'sort by price low to high', 'show cheapest first', 'sort by newest',
            'sort by rating', 'sort by popularity', 'price ascending',
            'newest first', 'best rated',
            
            # Account phrases
            'log into my account', 'access my account', 'my account',
            'log out of my account', 'exit my account',
            'sign up for an account', 'create an account',
            'join the site', 'view my account', 'my info',
            'edit my information', 'change my details', 'modify my account',
            'edit contact info', 'change my address', 'my past purchases',
            'order list', 'order progress', 'what do you mean',
            'what does that mean', 'i have a question', 'need assistance',
            'get me customer service', 'use my discount code',
            'enter discount code', 'change payment method',
            'change shipping option', 'buy now', 'place order',
            'i want a refund', 'refund this purchase', 'refund please',
            'cancel and refund', 'what would you suggest', 'what\'s good',
            'see you later', 'thanks that\'s all', 'have a good day',
            'see you',
            
            # Support phrases
            'contact customer support', 'get customer service', 'help desk',
            'customer service please', 'support team',
            'return this item', 'return policy', 'how to return',
            'request refund', 'get my money back', 'money back',
            
            # Recommendation phrases
            'what do you recommend', 'suggest something for me',
            'recommend products', 'suggest items', 'any recommendations'
        ]
        
        text_lower = text.lower()
        for phrase in phrase_patterns:
            if phrase in text_lower:
                # Find which intent this phrase belongs to
                intent_name = self._get_intent_for_phrase(phrase)
                if intent_name:
                    match = KeywordMatch(
                        keyword=phrase,
                        intent_name=intent_name,
                        match_type='exact',
                        confidence=1.0,
                        start_pos=text_lower.find(phrase),
                        end_pos=text_lower.find(phrase) + len(phrase),
                        priority_weight=2.0  # Higher weight for phrases
                    )
                    matches.append(match)
        
        return matches
    
    def _get_intent_for_phrase(self, phrase: str) -> str:
        """Get intent name for a specific phrase."""
        phrase_intent_mapping = {
            # Cart phrases
            'show my cart': 'view_cart',
            'view my cart': 'view_cart',
            'what\'s in my cart': 'view_cart',
            'my shopping cart': 'view_cart',
            'show cart contents': 'view_cart',
            'view cart contents': 'view_cart',
            'cart summary': 'view_cart',
            'what\'s in my basket': 'view_cart',
            'what did i add': 'view_cart',
            'my basket': 'view_cart',
            'take this out of my basket': 'remove_from_cart',
            'i don\'t want this anymore': 'remove_from_cart',
            'get rid of this': 'remove_from_cart',
            'don\'t want this': 'remove_from_cart',
            'put this in my basket': 'add_to_cart',
            'i want to see clothing': 'search_by_category',
            'empty my basket': 'clear_cart',
            'remove everything': 'clear_cart',
            'start over': 'clear_cart',
            'delete all': 'clear_cart',
            'quantity 2 please': 'update_cart',
            'i want 3 of these': 'update_cart',
            
            # Profile phrases
            'show my profile': 'view_profile',
            'view my profile': 'view_profile',
            'my profile information': 'view_profile',
            'update my profile': 'update_profile',
            'edit my profile': 'update_profile',
            'change my profile': 'update_profile',
            'modify my profile': 'update_profile',
            'update personal info': 'update_profile',
            'edit personal info': 'update_profile',
            
            # Wishlist phrases
            'add to wishlist': 'add_to_wishlist',
            'save to wishlist': 'add_to_wishlist',
            'save for later': 'add_to_wishlist',
            'remove from wishlist': 'remove_from_wishlist',
            'delete from wishlist': 'remove_from_wishlist',
            'unsave this': 'remove_from_wishlist',
            'show my wishlist': 'view_wishlist',
            'view my wishlist': 'view_wishlist',
            'my wishlist': 'view_wishlist',
            'my saved items': 'view_wishlist',
            'saved for later': 'view_wishlist',
            'my favorites': 'view_wishlist',
            'add to favorites': 'add_to_wishlist',
            'add to my list': 'add_to_wishlist',
            'delete from favorites': 'remove_from_wishlist',
            'remove from my list': 'remove_from_wishlist',
            'remove from saved': 'remove_from_wishlist',
            'wishlist items': 'view_wishlist',
            'favorites list': 'view_wishlist',
            
            # Order phrases
            'show my orders': 'view_orders',
            'view my orders': 'view_orders',
            'my orders': 'view_orders',
            'order history': 'view_orders',
            'track my order': 'track_order',
            'where is my order': 'track_order',
            'order status': 'track_order',
            'tracking information': 'track_order',
            'package location': 'track_order',
            'delivery status': 'track_order',
            
            # Search phrases
            'show me electronics': 'search_by_category',
            'show me clothing': 'search_by_category',
            'show me beauty products': 'search_by_category',
            'browse electronics': 'search_by_category',
            'browse clothing': 'search_by_category',
            'browse home and garden': 'search_by_category',
            'what\'s new': 'browse_products',
            'what\'s popular': 'browse_products',
            'what\'s trending': 'browse_products',
            'new arrivals': 'browse_products',
            'popular items': 'browse_products',
            'featured products': 'browse_products',
            'i\'m looking for': 'search_products',
            'looking for a': 'search_products',
            'looking for': 'search_products',
            'what do you have in': 'search_by_category',
            'what\'s in the': 'search_by_category',
            'sports section': 'search_by_category',
            'electronics please': 'search_by_category',
            'clothing please': 'search_by_category',
            'home decor items': 'search_by_category',
            'show me what\'s popular': 'browse_products',
            'browse deals': 'browse_products',
            'what\'s on sale': 'browse_products',
            'what\'s new': 'browse_products',
            'what\'s trending': 'browse_products',
            'show only red items': 'filter_products',
            'show items with free shipping': 'filter_products',
            'under $50 please': 'filter_products',
            'only nike products': 'filter_products',
            'free shipping only': 'filter_products',
            'sort by price low to high': 'sort_products',
            'show cheapest first': 'sort_products',
            'sort by newest': 'sort_products',
            'sort by rating': 'sort_products',
            'sort by popularity': 'sort_products',
            'price ascending': 'sort_products',
            'newest first': 'sort_products',
            'best rated': 'sort_products',
            
            # Account phrases
            'log into my account': 'login',
            'access my account': 'login',
            'my account': 'login',
            'log out of my account': 'logout',
            'exit my account': 'logout',
            'sign up for an account': 'register',
            'create an account': 'register',
            'join the site': 'register',
            'view my account': 'view_profile',
            'my info': 'view_profile',
            'edit my information': 'update_profile',
            'change my details': 'update_profile',
            'modify my account': 'update_profile',
            'edit contact info': 'update_profile',
            'change my address': 'update_profile',
            'my past purchases': 'view_orders',
            'order list': 'view_orders',
            'order progress': 'track_order',
            'what do you mean': 'clarification',
            'what does that mean': 'clarification',
            'i have a question': 'faq',
            'need assistance': 'contact_support',
            'get me customer service': 'contact_support',
            'use my discount code': 'apply_coupon',
            'enter discount code': 'apply_coupon',
            'change payment method': 'select_payment',
            'change shipping option': 'select_shipping',
            'buy now': 'checkout',
            'place order': 'checkout',
            'i want a refund': 'refund',
            'refund this purchase': 'refund',
            'refund please': 'refund',
            'cancel and refund': 'refund',
            'what would you suggest': 'get_recommendations',
            'what\'s good': 'get_recommendations',
            'see you later': 'goodbye',
            'thanks that\'s all': 'goodbye',
            'have a good day': 'goodbye',
            'see you': 'goodbye',
            
            # Support phrases
            'contact customer support': 'contact_support',
            'get customer service': 'contact_support',
            'help desk': 'contact_support',
            'customer service please': 'contact_support',
            'support team': 'contact_support',
            'return this item': 'return_item',
            'return policy': 'return_item',
            'how to return': 'return_item',
            'request refund': 'refund',
            'get my money back': 'refund',
            'money back': 'refund',
            
            # Recommendation phrases
            'what do you recommend': 'get_recommendations',
            'suggest something for me': 'get_recommendations',
            'recommend products': 'get_recommendations',
            'suggest items': 'get_recommendations',
            'any recommendations': 'get_recommendations'
        }
        return phrase_intent_mapping.get(phrase)
    
    def _find_exact_matches(self, text: str) -> List[KeywordMatch]:
        """Find exact keyword matches."""
        matches = []
        words = text.split()
        
        # Use set for faster lookup
        seen_keywords = set()
        
        for word in words:
            if word in self.keyword_hashmap and word not in seen_keywords:
                seen_keywords.add(word)
                for metadata in self.keyword_hashmap[word]:
                    match = KeywordMatch(
                        keyword=word,
                        intent_name=metadata['intent_name'],
                        match_type='exact',
                        confidence=1.0,
                        start_pos=text.find(word),
                        end_pos=text.find(word) + len(word),
                        priority_weight=metadata['priority_weight']
                    )
                    matches.append(match)
        
        return matches
    
    def _find_partial_matches(self, text: str) -> List[KeywordMatch]:
        """Find partial keyword matches using trie."""
        matches = []
        trie_results = self.keyword_trie.search(text)
        
        for keyword, metadata in trie_results:
            # Skip if already found as exact match
            if keyword in self.keyword_hashmap:
                continue
            
            match = KeywordMatch(
                keyword=keyword,
                intent_name=metadata['intent_name'],
                match_type='partial',
                confidence=0.8,
                start_pos=text.find(keyword),
                end_pos=text.find(keyword) + len(keyword),
                priority_weight=metadata['priority_weight']
            )
            matches.append(match)
        
        return matches
    
    def _find_ngram_matches(self, tokens: List[str]) -> List[KeywordMatch]:
        """Find n-gram matches for multi-word phrases."""
        matches = []
        
        # Create 2-grams and 3-grams
        for n in [2, 3]:
            ngrams = self.preprocessor.create_ngrams(tokens, n)
            
            for ngram in ngrams:
                if ngram in self.keyword_hashmap:
                    for metadata in self.keyword_hashmap[ngram]:
                        match = KeywordMatch(
                            keyword=ngram,
                            intent_name=metadata['intent_name'],
                            match_type='exact',
                            confidence=1.0,
                            start_pos=0,  # Will be calculated properly in real implementation
                            end_pos=len(ngram),
                            priority_weight=metadata['priority_weight']
                        )
                        matches.append(match)
        
        return matches
    
    def _find_fuzzy_matches(self, text: str) -> List[KeywordMatch]:
        """Find fuzzy matches for typos and variations."""
        matches = []
        words = text.split()
        
        for word in words:
            # Simple fuzzy matching - look for words with 1-2 character differences
            for keyword in self.keyword_trie.get_all_keywords():
                if self._calculate_edit_distance(word, keyword) <= 2 and len(word) >= 3:
                    # Find metadata for this keyword
                    if keyword in self.keyword_hashmap:
                        for metadata in self.keyword_hashmap[keyword]:
                            match = KeywordMatch(
                                keyword=keyword,
                                intent_name=metadata['intent_name'],
                                match_type='fuzzy',
                                confidence=0.6,
                                start_pos=text.find(word),
                                end_pos=text.find(word) + len(word),
                                priority_weight=metadata['priority_weight']
                            )
                            matches.append(match)
        
        return matches
    
    def _calculate_edit_distance(self, s1: str, s2: str) -> int:
        """Calculate edit distance between two strings."""
        if len(s1) < len(s2):
            return self._calculate_edit_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _deduplicate_matches(self, matches: List[KeywordMatch]) -> List[KeywordMatch]:
        """Remove duplicate matches, keeping the best one."""
        seen = set()
        unique_matches = []
        
        for match in matches:
            key = (match.keyword, match.intent_name, match.match_type)
            if key not in seen:
                seen.add(key)
                unique_matches.append(match)
        
        return unique_matches
    
    def match_intent(self, user_input: str) -> Optional[MatchingResult]:
        """
        Match user input against keyword dictionaries and return intent.
        
        Args:
            user_input: The user's input text
            
        Returns:
            MatchingResult with intent information and confidence score
        """
        start_time = time.time()
        
        try:
            # Find all keyword matches
            matches = self._find_keyword_matches(user_input)
            
            if not matches:
                processing_time = (time.time() - start_time) * 1000
                self.processing_times.append(processing_time)
                return None
            
            # Group matches by intent
            intent_matches = defaultdict(list)
            for match in matches:
                intent_matches[match.intent_name].append(match)
            
            # Find the best intent based on confidence and match count
            best_intent = None
            best_confidence = 0
            best_matches = []
            
            for intent_name, intent_match_list in intent_matches.items():
                confidence = self._calculate_confidence_score(intent_match_list)
                
                # Boost confidence for intents with more matches
                match_count_boost = min(0.1, len(intent_match_list) * 0.02)
                final_confidence = min(1.0, confidence + match_count_boost)
                
                if final_confidence > best_confidence:
                    best_confidence = final_confidence
                    best_intent = intent_name
                    best_matches = intent_match_list
            
            if not best_intent:
                processing_time = (time.time() - start_time) * 1000
                self.processing_times.append(processing_time)
                return None
            
            # Get action code for the intent
            action_code = self._get_action_code_for_intent(best_intent)
            
            # Determine best match type
            best_match_type = max(best_matches, key=lambda x: x.confidence).match_type
            
            processing_time = (time.time() - start_time) * 1000
            self.processing_times.append(processing_time)
            
            # Update performance tracking
            self.match_counts[best_intent] += 1
            
            result = MatchingResult(
                intent_name=best_intent,
                action_code=action_code,
                confidence_score=best_confidence,
                matched_keywords=best_matches,
                processing_time_ms=processing_time,
                total_matches=len(matches),
                best_match_type=best_match_type,
                metadata={
                    'total_intents_considered': len(intent_matches),
                    'keyword_types_found': list(set(m.keyword for m in best_matches)),
                    'match_distribution': {m.match_type: sum(1 for x in best_matches if x.match_type == m.match_type) for m in best_matches}
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in keyword matching: {e}")
            processing_time = (time.time() - start_time) * 1000
            self.processing_times.append(processing_time)
            return None
    
    def _get_action_code_for_intent(self, intent_name: str) -> str:
        """Get action code for a given intent name."""
        # Comprehensive action code mapping - FIXED
        action_code_mapping = {
            # Search intents
            'search_products': 'SEARCH_PRODUCTS',
            'search_by_category': 'SEARCH_BY_CATEGORY',
            'browse_products': 'BROWSE_CATEGORIES',
            'filter_products': 'APPLY_FILTERS',
            'sort_products': 'SORT_PRODUCTS',
            
            # Product intents
            'get_product_info': 'GET_PRODUCT_DETAILS',
            'compare_products': 'COMPARE_PRODUCTS',
            
            # Cart intents
            'add_to_cart': 'ADD_ITEM_TO_CART',
            'remove_from_cart': 'REMOVE_ITEM_FROM_CART',
            'update_cart': 'UPDATE_CART_QUANTITY',
            'view_cart': 'VIEW_CART_CONTENTS',
            'clear_cart': 'CLEAR_CART_CONTENTS',
            
            # Checkout intents
            'checkout': 'INITIATE_CHECKOUT',
            'apply_coupon': 'APPLY_DISCOUNT_CODE',
            'remove_coupon': 'REMOVE_DISCOUNT_CODE',
            'select_payment': 'SELECT_PAYMENT_METHOD',
            'select_shipping': 'SELECT_SHIPPING_METHOD',
            
            # Account intents - FIXED MAPPINGS
            'login': 'USER_LOGIN',
            'logout': 'USER_LOGOUT',
            'register': 'USER_REGISTER',
            'view_profile': 'VIEW_USER_PROFILE',
            'update_profile': 'UPDATE_USER_PROFILE',  # FIXED: was UPDATE_CART_QUANTITY
            'view_orders': 'VIEW_ORDER_HISTORY',
            'track_order': 'TRACK_ORDER_STATUS',
            
            # Support intents
            'faq': 'GET_FAQ_ANSWER',
            'contact_support': 'CONTACT_CUSTOMER_SUPPORT',
            'complaint': 'SUBMIT_COMPLAINT',
            'return_item': 'INITIATE_RETURN',
            'refund': 'REQUEST_REFUND',
            
            # Recommendation intents - FIXED MAPPINGS
            'get_recommendations': 'GET_PERSONALIZED_RECOMMENDATIONS',
            'add_to_wishlist': 'ADD_TO_WISHLIST',
            'remove_from_wishlist': 'REMOVE_FROM_WISHLIST',  # FIXED: was REMOVE_ITEM_FROM_CART
            'view_wishlist': 'VIEW_WISHLIST',
            
            # General intents
            'greeting': 'SEND_GREETING',
            'goodbye': 'SEND_GOODBYE',
            'thanks': 'SEND_THANKS',
            'clarification': 'REQUEST_CLARIFICATION',
            'unknown': 'HANDLE_UNKNOWN_INTENT'
        }
        
        return action_code_mapping.get(intent_name, 'HANDLE_UNKNOWN_INTENT')
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if not self.processing_times:
            return {}
        
        processing_times = self.processing_times[-100:]  # Last 100 queries
        
        return {
            'avg_processing_time_ms': sum(processing_times) / len(processing_times),
            'max_processing_time_ms': max(processing_times),
            'min_processing_time_ms': min(processing_times),
            'queries_under_50ms': sum(1 for t in processing_times if t < 50),
            'queries_under_50ms_percentage': sum(1 for t in processing_times if t < 50) / len(processing_times) * 100,
            'total_queries_processed': len(self.processing_times),
            'most_matched_intents': dict(self.match_counts.most_common(10))
        }
    
    def clear_performance_stats(self):
        """Clear performance statistics."""
        self.processing_times.clear()
        self.match_counts.clear()


# Factory function for easy instantiation
def create_keyword_matcher() -> KeywordMatcher:
    """Create a new KeywordMatcher instance."""
    return KeywordMatcher()


# Example usage and testing
if __name__ == "__main__":
    # Create matcher
    matcher = create_keyword_matcher()
    
    # Test queries
    test_queries = [
        "I'm looking for a laptop",
        "Add this to my cart",
        "Show me my cart",
        "I want to checkout",
        "What's the price of this product?",
        "Compare these two phones",
        "Filter by price under $100",
        "Sort by newest first",
        "I need help with my order",
        "How do I return an item?",
        "Add to wishlist",
        "Show my wishlist",
        "Track my order",
        "View my orders",
        "Apply coupon code SAVE20",
        "Remove this from cart",
        "Update quantity to 2",
        "Clear my cart",
        "Pay with credit card",
        "Select free shipping",
        "Return this item",
        "Request refund",
        "Update my profile",
        "View my profile",
        "Logout",
        "Register new account",
        "What do you recommend?",
        "Remove from wishlist",
        "Browse electronics",
        "Search for smartphones",
        "Hello",
        "Goodbye",
        "Thank you",
        "I don't understand"
    ]
    
    print("🧪 Testing Keyword Matching Engine")
    print("=" * 50)
    
    for query in test_queries:
        result = matcher.match_intent(query)
        if result:
            print(f"✅ '{query}' -> {result.intent_name} ({result.action_code}) - Confidence: {result.confidence_score:.3f} - Time: {result.processing_time_ms:.2f}ms")
        else:
            print(f"❌ '{query}' -> No match found")
    
    # Show performance stats
    stats = matcher.get_performance_stats()
    print(f"\n📊 Performance Statistics:")
    print(f"Average processing time: {stats.get('avg_processing_time_ms', 0):.2f}ms")
    print(f"Queries under 50ms: {stats.get('queries_under_50ms_percentage', 0):.1f}%")
    print(f"Total queries processed: {stats.get('total_queries_processed', 0)}")
