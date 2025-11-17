import os
import json
import time
import requests
from urllib.parse import urljoin
from db import ensure_tables, upsert_raw
from data_cleaner import clean_text, parse_price_value, remove_unwanted_fields
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer
import numpy as np

BASE_URL = "https://happyruh.com"

# --- Keys / config from env ---
SF_TOKEN = os.getenv("SHOPIFY_STOREFRONT_TOKEN")
SF_DOMAIN = os.getenv("SHOPIFY_DOMAIN", "happyruh.com")
SF_API_VERSION = os.getenv("SHOPIFY_API_VERSION", "2024-07")

ADMIN_KEY = os.getenv("SHOPIFY_ADMIN_API_KEY")
ADMIN_PASS = os.getenv("SHOPIFY_ADMIN_PASSWORD")
ADMIN_SHOP = os.getenv("SHOPIFY_SHOP")  # e.g., 'happyruh'

# --- Qdrant setup ---
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "semantic_collection")
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL_NAME", "all-MiniLM-L6-v2")
VECTOR_SIZE = 384

qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, prefer_grpc=False, timeout=180)
embedder = SentenceTransformer(EMBED_MODEL_NAME)


def ensure_collection_exists():
    """Ensure Qdrant collection exists"""
    collections = qdrant.get_collections().collections
    names = [c.name for c in collections]
    if QDRANT_COLLECTION not in names:
        qdrant.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE),
        )


def embed_texts(texts):
    if not texts:
        return np.empty((0, VECTOR_SIZE), dtype=np.float32)
    embs = embedder.encode(texts, show_progress_bar=False)
    return np.asarray(embs, dtype=np.float32)


# ---------- Path A: Shopify Storefront GraphQL ----------
def fetch_products_storefront_graphql():
    if not SF_TOKEN:
        return None
    url = f"https://{SF_DOMAIN}/api/{SF_API_VERSION}/graphql.json"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Storefront-Access-Token": SF_TOKEN,
    }
    query = """
    query getProducts($cursor: String) {
      products(first: 250, after: $cursor) {
        edges {
          cursor
          node {
            id
            handle
            title
            descriptionHtml
            productType
            images(first: 1) { edges { node { src: url } } }
            variants(first: 1) { edges { node { price { amount currencyCode } } } }
          }
        }
        pageInfo { hasNextPage }
      }
    }
    """
    variables = {"cursor": None}
    out = []
    while True:
        resp = requests.post(url, headers=headers, json={"query": query, "variables": variables}, timeout=45)
        if resp.status_code != 200:
            print("Storefront GraphQL failed:", resp.status_code, resp.text[:300])
            return out or None
        data = resp.json()
        edges = (((data or {}).get("data") or {}).get("products") or {}).get("edges") or []
        for e in edges:
            n = e["node"]
            price = None
            v_edges = (((n.get("variants") or {}).get("edges")) or [])
            if v_edges:
                p = v_edges[0]["node"]["price"]
                if p and p.get("amount"):
                    price = p["amount"]
            img = None
            i_edges = (((n.get("images") or {}).get("edges")) or [])
            if i_edges:
                img = i_edges[0]["node"].get("src")

            out.append({
                "id": int(abs(hash(n["id"])) % 10**12),
                "handle": n.get("handle"),
                "title": n.get("title"),
                "body_html": n.get("descriptionHtml"),
                "product_type": n.get("productType"),
                "image": {"src": img} if img else None,
                "variants": [{"price": price}] if price else [],
            })
        page_info = (((data or {}).get("data") or {}).get("products") or {}).get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        variables["cursor"] = edges[-1]["cursor"]
        time.sleep(0.25)
    return out


# ---------- Path B: Shopify Admin REST ----------
def build_admin_base():
    if not (ADMIN_KEY and ADMIN_PASS and ADMIN_SHOP):
        return None
    shop = ADMIN_SHOP
    if not shop.endswith(".myshopify.com"):
        shop = f"{shop}.myshopify.com"
    return f"https://{ADMIN_KEY}:{ADMIN_PASS}@{shop}/admin/api/{SF_API_VERSION}"


def fetch_products_admin_rest(limit=250, max_pages=40):
    base = build_admin_base()
    if not base:
        return None
    out, page = [], 1
    while page <= max_pages:
        url = f"{base}/products.json"
        params = {"limit": str(limit), "page": str(page)}
        r = requests.get(url, params=params, timeout=45)
        if r.status_code != 200:
            print("Admin REST failed:", r.status_code, r.text[:300])
            return out or None
        data = r.json() or {}
        products = data.get("products") or []
        out.extend(products)
        if len(products) < limit:
            break
        page += 1
        time.sleep(0.25)
    return out


# ---------- Path C: Public JSON (fallback) ----------
def get_json(url, params=None, retry=3, sleep=0.8):
    for i in range(retry):
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, params=params, timeout=30)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 503):
                time.sleep(sleep * (i + 1))
                continue
        except Exception:
            time.sleep(sleep * (i + 1))
    return None


