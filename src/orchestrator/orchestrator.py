# src/orchestrator/orchestrator.py
import os
import json
import logging
import re
import uuid
from typing import List, Tuple, Optional, Dict
from pathlib import Path
from sentence_transformers import SentenceTransformer
from .llm_connector import generate_response, get_llm_connector

# Import intent classifier
try:
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
    from intent_classifier.keyword_matcher import KeywordMatcher
    from intent_classifier import IntentCategory, ActionCode
    
    # Initialize keyword matcher
    _keyword_matcher = KeywordMatcher()
    INTENT_CLASSIFIER_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Intent classifier not available: {e}")
    INTENT_CLASSIFIER_AVAILABLE = False
    _keyword_matcher = None

# Qdrant imports for filtering
try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    models = None

# Configure logging
logger = logging.getLogger("Orchestrator")

# Initialize embedding model (local)
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
_emb_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "semantic_collection")

# Try Qdrant, fallback to local JSON
_qdrant = None
try:
    from qdrant_client import QdrantClient
    _qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    _qdrant.get_collections()
except Exception:
    _qdrant = None

# Load products from JSON as fallback
_products_cache = None

def _load_products():
    global _products_cache
    if _products_cache is not None:
        return _products_cache
    try:
        # Try the scraped products first, then fallback to happyruh_products
        json_path = Path(__file__).parent.parent / "data" / "scraped_products.json"
        if not json_path.exists():
            json_path = Path(__file__).parent.parent / "data" / "happyruh_products.json"
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Handle both formats: { "count": ..., "products": [...] } and just [...]
                if isinstance(data, dict) and "products" in data:
                    _products_cache = data["products"]
                elif isinstance(data, list):
                    _products_cache = data
                else:
                    _products_cache = []
                return _products_cache
    except Exception as e:
        print(f"Error loading products: {e}")
    return []

def _semantic_search_local(query: str, top_k: int = 4) -> str:
    """
    Fallback: Search products locally using embeddings and cosine similarity.
    """
    products = _load_products()
    if not products:
        return ""
    
    # Extract price filters
    min_price, max_price = _extract_price_filters(query)
    
    # Filter products by price if specified
    if min_price is not None or max_price is not None:
        filtered_products = []
        for product in products:
            # Extract price from product
            variants = product.get("variants", [])
            product_price = None
            if variants:
                try:
                    product_price = float(variants[0].get("price", 0))
                except:
                    pass
            
            # Apply price filters
            if min_price is not None and (product_price is None or product_price < min_price):
                continue
            if max_price is not None and (product_price is None or product_price > max_price):
                continue
                
            filtered_products.append(product)
        products = filtered_products
    
    # Encode query
    query_vector = _emb_model.encode(query).tolist()
    
    # Score products
    scored = []
    for product in products:
        # Create searchable text from product
        title = product.get("title", "")
        body_html = product.get("body_html", "")
        product_type = product.get("product_type", "")
        
        # Simple text preprocessing (remove HTML tags)
        text = f"{title} {product_type}".strip()
        if not text:
            continue
        
        try:
            # Encode product text
            text_vector = _emb_model.encode(text).tolist()
            
            # Compute cosine similarity
            dot_product = sum(a * b for a, b in zip(query_vector, text_vector))
            norm_q = sum(a * a for a in query_vector) ** 0.5
            norm_t = sum(a * a for a in text_vector) ** 0.5
            
            if norm_q > 0 and norm_t > 0:
                similarity = dot_product / (norm_q * norm_t)
                scored.append((similarity, product))
        except Exception:
            continue
    
    # Sort by similarity and get top_k (with deduplication)
    scored.sort(reverse=True)
    
    # Format as text context - with full product details (deduplicated)
    pieces = []
    seen_products = set()  # Track unique product IDs
    
    for score, product in scored:
        product_id = product.get("product_id") or product.get("id")
        title = product.get("title", "Unknown")
        body = product.get("body_html", "")[:300]
        product_type = product.get("product_type", "")
        
        # CRITICAL: Use ONLY product_id for deduplication (not title)
        if not product_id:
            continue  # Skip if no product ID
        
        if product_id in seen_products:
            continue  # Skip duplicates based on product_id only
        
        seen_products.add(product_id)
        variants = product.get("variants", [])
        price = None
        if variants:
            try:
                price = float(variants[0].get("price", 0))
            except:
                pass
        
        # Build product string with all details
        product_str = f"Product: {title}"
        if product_id:
            product_str += f"\nID: {product_id}"
        if product_type:
            product_str += f"\nType: {product_type}"
        if price:
            product_str += f"\nPrice: ₹{price}"
        else:
            product_str += f"\nPrice: Price on request"
        if body:
            product_str += f"\nDescription: {body}"
        
        pieces.append(product_str)
        
        # Stop once we have enough unique products
        if len(pieces) >= top_k:
            break
    
    return "\n\n".join(pieces)

