# src/orchestrator/orchestrator.py
import os
import json
import logging
import re
from typing import List, Tuple, Optional
from pathlib import Path
from sentence_transformers import SentenceTransformer
from .llm_connector import generate_response

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
            
            # Perform search with filters
            search_params = {"collection_name": QDRANT_COLLECTION, "query_vector": vector, "limit": top_k * 3}
            if filter_conditions and models:
                search_params["query_filter"] = models.Filter(must=filter_conditions)
                
            hits = _qdrant.search(**search_params)
            pieces: List[str] = []
            seen_products = set()  # Track unique product names
            
            for h in hits:
                payload = getattr(h, "payload", {}) or {}
                title = payload.get("product_name") or payload.get("title") or ""
                price = payload.get("price")
                product_id = payload.get("product_id")
                product_type = payload.get("type") or ""
                description = payload.get("description") or ""
                
                # CRITICAL: Use ONLY product_id for deduplication (not title)
                if not product_id:
                    continue  # Skip if no product ID
                
                if product_id in seen_products:
                    continue  # Skip duplicates based on product_id only
                
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
                    
                    # Stop once we have enough unique products
                    if len(pieces) >= top_k:
                        break
            
            return "\n\n".join(pieces)
        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
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


def orchestrate_query(user_query: str) -> str:
    """
    Full pipeline:
      - perform semantic search
      - call LLM with context
      - return clean, product-focused HTML
    """
    logger.info(f"--- Orchestrator processing query: '{user_query}'")
    
    try:
        # Search for relevant products
        logger.info("Starting semantic search...")
        context = semantic_search(user_query, top_k=4)
        
        # Extract product details from context for better display
        if not context.strip():
            logger.warning("No products found in search results")
            return '<div style="text-align: center; padding: 20px; color: #9ca3af;"><p>No products found. Try searching for different terms.</p></div>'
        
        logger.info(f"Found products context (length: {len(context)} chars)")
        
        # Call LLM to generate response
        logger.info("Calling LLM to generate response...")
        llm_html = generate_response(user_query, context)
        logger.info(f"LLM response generated (length: {len(llm_html)} chars)")
        
        # Wrap in clean container
        final_html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">
            <div style="margin-bottom: 20px;">
                {llm_html}
            </div>
        </div>
        """
        logger.info("Final HTML response prepared")
        return final_html
    except Exception as e:
        logger.error(f"Error in orchestrator: {str(e)}", exc_info=True)
        return f'<div style="color: #fca5a5; padding: 15px; background: rgba(252, 165, 165, 0.1); border-radius: 8px;"><p><b>Error:</b> {str(e)[:150]}</p></div>'