def fetch_products_public_json(limit=250, max_pages=40):
    all_products, page = [], 1
    while page <= max_pages:
        url = urljoin(BASE_URL, "/products.json")
        data = get_json(url, params={"limit": str(limit), "page": str(page)})
        if not data or not isinstance(data, dict) or not data.get("products"):
            break
        products = data["products"]
        all_products.extend(products)
        if len(products) < limit:
            break
        page += 1
        time.sleep(0.25)
    return all_products


# ---------- Main runner ----------
if __name__ == "__main__":
    # Try to ensure database tables, but don't fail if DB is unavailable
    try:
        ensure_tables()
        print("✓ Database tables ready")
        db_available = True
    except Exception as e:
        print(f"⚠️ Database unavailable: {e}")
        print("   Will save to JSON file instead\n")
        db_available = False
    
    try:
        ensure_collection_exists()
        print("✓ Qdrant collection ready")
    except Exception as e:
        print(f"⚠️ Qdrant unavailable: {e}\n")
    
    print("🛒 Fetching products from HappyRuH...")

    raw_products = None

    # 1) Try Storefront GraphQL
    if SF_TOKEN:
        print("→ Using Shopify Storefront GraphQL")
        raw_products = fetch_products_storefront_graphql()

    # 2) Else try Admin REST
    if (not raw_products) and ADMIN_KEY and ADMIN_PASS and ADMIN_SHOP:
        print("→ Using Shopify Admin REST")
        raw_products = fetch_products_admin_rest()

    # 3) Else fallback to public JSON
    if not raw_products:
        print("→ Falling back to public JSON endpoints")
        raw_products = fetch_products_public_json()

    # --- Clean products: Remove unwanted fields like tags ---
    if raw_products:
        raw_products = [remove_unwanted_fields(p) for p in raw_products]
        print(f"📋 Cleaned {len(raw_products)} products (removed unwanted fields)")
        
        # Remove duplicates based on product ID
        seen_ids = set()
        unique_products = []
        for p in raw_products:
            pid = p.get("id")
            if pid and pid not in seen_ids:
                seen_ids.add(pid)
                unique_products.append(p)
        
        if len(unique_products) < len(raw_products):
            print(f"🔄 Removed {len(raw_products) - len(unique_products)} duplicate products")
        
        raw_products = unique_products
        print(f"✓ {len(raw_products)} unique products ready for indexing")

    # --- Save directly to Postgres and Qdrant ---
    count = 0
    payloads, texts = [], []

    for rp in raw_products or []:
        pid = rp.get("id")
        handle = rp.get("handle")
        title = rp.get("title") or ""
        desc = clean_text(rp.get("body_html") or "")
        url = urljoin(BASE_URL, f"/products/{handle}") if handle else None
        price = None
        if rp.get("variants"):
            price = parse_price_value(rp["variants"][0].get("price"))

        # 1️⃣ Store in Postgres (if available)
        if db_available:
            try:
                upsert_raw({"id": pid, "handle": handle, "title": title, "url": url, "json": rp})
            except Exception as e:
                print(f"Warning: Could not store product {pid} in DB: {e}")

        # 2️⃣ Prepare for Qdrant
        text = f"Product: {title}. Price: {price or 'N/A'}. Description: {desc[:200]}"
        payloads.append({
            "product_id": pid,
            "type": "product",
            "source": "happyruh_scraper",
            "product_name": title,
            "price": price,
            "url": url,
            "description": desc,
        })
        texts.append(text)
        count += 1

    if texts:
        try:
            # Clear existing entries with same product_ids to avoid duplicates
            if payloads:
                product_ids = [str(p["product_id"]) for p in payloads if p.get("product_id")]
                if product_ids:
                    # Delete points with matching product_ids
                    qdrant.delete(
                        collection_name=QDRANT_COLLECTION,
                        points_selector=models.FilterSelector(
                            filter=models.Filter(
                                must=[
                                    models.FieldCondition(
                                        key="product_id",
                                        match=models.MatchAny(any=product_ids)
                                    )
                                ]
                            )
                        )
                    )
                    print(f"🧹 Cleared {len(product_ids)} existing product entries from Qdrant")
            
            vectors = embed_texts(texts)
            points = [
                models.PointStruct(id=i + 1, vector=vectors[i].tolist(), payload=payloads[i])
                for i in range(len(texts))
            ]
            qdrant.upsert(collection_name=QDRANT_COLLECTION, points=points)
            print(f"✓ Stored {count} products in Qdrant")
        except Exception as e:
            print(f"⚠️ Could not store in Qdrant: {e}")
    
    # Save to JSON file as backup
    try:
        json_output = {
            "count": count,
            "products": payloads,
            "texts": texts
        }
        with open("src/data/scraped_products.json", "w", encoding="utf-8") as f:
            json.dump(json_output, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved {count} products to src/data/scraped_products.json")
    except Exception as e:
        print(f"⚠️ Could not save to JSON: {e}")
    
    print(f"\n✅ Scraping complete! Processed {count} products.") 