def semantic_search(query: str, top_k: int = 4) -> str:
    """
    Query Qdrant if available, otherwise use local JSON search.
    Returns full product details (deduplicated).
    """
    # Extract potential filters from query
    min_price, max_price = _extract_price_filters(query)
    
    if _qdrant and QDRANT_AVAILABLE and models:
        try:
            vector = _emb_model.encode(query).tolist()
            
            logger.info(f"Searching Qdrant with query: {query}")
            
            # Build filter conditions
            filter_conditions = []
            
            # Add price filters if specified
            if min_price is not None or max_price is not None:
                price_conditions = []
                if min_price is not None and models:
                    price_conditions.append(models.FieldCondition(
                        key="price",
                        range=models.Range(gte=min_price)
                    ))
                if max_price is not None and models:
                    price_conditions.append(models.FieldCondition(
                        key="price",
                        range=models.Range(lte=max_price)
                    ))
                filter_conditions.extend(price_conditions)
                logger.info(f"Applied price filters: min={min_price}, max={max_price}")
            
            # Perform search with filters
            search_params = {"collection_name": QDRANT_COLLECTION, "query_vector": vector, "limit": top_k * 3}
            if filter_conditions and models:
                search_params["query_filter"] = models.Filter(must=filter_conditions)
                
            hits = _qdrant.search(**search_params)
            logger.info(f"Qdrant returned {len(hits)} results")
            
            pieces: List[str] = []
            seen_products = set()  # Track unique product IDs
            
            for idx, h in enumerate(hits):
                payload = getattr(h, "payload", {}) or {}
                
                # Try multiple field names for compatibility
                title = payload.get("title") or payload.get("product_name") or ""
                price = payload.get("price")
                product_id = payload.get("id") or payload.get("product_id") or ""
                product_type = payload.get("product_type") or payload.get("type") or ""
                description = payload.get("description") or ""
                
                logger.info(f"Product {idx}: id={product_id}, title={title[:50] if title else 'N/A'}")
                
                # Skip if no product ID
                if not product_id:
                    logger.warning(f"Skipping product {idx}: no product_id")
                    continue
                
                # Skip duplicates
                if product_id in seen_products:
                    logger.info(f"Skipping duplicate product_id: {product_id}")
                    continue
                
                # Add to results if has title
                if title:
                    seen_products.add(product_id)
                    product_str = f"Product: {title}"
                    if product_id:
                        product_str += f"\nID: {product_id}"
                    if product_type:
                        product_str += f"\nType: {product_type}"
                    if price:
                        product_str += f"\nPrice: ₹{price}"
                    else:
                        product_str += f"\nPrice: Price on request"
                    if description:
                        product_str += f"\nDescription: {description[:300]}"
                    pieces.append(product_str)
                    logger.info(f"Added product {idx} to results")
                    
                    # Stop once we have enough unique products
                    if len(pieces) >= top_k:
                        break
                else:
                    logger.warning(f"Skipping product {idx}: no title")
            
            logger.info(f"Final result: {len(pieces)} products formatted")
            return "\n\n".join(pieces)
        except Exception as e:
            logger.error(f"Qdrant search failed: {e}", exc_info=True)
            pass
    
    # Fallback to local search
    return _semantic_search_local(query, top_k)


