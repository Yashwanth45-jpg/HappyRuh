"""
Load HappyRuH products from JSON into Qdrant vector database.
This enables semantic search across product data.
"""

import json
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models
import time
import uuid
import logging

# Import data cleaner functions
from data_cleaner import clean_text, parse_price_value, remove_unwanted_fields

# Import LLM summarizer
try:
    from llm_summarizer import summarize_description
    USE_SUMMARIZER = True
    print("✅ LLM Summarizer loaded")
except ImportError as e:
    USE_SUMMARIZER = False
    print(f"⚠️ LLM Summarizer not available: {e}")

# Configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "semantic_collection")
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL_NAME", "all-MiniLM-L6-v2")

# Initialize clients
embedder = SentenceTransformer(EMBED_MODEL_NAME)
qdrant = QdrantClient(url=QDRANT_URL, prefer_grpc=False)

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_products():
    """Load products from JSON file."""
    json_path = Path(__file__).parent / "data" / "happyruh_products.json"
    
    if not json_path.exists():
        print(f"❌ Product file not found: {json_path}")
        return []
    
    with open(json_path, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    print(f"✅ Loaded {len(products)} products from JSON")
    
    # Clean products using data_cleaner
    cleaned_products = [remove_unwanted_fields(p) for p in products]
    print(f"✅ Cleaned {len(cleaned_products)} products")
    
    return cleaned_products


def create_or_recreate_collection():
    """Create collection if it doesn't exist, or recreate it."""
    try:
        # Delete existing collection to start fresh
        qdrant.delete_collection(QDRANT_COLLECTION)
        print(f"🗑️ Deleted existing collection '{QDRANT_COLLECTION}'")
    except Exception:
        pass
    
    # Create new collection
    print(f"📦 Creating new collection '{QDRANT_COLLECTION}'...")
    qdrant.create_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config=models.VectorParams(
            size=384,  # all-MiniLM-L6-v2 embedding size
            distance=models.Distance.COSINE,
        ),
    )
    print(f"✅ Collection created")


def embed_and_store_products(products):
    """Embed products and store in Qdrant."""
    if not products:
        print("❌ No products to embed")
        return
    
    points = []
    
    for idx, product in enumerate(products, 1):
        try:
            # Extract product information
            product_id = str(product.get("id", idx))
            title = product.get("title", "Unknown Product")
            body_html = product.get("body_html", "")
            
            # Use data_cleaner to clean the description
            # This removes HTML, markdown, hashtags, etc.
            raw_description = clean_text(body_html)
            
            # Use LLM to summarize description if available
            if USE_SUMMARIZER and raw_description:
                print(f"   Summarizing product {idx}: {title[:50]}...")
                description = summarize_description(raw_description)
            else:
                description = raw_description[:500] if raw_description else "No description available"
            
            # Extract and parse price from variants using data_cleaner
            price = 0.0
            variants = product.get("variants", [])
            if variants and len(variants) > 0:
                price_raw = variants[0].get("price", "0")
                parsed_price = parse_price_value(price_raw)
                price = parsed_price if parsed_price is not None else 0.0
            
            # Extract images
            images = []
            
            # Check for 'image' field (single image)
            single_image = product.get("image")
            if single_image and isinstance(single_image, dict):
                img_src = single_image.get("src", "")
                if img_src:
                    images.append(img_src)
            
            # Check for 'images' field (multiple images)
            product_images = product.get("images", [])
            for img in product_images:
                if isinstance(img, dict):
                    img_src = img.get("src", "")
                    if img_src and img_src not in images:  # Avoid duplicates
                        images.append(img_src)
            
            # Create searchable text combining title and clean description
            search_text = f"{title}. {description}"
            
            # Generate embedding
            embedding = embedder.encode(search_text).tolist()
            
            # Create point for Qdrant with clean payload
            point = models.PointStruct(
                id=str(uuid.uuid4()),  # Use UUID for Qdrant point ID
                vector=embedding,
                payload={
                    "id": product_id,
                    "title": title,
                    "description": description,  # Clean description (no HTML/markdown/hashtags)
                    "price": price,
                    "images": images,
                    "product_type": product.get("product_type", ""),
                    "vendor": product.get("vendor", ""),
                    "handle": product.get("handle", ""),
                }
            )
            points.append(point)
            
            if idx % 5 == 0:
                print(f"   Processed {idx}/{len(products)} products...")
        
        except Exception as e:
            print(f"⚠️ Error processing product {idx}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    if not points:
        print("❌ No points to store")
        return
    
    print(f"\n📤 Uploading {len(points)} product embeddings to Qdrant...")
    
    # Upload points to Qdrant in batches
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i+batch_size]
        qdrant.upsert(
            collection_name=QDRANT_COLLECTION,
            points=batch,
        )
        print(f"   Uploaded batch {i//batch_size + 1}/{(len(points)-1)//batch_size + 1}")
    
    print(f"✅ Successfully stored {len(points)} products in Qdrant")


def verify_search():
    """Test semantic search with sample queries."""
    print("\n🔍 Testing semantic search...")
    
    test_queries = [
        "perfume products",
        "floral fragrance for women",
        "palm stones for healing",
    ]
    
    for query in test_queries:
        query_vector = embedder.encode(query).tolist()
        results = qdrant.search(
            collection_name=QDRANT_COLLECTION,
            query_vector=query_vector,
            limit=2,
        )
        
        print(f"\n📝 Query: '{query}'")
        for result in results:
            payload = result.payload
            if payload is not None:
                title = payload.get('title', 'Unknown')
                price = payload.get('price', 0)
                desc = payload.get('description', '')[:100]
                print(f"   • {title} - ${price}")
                print(f"     {desc}...")
                print(f"     (Score: {result.score:.3f})")
            else:
                print(f"   • Product (Score: {result.score:.3f}")


if __name__ == "__main__":
    print("🚀 Loading HappyRuH products into Qdrant...\n")
    
    # Load and clean products from JSON
    products = load_products()
    
    if products:
        # Create/verify collection
        create_or_recreate_collection()
        
        # Embed and store products
        embed_and_store_products(products)
        
        # Verify search works
        verify_search()
        
        print("\n✅ Product loading complete!")
    else:
        print("❌ Failed to load products")