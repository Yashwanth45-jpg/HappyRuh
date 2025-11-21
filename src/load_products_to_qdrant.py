"""
Loads products into Qdrant with both TEXT + IMAGE embeddings.
Uses fast LLM summarization (Qwen/Ollama) for descriptions.
"""

import os
import json
import re
import io
import requests
from pathlib import Path
from PIL import Image
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv

# Import summarizer + DB products
from llm_summarizer import summarize_description, summarize_batch
from db_logger.crud import fetch_all_raw_products


# ----------------------------------------------------
# CLEAN HTML
# ----------------------------------------------------
def strip_html(html_text: str) -> str:
    if not html_text:
        return ""
    text = re.sub(r'<[^>]+>', ' ', html_text)
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&quot;', '"').replace('&#39;', "'").replace('&nbsp;', ' ')
    return re.sub(r'\s+', ' ', text).strip()


# ----------------------------------------------------
# ENV
# ----------------------------------------------------
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "semantic_collection")

TEXT_EMBED_MODEL = os.getenv("EMBED_MODEL_NAME", "all-MiniLM-L6-v2")
IMAGE_EMBED_MODEL = "clip-ViT-B-32"

TEXT_VECTOR_SIZE = 384
IMAGE_VECTOR_SIZE = 512


# ----------------------------------------------------
# INIT MODELS + QDRANT
# ----------------------------------------------------
print("🔄 Loading text + image embedding models...")
embedder_text = SentenceTransformer(TEXT_EMBED_MODEL)
embedder_image = SentenceTransformer(IMAGE_EMBED_MODEL)

qdrant = QdrantClient(url=QDRANT_URL, prefer_grpc=False)
print("✅ Models and Qdrant ready")


# ----------------------------------------------------
# DOWNLOAD IMAGE
# ----------------------------------------------------
def download_image(url: str):
    """Download image safely and return PIL Image"""
    if not url:
        return None
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return Image.open(io.BytesIO(resp.content)).convert("RGB")
    except Exception:
        return None


# ----------------------------------------------------
# CREATE COLLECTION (TEXT + IMAGE VECTORS)
# ----------------------------------------------------
def create_collection():
    """Delete + recreate collection with multi-vector support"""
    try:
        qdrant.delete_collection(QDRANT_COLLECTION)
        print(f"🗑 Deleted old collection {QDRANT_COLLECTION}")
    except:
        print("ℹ No previous collection found")

    qdrant.create_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config={
            "text": models.VectorParams(size=TEXT_VECTOR_SIZE, distance=models.Distance.COSINE),
            "image": models.VectorParams(size=IMAGE_VECTOR_SIZE, distance=models.Distance.COSINE),
        }
    )
    print("✅ Created new collection with TEXT + IMAGE vectors")


# ----------------------------------------------------
# LOAD PRODUCTS (FROM POSTGRES)
# ----------------------------------------------------
def load_products():
    products = fetch_all_raw_products()
    print(f"📦 Loaded {len(products)} products from PostgreSQL")
    products = [
        p for p in products
        if p.get("product_type", "").lower() not in ["ticket", "event"]
    ]
    print(f"✔ {len(products)} products after filtering")

    return products


# ----------------------------------------------------
# MAIN: Embed + Upload to Qdrant
# ----------------------------------------------------
def upload_products_with_summarization(products):
    points = []

    # 1️⃣ First generate summaries for all products
    descriptions = []
    for p in products:
        clean = strip_html(p.get("body_html", "") or p.get("description", ""))
        descriptions.append(clean)

    print("📝 Generating text summaries...")
    summaries = summarize_batch(descriptions, prefer_fast=True)

    # 2️⃣ Process each product
    for idx, product in enumerate(products):
        print(f"\n--- Processing {idx+1}/{len(products)} ---")

        product_id = str(product.get("id"))
        title = product.get("title", "Unknown")

        # Clean full description
        html_desc = product.get("body_html", "") or product.get("description", "")
        full_description = strip_html(html_desc)

        # Choose summary
        summary = summaries[idx] if summaries[idx] else full_description

        # PRICE
        variants = product.get("variants", [])
        price = float(variants[0].get("price", 0)) if variants else 0

        # IMAGES (take first)
        images = [img.get("src") for img in product.get("images", []) if isinstance(img, dict)]
        image_url = images[0] if images else None

        # ------------------------------
        # TEXT EMBEDDING
        # ------------------------------
        embed_text = f"{title}. {summary}"
        text_vector = embedder_text.encode(embed_text).tolist()

        # ------------------------------
        # IMAGE EMBEDDING
        # ------------------------------
        if image_url:
            img = download_image(image_url)
            if img:
                image_vector = embedder_image.encode(img).tolist()
            else:
                image_vector = [0] * IMAGE_VECTOR_SIZE
        else:
            image_vector = [0] * IMAGE_VECTOR_SIZE

        try:
            point_id = int(product_id)
        except:
            point_id = idx + 1    

        # ------------------------------
        # CREATE POINT
        # ------------------------------
        point = models.PointStruct(
            id=point_id,
            vector={
                "text": text_vector,
                "image": image_vector
            },
            payload={
                "id": product_id,
                "title": title,
                "description": summary,
                "description_full": full_description,
                "price": price,
                "images": images,
                "vendor": product.get("vendor", ""),
                "product_type": product.get("product_type", ""),
            }
        )

        points.append(point)
        print(f"   ✓ Embedded text + image")

    # Upload to Qdrant
    print("\n📤 Uploading all vectors to Qdrant...")
    qdrant.upsert(collection_name=QDRANT_COLLECTION, points=points)
    print("✅ Upload completed")


# ----------------------------------------------------
# VERIFY
# ----------------------------------------------------
def verify_collection():
    info = qdrant.get_collection(QDRANT_COLLECTION)
    print("\n📚 Collection Verified")
    print(f"   Points: {info.points_count}")
    print(f"   Vectors: {info.config.params.vectors}")


# ----------------------------------------------------
# ENTRY
# ----------------------------------------------------
if __name__ == "__main__":
    print("🚀 Starting multi-modal Qdrant loader...\n")

    create_collection()
    products = load_products()

    if products:
        upload_products_with_summarization(products)
        verify_collection()
        print("\n✅ All done — text + image embeddings stored!")
    else:
        print("❌ No products found")