def _extract_price_filters(query: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Extract price filters from query.
    Supports patterns like "under 500", "above 1000", "between 500 and 1000", etc.
    Returns (min_price, max_price) tuple where None means no filter.
    """
    query_lower = query.lower()
    
    # Pattern 1: "under X", "below X", "less than X"
    under_patterns = [r'\b(under|below|less than)\s*(\d+(?:\.\d+)?)', r'\b(\d+(?:\.\d+)?)\s*(?:or\s*)?(?:less|under|below)']
    for pattern in under_patterns:
        match = re.search(pattern, query_lower)
        if match:
            max_price = float(match.group(2) if len(match.groups()) >= 2 and match.group(2) else match.group(1))
            return (None, max_price)
    
    # Pattern 2: "above X", "over X", "more than X"
    above_patterns = [r'\b(above|over|more than)\s*(\d+(?:\.\d+)?)', r'\b(\d+(?:\.\d+)?)\s*(?:or\s*)?(?:more|above|over)']
    for pattern in above_patterns:
        match = re.search(pattern, query_lower)
        if match:
            min_price = float(match.group(2) if len(match.groups()) >= 2 and match.group(2) else match.group(1))
            return (min_price, None)
    
    # Pattern 3: "between X and Y"
    between_match = re.search(r'\b(between)\s*(\d+(?:\.\d+)?)\s*(?:and|to)\s*(\d+(?:\.\d+)?)', query_lower)
    if between_match:
        min_price = float(between_match.group(2))
        max_price = float(between_match.group(3))
        return (min_price, max_price)
    
    # Pattern 4: "X to Y"
    range_match = re.search(r'\b(\d+(?:\.\d+)?)\s*(?:to|-)\s*(\d+(?:\.\d+)?)', query_lower)
    if range_match:
        min_price = float(range_match.group(1))
        max_price = float(range_match.group(2))
        return (min_price, max_price)
    
    return (None, None)


# LLM-based intent classifier for fallback
def _classify_intent_with_llm(query: str, context: dict = None) -> Optional[Dict]:
    """
    Use LLM to classify intent for unknown or low-confidence queries.
    Uses direct Ollama API call with a focused classification prompt.
    Returns dict with category, confidence, needs_clarification, and reasoning.
    """
    try:
        import requests
        
        # Dedicated intent classification prompt (not the conversational master prompt)
        classification_prompt = f"""Classify this e-commerce query. If NOT about shopping → UNKNOWN.

Categories:
SEARCH = wants products | ADD_TO_CART = add to cart | CHECKOUT = buy now | VIEW_CART = see cart | VIEW_ORDERS = order history
GREETING = only "hi"/"hello" | GOODBYE = only "bye" | THANKS = only "thanks" | FAQ = policies | ACCOUNT = login/register
UNKNOWN = anything NOT shopping (weather, jokes, parties, events, personal chat)

Examples:
"show me perfumes" → CATEGORY: SEARCH | NEEDS_CLARIFICATION: false | REASONING: Wants products
"hello" → CATEGORY: GREETING | NEEDS_CLARIFICATION: false | REASONING: Simple greeting
"what's the weather" → CATEGORY: UNKNOWN | NEEDS_CLARIFICATION: false | REASONING: Not about shopping
"I'm going to a party" → CATEGORY: UNKNOWN | NEEDS_CLARIFICATION: false | REASONING: Personal statement, not shopping

Query: "{query}"

Classify (format: CATEGORY: X | NEEDS_CLARIFICATION: true/false | REASONING: brief):"""

        # Call Ollama API directly with minimal settings for classification
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
        
        payload = {
            "model": ollama_model,
            "prompt": classification_prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Low temperature for consistent classification
                "top_p": 0.9,
                "max_tokens": 100,  # Short response
                "stop": ["\n\n", "User query:"]
            }
        }
        
        response = requests.post(
            f"{ollama_url}/api/generate",
            json=payload,
            timeout=15
        )
        response.raise_for_status()
        
        llm_output = response.json().get('response', '').strip()
        logger.info(f"LLM intent classification output: {llm_output[:200]}")
        
        # Parse structured response (supports both newline and pipe formats)
        category = None
        needs_clarification = False
        reasoning = ""
        
        # Try pipe-separated format first
        if '|' in llm_output:
            parts = llm_output.split('|')
            for part in parts:
                part = part.strip()
                if 'CATEGORY:' in part:
                    category = part.replace('CATEGORY:', '').strip().upper()
                elif 'NEEDS_CLARIFICATION:' in part:
                    clarification_str = part.replace('NEEDS_CLARIFICATION:', '').strip().lower()
                    needs_clarification = clarification_str in ['true', 'yes', '1']
                elif 'REASONING:' in part:
                    reasoning = part.replace('REASONING:', '').strip()
        else:
            # Try newline format
            for line in llm_output.split('\n'):
                line = line.strip()
                if line.startswith('CATEGORY:'):
                    category = line.replace('CATEGORY:', '').strip().upper()
                elif line.startswith('NEEDS_CLARIFICATION:'):
                    clarification_str = line.replace('NEEDS_CLARIFICATION:', '').strip().lower()
                    needs_clarification = clarification_str in ['true', 'yes', '1']
                elif line.startswith('REASONING:'):
                    reasoning = line.replace('REASONING:', '').strip()
        
        # Validate category
        valid_categories = ['SEARCH', 'ADD_TO_CART', 'CHECKOUT', 'VIEW_CART', 'VIEW_ORDERS',
                           'GREETING', 'GOODBYE', 'THANKS', 'FAQ', 'ACCOUNT', 'UNKNOWN']
        
        if category and category in valid_categories:
            # Confidence based on category and clarity
            if category == 'UNKNOWN':
                confidence = 0.9  # High confidence that it's NOT e-commerce
            elif needs_clarification:
                confidence = 0.6  # Medium confidence, ambiguous
            else:
                confidence = 0.8  # Good confidence
            
            return {
                'category': category,
                'confidence': confidence,
                'needs_clarification': needs_clarification,
                'reasoning': reasoning,
                'strategy': 'llm_classification'
            }
        else:
            # Fallback parsing - look for category keywords in response
            response_upper = llm_output.upper()
            for cat in valid_categories:
                if cat in response_upper:
                    return {
                        'category': cat,
                        'confidence': 0.7,
                        'needs_clarification': False,
                        'reasoning': llm_output[:100],
                        'strategy': 'llm_classification'
                    }
            
            # Default to UNKNOWN
            return {
                'category': 'UNKNOWN',
                'confidence': 0.5,
                'needs_clarification': False,
                'reasoning': llm_output[:100],
                'strategy': 'llm_classification'
            }
            
    except Exception as e:
        logger.warning(f"LLM intent classification failed: {e}")
        return None


# Hybrid intent classification with LLM fallback
def classify_intent(query: str, use_hybrid: bool = True, context: dict = None):
    """
    Hybrid intent classification combining keyword matching and LLM.
    
    Strategy (Options A+B+C combined):
    1. Try keyword matching first (fast)
    2. If confidence >= 0.85: Accept result (Option A)
    3. If confidence 0.70-0.85: Flag for clarification (Option B)
    4. If confidence < 0.70: Use LLM validation (Option C)
    5. If no keyword match: Use LLM classification (Option C)
    
    Args:
        query: User's input text
        use_hybrid: Enable LLM fallback for low confidence
        context: Additional context (chat history, etc.)
    """
    if not _keyword_matcher:
        return None
    
    from types import SimpleNamespace
    
    # STEP 1: Try keyword matching first
    match_result = _keyword_matcher.match_intent(query)
    
    # STEP 2: Check if we got a match
    if not match_result:
        # Option C: No keyword match - use LLM if hybrid enabled
        if use_hybrid:
            logger.info("No keyword match found, falling back to LLM classification")
            llm_result = _classify_intent_with_llm(query, context)
            
            if llm_result:
                try:
                    category = IntentCategory[llm_result['category']]
                except KeyError:
                    category = IntentCategory.UNKNOWN
                
                return SimpleNamespace(
                    category=category,
                    action_code=ActionCode.SEARCH_PRODUCTS,
                    confidence=llm_result['confidence'],
                    entities={},
                    metadata={
                        'strategy': 'llm_fallback',
                        'needs_clarification': False,
                        'reasoning': llm_result.get('reasoning', ''),
                        'processing_time_ms': 0
                    }
                )
        
        # Return unknown if LLM failed or not enabled
        return SimpleNamespace(
            category=IntentCategory.UNKNOWN,
            action_code=ActionCode.SEARCH_PRODUCTS,
            confidence=0.0,
            entities={},
            metadata={'strategy': 'keyword_matching', 'needs_clarification': False}
        )
    
    # STEP 3: We have a keyword match - check confidence and match type
    confidence = match_result.confidence_score
    match_type = match_result.best_match_type
    
    # Map intent_name to IntentCategory
    intent_name = match_result.intent_name.upper().replace(" ", "_")
    try:
        category = IntentCategory[intent_name]
    except KeyError:
        category = IntentCategory.SEARCH if "search" in intent_name.lower() else IntentCategory.UNKNOWN
    
    # Map action_code string to ActionCode enum
    action_code_str = match_result.action_code.upper()
    try:
        action_code = ActionCode[action_code_str]
    except KeyError:
        action_code = ActionCode.SEARCH_PRODUCTS
    
    # Extract entities from matched keywords
    entities = {}
    
    # ADJUSTED LOGIC: Be more aggressive with fuzzy matches
    # For fuzzy matches, use stricter threshold (0.85 instead of 0.70)
    # This prevents false positives like "birthday party" → LOGIN
    
    if match_type == 'fuzzy':
        # Fuzzy matches need higher confidence
        if confidence >= 0.85:
            threshold_high = True
            threshold_medium = False
            threshold_low = False
        else:
            # All fuzzy matches < 0.85 should use LLM validation
            threshold_high = False
            threshold_medium = False
            threshold_low = True
    else:
        # Exact and partial matches use normal thresholds
        threshold_high = confidence >= 0.85
        threshold_medium = 0.70 <= confidence < 0.85
        threshold_low = confidence < 0.70
    
    # OPTION A: High confidence threshold (>= 0.85) - Accept result
    if threshold_high:
        logger.info(f"High confidence ({confidence:.2f}) - accepting keyword match: {category.value}")
        return SimpleNamespace(
            category=category,
            action_code=action_code,
            confidence=confidence,
            entities=entities,
            metadata={
                'strategy': 'keyword_matching',
                'needs_clarification': False,
                'processing_time_ms': match_result.processing_time_ms,
                'matched_keywords': [m.keyword for m in match_result.matched_keywords],
                'total_matches': match_result.total_matches,
                'best_match_type': match_result.best_match_type
            }
        )
    
    # OPTION B: Medium confidence (0.70-0.85) - Add clarification flag
    elif threshold_medium:
        logger.info(f"Medium confidence ({confidence:.2f}) - may need clarification: {category.value}")
        
        # Generate clarification message
        clarification_msg = None
        if match_result.best_match_type == 'fuzzy':
            clarification_msg = f"I think you want to {category.value.lower().replace('_', ' ')}, but I'm not entirely sure. Could you clarify?"
        
        return SimpleNamespace(
            category=category,
            action_code=action_code,
            confidence=confidence,
            entities=entities,
            metadata={
                'strategy': 'keyword_matching',
                'needs_clarification': True,
                'clarification_message': clarification_msg,
                'processing_time_ms': match_result.processing_time_ms,
                'matched_keywords': [m.keyword for m in match_result.matched_keywords],
                'total_matches': match_result.total_matches,
                'best_match_type': match_result.best_match_type
            }
        )
    
    # OPTION C: Low confidence (< 0.70) OR fuzzy match < 0.85 - Use LLM validation if hybrid enabled
    else:
        logger.info(f"Low confidence ({confidence:.2f}) or fuzzy match - using LLM validation")
        
        if use_hybrid:
            llm_result = _classify_intent_with_llm(query, context)
            
            # Use LLM result if:
            # 1. LLM has higher confidence, OR
            # 2. LLM says UNKNOWN (indicates false positive), OR
            # 3. Fuzzy match with low confidence (< 0.80)
            should_use_llm = (
                llm_result and (
                    llm_result['confidence'] > confidence or  # LLM more confident
                    llm_result['category'] == 'UNKNOWN' or    # LLM detected non-ecommerce query
                    (match_type == 'fuzzy' and confidence < 0.80)  # Low confidence fuzzy match
                )
            )
            
            if should_use_llm:
                logger.info(f"Using LLM classification: {llm_result['category']} (confidence: {llm_result['confidence']:.2f}, keyword was: {category.value} @ {confidence:.2f})")
                
                try:
                    llm_category = IntentCategory[llm_result['category']]
                except KeyError:
                    llm_category = IntentCategory.UNKNOWN
                
                # Use LLM's needs_clarification flag
                llm_needs_clarification = llm_result.get('needs_clarification', False)
                clarification_msg = None
                if llm_needs_clarification:
                    clarification_msg = f"I classified this as {llm_category.value.lower().replace('_', ' ')}, but I'm not entirely sure. {llm_result.get('reasoning', '')}"
                
                return SimpleNamespace(
                    category=llm_category,
                    action_code=ActionCode.SEARCH_PRODUCTS,
                    confidence=llm_result['confidence'],
                    entities=entities,
                    metadata={
                        'strategy': 'hybrid_llm_validation',
                        'needs_clarification': llm_needs_clarification,
                        'clarification_message': clarification_msg,
                        'reasoning': llm_result.get('reasoning', ''),
                        'keyword_match': category.value,
                        'keyword_confidence': confidence,
                        'processing_time_ms': match_result.processing_time_ms
                    }
                )
        
        # Fallback: return keyword result with clarification flag
        return SimpleNamespace(
            category=category,
            action_code=action_code,
            confidence=confidence,
            entities=entities,
            metadata={
                'strategy': 'keyword_matching_low_confidence',
                'needs_clarification': True,
                'clarification_message': f"I'm not very confident about this. Did you mean to {category.value.lower().replace('_', ' ')}?",
                'processing_time_ms': match_result.processing_time_ms,
                'matched_keywords': [m.keyword for m in match_result.matched_keywords],
                'total_matches': match_result.total_matches,
                'best_match_type': match_result.best_match_type
            }
        )


def orchestrate_query(
    user_query: str, 
    user_id: str = "anonymous", 
    session_id: str = "default",
    chat_history: List[Dict[str, str]] = None
) -> str:
    """
    Full pipeline:
      - classify intent
      - perform semantic search
      - call LLM with context and conversation history
      - return clean, product-focused HTML
      
    Args:
        user_query: The user's current message
        user_id: User identifier for logging
        session_id: Session identifier for logging
        chat_history: List of previous messages [{'role': 'user'/'assistant', 'content': '...'}]
    """
    logger.info(f"--- Orchestrator processing query: '{user_query}'")
    
    # 1. CLASSIFY INTENT
    intent_result = None
    if INTENT_CLASSIFIER_AVAILABLE:
        try:
            # Use hybrid mode for better accuracy (falls back to keyword-only if embeddings unavailable)
            intent_result = classify_intent(user_query, use_hybrid=True, context={
                'chat_history': chat_history,
                'session_id': session_id,
                'user_id': user_id
            })
            
            logger.info(f"Intent classified: {intent_result.category.value} (action: {intent_result.action_code.value}, confidence: {intent_result.confidence:.2f})")
            logger.info(f"Classification strategy: {intent_result.metadata.get('strategy', 'unknown')}")
            logger.info(f"Extracted entities: {intent_result.entities}")
            
            # Check if clarification is needed (only for keyword-based classification)
            # If LLM was used, let it handle clarification in the response
            if intent_result.metadata.get('needs_clarification'):
                strategy = intent_result.metadata.get('strategy', '')
                # Only return early clarification for keyword-based matches
                if strategy not in ['llm_classification', 'hybrid_llm_validation']:
                    clarification = intent_result.metadata.get('clarification_message')
                    if clarification:
                        return f'<div style="padding: 15px;"><p>{clarification}</p></div>'
            
            # Handle specific intents with quick responses
            if intent_result.category == IntentCategory.GREETING:
                return '<div style="padding: 15px;"><p>Hello! 👋 Welcome to HappyRuh. I\'m here to help you find the perfect fragrance or crystal. What are you looking for today?</p></div>'
            
            if intent_result.category == IntentCategory.GOODBYE:
                return '<div style="padding: 15px;"><p>Thank you for visiting HappyRuh! Feel free to come back anytime. Have a great day! 🌟</p></div>'
            
            if intent_result.category == IntentCategory.THANKS:
                return '<div style="padding: 15px;"><p>You\'re welcome! Happy to help. Is there anything else you\'d like to know? 😊</p></div>'
                
        except Exception as e:
            logger.warning(f"Intent classification failed: {e}")
            intent_result = None

    QUEUE_CONVO_PATH = os.getenv("CONVO_HIST_QUEUE_PATH", None)
    query_id = str(uuid.uuid4())
    queue_id = None  # Will store the ID returned from the queue endpoint
    
    logger.info(f"Generated query_id: {query_id}")
    logger.info(f"QUEUE_CONVO_PATH: {QUEUE_CONVO_PATH}")
    
    if QUEUE_CONVO_PATH:
        try:
            import requests
            payload = {
                "id": query_id,
                "user_id": user_id,
                "session_id": session_id,
                "query": user_query
            }
            logger.info(f"Attempting to POST to: {QUEUE_CONVO_PATH}")
            logger.info(f"Payload: {payload}")
            
            resp = requests.post(QUEUE_CONVO_PATH, json=payload, timeout=10)
            resp.raise_for_status()
            
            # Extract queue_id from response
            try:
                response_data = resp.json()
                queue_id = response_data.get("queue_id") or response_data.get("id") or query_id
                logger.info(f"Successfully queued conversation. Status: {resp.status_code}, queue_id: {queue_id}")
                logger.info(f"Queue response: {response_data}")
            except:
                # If response is not JSON or doesn't have queue_id, use query_id
                queue_id = query_id
                logger.info(f"Successfully queued conversation. Status: {resp.status_code}, using query_id as fallback")
                
        except Exception as e:
            logger.error(f"Failed to queue conversation history: {str(e)}", exc_info=True)
            queue_id = query_id  # Fallback to query_id
    else:
        logger.warning("QUEUE_CONVO_PATH not set in environment variables")
        queue_id = query_id
            
    logger.info(f"Using queue_id for completion: {queue_id}")
    
    try:
        # 2. Use extracted entities for better search
        # If intent classifier extracted price filters or product type, use them
        min_price, max_price = _extract_price_filters(user_query)
        
        # Override with intent entities if available
        if intent_result and intent_result.entities:
            if 'min_price' in intent_result.entities:
                min_price = intent_result.entities['min_price']
            if 'max_price' in intent_result.entities:
                max_price = intent_result.entities['max_price']
            
            logger.info(f"Using intent entities: min_price={min_price}, max_price={max_price}")
        
        # Search for relevant products
        logger.info("Starting semantic search...")
        context = semantic_search(user_query, top_k=4)
        
        # Extract product details from context for better display
        if not context.strip():
            logger.warning("No products found in search results")
            return '<div style="text-align: center; padding: 20px; color: #9ca3af;"><p>No products found. Try searching for different terms.</p></div>'
        
        logger.info(f"Found products context (length: {len(context)} chars)")
        
        # Initialize conversation history if not provided
        if chat_history is None:
            chat_history = []
        
        # Prepare intent metadata to pass to LLM (only if LLM was used for classification)
        intent_metadata = None
        if intent_result and intent_result.metadata.get('strategy') in ['llm_classification', 'hybrid_llm_validation']:
            intent_metadata = {
                'needs_clarification': intent_result.metadata.get('needs_clarification', False),
                'reasoning': intent_result.metadata.get('reasoning', ''),
                'strategy': intent_result.metadata.get('strategy', ''),
                'confidence': intent_result.confidence,
                'category': intent_result.category.value
            }
            logger.info(f"Passing intent metadata to LLM: {intent_metadata}")
        
        # Call LLM to generate response using new chat-based approach
        logger.info("Calling LLM to generate response with chat history...")
        llm_connector = get_llm_connector()
        llm_response = llm_connector.get_chat_response(
            user_message=user_query,
            chat_history=chat_history,
            search_results=context,
            intent_metadata=intent_metadata
        )
        logger.info(f"LLM response generated (length: {len(llm_response)} chars)")
        
        # Wrap in clean container
        final_html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">
            <div style="margin-bottom: 20px;">
                {llm_response}
            </div>
        </div>
        """
        logger.info("Final HTML response prepared")
        print("Final HTML length:", len(final_html))
        # Store completion
        if QUEUE_CONVO_PATH and queue_id:
            try:
                import requests
                # Build the correct completion path using queue_id
                # QUEUE_CONVO_PATH should be like "http://localhost:1234/api/conversations/queue"
                # Completion endpoint: /api/conversations/queue/{queue_id}/complete
                if QUEUE_CONVO_PATH.endswith('/queue'):
                    path = f"{QUEUE_CONVO_PATH}/{queue_id}/complete"
                else:
                    # If path doesn't end with /queue, append the full path
                    base_path = QUEUE_CONVO_PATH.rstrip('/')
                    path = f"{base_path}/api/conversations/queue/{queue_id}/complete"
                
                payload = {
                    "ai_response": final_html,
                    "model_used": "ollama",
                    "tokens_used": 0
                }
                logger.info(f"Attempting to POST completion to: {path}")
                logger.info(f"Completion payload keys: {list(payload.keys())}")
                
                resp = requests.post(path, json=payload, timeout=10)
                
                # Log response details
                logger.info(f"Completion response status: {resp.status_code}")
                logger.info(f"Completion response body: {resp.text[:500]}")
                
                resp.raise_for_status()
                
                logger.info(f"Successfully stored completion. Status: {resp.status_code}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to store conversation completion - Request error: {str(e)}", exc_info=True)
                logger.error(f"Request URL was: {path}")
                logger.error(f"Response (if any): {getattr(e.response, 'text', 'No response')[:500]}")
            except Exception as e:
                logger.error(f"Failed to store conversation completion - Unexpected error: {str(e)}", exc_info=True)
        else:
            logger.warning("QUEUE_CONVO_PATH not set or queue_id not available, skipping completion storage")
            
        return final_html
    except Exception as e:
        logger.error(f"Error in orchestrator: {str(e)}", exc_info=True)
        return f'<div style="color: #fca5a5; padding: 15px; background: rgba(252, 165, 165, 0.1); border-radius: 8px;"><p><b>Error:</b> {str(e)[:150]}</p></div>'
