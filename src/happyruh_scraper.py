import os
import time
import requests
import sys
from urllib.parse import urljoin
from datetime import datetime, timezone
from tqdm import tqdm
from db_logger.db import create_tables
from db_logger.crud import (
    upsert_raw_products_batch,
    create_pipeline_run,
    finish_pipeline_run,
)
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://happyruh.com"

# --- Keys / config from env ---
SF_TOKEN = os.getenv("SHOPIFY_STOREFRONT_TOKEN")
SF_DOMAIN = os.getenv("SHOPIFY_DOMAIN", "happyruh.com")
SF_API_VERSION = os.getenv("SHOPIFY_API_VERSION", "2024-07")

ADMIN_KEY = os.getenv("SHOPIFY_ADMIN_API_KEY")
ADMIN_PASS = os.getenv("SHOPIFY_ADMIN_PASSWORD")
ADMIN_SHOP = os.getenv("SHOPIFY_SHOP")  # e.g., 'happyruh'


# ---------- Path A: Shopify Storefront GraphQL ----------
def fetch_products_storefront_graphql():
    # print("Start fun")
    if not SF_TOKEN:
        print("no sf token")
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
            images(first: 5) { edges { node { src: url } } }
            variants(first: 1) { edges { node { price { amount currencyCode } } } }
          }
        }
        pageInfo { hasNextPage }
      }
    }
    """
    variables = {"cursor": None}
    out = []
    # print("before while")
    while True:
        # print("in while")
        resp = requests.post(url, headers=headers, json={"query": query, "variables": variables}, timeout=45)
        # print(resp)
        if resp.status_code != 200:
            print(f"Storefront GraphQL failed: {resp.status_code} {resp.text[:300]}")
            return out or None
        data = resp.json()
        edges = (((data or {}).get("data") or {}).get("products") or {}).get("edges") or []
        for e in edges:
            out.append(e["node"])
        page_info = (((data or {}).get("data") or {}).get("products") or {}).get("pageInfo") or {}
        # print(out)
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
        print(r)
        if r.status_code != 200:
            print(f"Admin REST failed: {r.status_code} {r.text[:300]}")
            return out or None
        data = r.json() or {}
        products = data.get("products") or []
        out.extend(products)
        if len(products) < limit:
            break
        page += 1
        time.sleep(0.25)
    print(out)
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


def main():
    """Main pipeline execution function."""
    run_id = None
    try:
        print("Attempting to create database tables...")
        create_tables()
        print("Tables created or already exist.")
        run_id = create_pipeline_run(pipeline_name='scraper')
        print(f"🏁 Starting scraper pipeline run #{run_id}")
    except Exception as e:
        print(f"❌ Pre-flight check failed: {e}")
        if run_id:
            finish_pipeline_run(run_id, 'error', error=str(e))
        sys.exit(1)

    error_message = None
    products_saved_count = 0
    try:
        # 1. Fetch products
        print("🛒 Fetching products from HappyRuH...")
        raw_products = None
        if SF_TOKEN:
            print("→ Using Shopify Storefront GraphQL")
            raw_products = fetch_products_storefront_graphql()
        if (not raw_products) and ADMIN_KEY and ADMIN_PASS and ADMIN_SHOP:
            print("→ Using Shopify Admin REST")
            raw_products = fetch_products_admin_rest()
        if not raw_products:
            print("→ Falling back to public JSON endpoints")
            raw_products = fetch_products_public_json()

        if not raw_products:
            raise RuntimeError("Failed to fetch products from any source.")

        if raw_products:
            original_columns = list(raw_products[0].keys())
            print("Original columns from scraper:", original_columns)

        # 2. Clean and de-duplicate products
        cleaned_products = raw_products
        
        seen_ids = set()
        unique_products = []
        for p in cleaned_products:
            pid_str = p.get("id")
            if isinstance(pid_str, str) and "gid://shopify/Product/" in pid_str:
                pid = int(pid_str.split('/')[-1])
                p['id'] = pid
            else:
                pid = p.get("id")

            if pid and pid not in seen_ids:
                seen_ids.add(pid)
                unique_products.append(p)
        
        print(f"✓ Found {len(unique_products)} unique products")

        # 3. Store products in PostgreSQL
        BATCH_SIZE = 100
        print(f"📦 Storing {len(unique_products)} products in PostgreSQL (batch size: {BATCH_SIZE})...")
        
        product_batch = []
        
        with tqdm(total=len(unique_products), desc="Upserting products") as pbar:
            for i, rp in enumerate(unique_products):
                pid = rp.get("id")
                if not pid:
                    pbar.update(1)
                    continue
                
                handle = rp.get("handle")
                url = urljoin(BASE_URL, f"/products/{handle}") if handle else None
                
                product_data = {
                    "id": pid,
                    "handle": handle,
                    "title": rp.get("title"),
                    "url": url,
                    "description": rp.get("descriptionHtml"),
                    "product_type": rp.get("productType"),
                    "images": rp.get("images"),
                    "variants": rp.get("variants"),
                    "product_json": rp,
                    "fetched_at": datetime.now(timezone.utc),
                }
                
                if i == 0:
                    print("Columns being saved to DB:", list(product_data.keys()))

                product_batch.append(product_data)
                
                # If batch is full or it's the last item, upsert the batch
                if len(product_batch) >= BATCH_SIZE or i == len(unique_products) - 1:
                    upsert_raw_products_batch(product_batch)
                    products_saved_count += len(product_batch)
                    product_batch = []
                
                pbar.update(1)
        
        print(f"✓ Stored {products_saved_count} products in PostgreSQL")

    except Exception as e:
        import traceback
        print(f"❌ An error occurred during the scraper pipeline: {e}")
        traceback.print_exc()
        error_message = str(e)
        sys.exit(1)

    finally:
        if run_id:
            status = 'error' if error_message else 'ok'
            finish_pipeline_run(run_id, status, products_raw_count=products_saved_count, error=error_message)
            print(f"✅ Scraper pipeline run #{run_id} finished with status: {status}")
        else:
            status = 'error' if error_message else 'ok'
            print(f"✅ Scraper finished with status: {status}")


if __name__ == "__main__":
    main()