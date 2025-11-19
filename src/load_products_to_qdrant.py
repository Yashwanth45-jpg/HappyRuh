"""
Loads products from JSON into Qdrant with semantic embeddings.
Now with fast LLM summarization for descriptions.
"""

import os
import json
import re
from pathlib import Path
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv

# Import the fast summarizer
from llm_summarizer import summarize_description, summarize_batch
from db_logger.crud import fetch_all_raw_products


def strip_html(html_text: str) -> str:
    """Remove HTML tags and clean up text."""
    if not html_text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', html_text)
    
    # Decode HTML entities
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    text = text.replace('&nbsp;', ' ')
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

load_dotenv()

# Configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "semantic_collection")
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL_NAME", "all-MiniLM-L6-v2")

# Test mode - process all products
TEST_MODE = False
TEST_PRODUCT_LIMIT = 10

# Initialize
print("🔄 Loading embedding model...")
embedder = SentenceTransformer(EMBED_MODEL_NAME)
qdrant = QdrantClient(url=QDRANT_URL, prefer_grpc=False)
print("✅ Model and client ready")


def create_collection():
    """Create or recreate the Qdrant collection"""
    try:
        qdrant.delete_collection(QDRANT_COLLECTION)
        print(f"🗑️ Deleted existing collection '{QDRANT_COLLECTION}'")
    except Exception:
        print(f"ℹ️ Collection '{QDRANT_COLLECTION}' doesn't exist yet")
    
    qdrant.create_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config=models.VectorParams(
            size=384,  # all-MiniLM-L6-v2 embedding size
            distance=models.Distance.COSINE,
        ),
    )
    print(f"✅ Created collection '{QDRANT_COLLECTION}'")


def load_products():
    """Load products from JSON file"""
    # json_path = Path(__file__).parent / "data" / "happyruh_products.json"
    
    # if not json_path.exists():
    #     print(f"❌ Product file not found: {json_path}")
    #     return []
    
    # with open(json_path, 'r', encoding='utf-8') as f:
    #     products = json.load(f)

    products = fetch_all_raw_products()
    
    print(f"✅ Loaded {len(products)} products from JSON")
    # Test mode - limit products
    if TEST_MODE:
        products = products[:TEST_PRODUCT_LIMIT]
        print(f"🧪 TEST MODE: Processing only {len(products)} products")
    
    return products


def upload_products_with_summarization(products, use_fast_summarization=True):
    """Upload products to Qdrant with LLM-generated summaries"""
    points = []
    
    # Collect all descriptions for batch processing
    if use_fast_summarization:
        print(f"\n📝 Generating summaries for {len(products)} products...")
        # Extract and clean HTML descriptions first
        descriptions = []
        for p in products:
            html_desc = p.get("body_html", "") or p.get("description", "")
            clean_desc = strip_html(html_desc)
            descriptions.append(clean_desc)
        
        # Batch summarize (tries Qwen first, falls back to Ollama)
        summaries = summarize_batch(descriptions, prefer_fast=True)
        print(f"✅ Generated {len(summaries)} summaries")
    else:
        summaries = []
    
    # Process each product
    for idx, product in enumerate(products):
        product_id = str(product.get("id", ""))
        title = product.get("title", "Unknown Product")
        
        # Get price from first variant
        price_str = "0"
        variants = product.get("variants", [])
        if variants and len(variants) > 0:
            price_str = variants[0].get("price", "0")
        
        try:
            price = float(price_str)
        except:
            price = 0.0
        
        # Get description (Shopify uses body_html) and strip HTML tags
        html_description = product.get("body_html", "") or product.get("description", "")
        full_description = strip_html(html_description)
        
        # Use summarized description with fallback
        if use_fast_summarization:
            description = summaries[idx] if summaries[idx] and summaries[idx] != "..." else full_description
        else:
            description = full_description
        
        # Get product images
        images = []
        product_images = product.get("images", [])
        for img in product_images:
            if isinstance(img, dict):
                img_url = img.get("src", "")
                if img_url:
                    images.append(img_url)
        
        # Create text for embedding
        embed_text = f"{title}. {description}"
        
        print(f"\n📦 {idx + 1}/{len(products)}: {title}")
        print(f"   💰 Price: ₹{price}")
        print(f"   📝 Summary: {description[:100]}...")
        print(f"   🔄 Generating embedding...")
        
        # Generate embedding
        embedding = embedder.encode(embed_text).tolist()
        
        # Create point with sequential ID (Qdrant-safe)
        # Use idx+1 as the point ID, store original product_id in payload
        point = models.PointStruct(
            id=idx + 1,  # Sequential integer ID for Qdrant
            vector=embedding,
            payload={
                "id": product_id,  # Original product ID stored in payload
                "title": title,
                "description": description,  # Store description (summarized or full)
                "description_full": full_description,  # Keep original body_html
                "price": price,
                "images": images,
                "product_type": product.get("product_type", ""),
                "vendor": product.get("vendor", ""),
            }
        )
        
        points.append(point)
        print(f"   ✅ Embedded successfully")
    
    # Upload to Qdrant
    if points:
        print(f"\n📤 Uploading {len(points)} products to Qdrant...")
        qdrant.upsert(
            collection_name=QDRANT_COLLECTION,
            points=points,
        )
        print(f"✅ Upload complete!")


def verify_collection():
    """Verify the collection was created successfully"""
    collection_info = qdrant.get_collection(QDRANT_COLLECTION)
    print(f"\n✅ Collection verified:")
    print(f"   Name: {QDRANT_COLLECTION}")
    print(f"   Points: {collection_info.points_count}")
    print(f"   Vector size: {collection_info.config.params.vectors.size}")
    
    # Sample search
    print(f"\n🔍 Testing semantic search...")
    test_query = "confident perfume for party"
    query_vector = embedder.encode(test_query).tolist()
    
    results = qdrant.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=query_vector,
        limit=3,
    )
    
    print(f"\nTop 3 results for '{test_query}':")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.payload.get('title', 'Unknown')}")
        print(f"   Score: {result.score:.3f}")
        print(f"   Price: ₹{result.payload.get('price', 0)}")
        print(f"   Description: {result.payload.get('description', '')[:100]}...")


if __name__ == "__main__":
    print("🚀 Starting Qdrant product loader with fast summarization...\n")
    
    # Create collection
    create_collection()
    
    # Load products
    products = load_products()
    
    if products:
        # Upload WITH summarization (Qwen will generate 3-sentence summaries)
        upload_products_with_summarization(products, use_fast_summarization=True)
        
        # Verify
        verify_collection()
        
        print("\n✅ All done! Products loaded with LLM-generated summaries.")
    else:
        print("❌ No products to load")