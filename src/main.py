# src/main.py
import os
import time
import uuid
import json
import logging
import threading
import re
from datetime import datetime
from typing import Optional

import psycopg2
import requests
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("HappyRuH-Backend")

# ----- Import orchestrator -----
try:
    from orchestrator.orchestrator import orchestrate_query
except Exception:
    orchestrate_query = None

# ----------------------------------------------------
# ENVIRONMENT CONFIG
# ----------------------------------------------------
POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql://ruh:ruhpass@localhost:5432/happyruh")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "semantic_collection")

EMBED_MODEL_NAME = os.getenv("EMBED_MODEL_NAME", "all-MiniLM-L6-v2")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

CRON_TIME = os.getenv("CRON_TIME", "03:10")

# ----------------------------------------------------
# INITIALIZE CLIENTS
# ----------------------------------------------------
app = FastAPI(title="HappyRuH Semantic Backend", version="1.0")

# Fix CORS - Add before routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

try:
    qdrant = QdrantClient(url=QDRANT_URL)
    embedder = SentenceTransformer(EMBED_MODEL_NAME)
    logger.info("✅ Qdrant and Embedder initialized")
except Exception as e:
    logger.warning(f"Failed to initialize Qdrant/Embedder: {e}")
    qdrant = None
    embedder = None


# ----------------------------------------------------
# UTILS: POSTGRES CONNECTION
# ----------------------------------------------------
def get_pg_conn():
    return psycopg2.connect(POSTGRES_DSN)


# ----------------------------------------------------
# UTILS: EXTRACT PRICE FILTER
# ----------------------------------------------------
def extract_price_filter(message: str) -> dict:
    """Extract price filters from user message"""
    filters = {"min_price": None, "max_price": None}
    
    # Pattern: "under X", "below X", "less than X"
    under_match = re.search(r'(?:under|below|less than)\s+(\d+)', message.lower())
    if under_match:
        filters["max_price"] = float(under_match.group(1))
    
    # Pattern: "above X", "over X", "more than X"
    over_match = re.search(r'(?:above|over|more than)\s+(\d+)', message.lower())
    if over_match:
        filters["min_price"] = float(over_match.group(1))
    
    # Pattern: "between X and Y"
    between_match = re.search(r'between\s+(\d+)\s+and\s+(\d+)', message.lower())
    if between_match:
        filters["min_price"] = float(between_match.group(1))
        filters["max_price"] = float(between_match.group(2))
    
    return filters


# ----------------------------------------------------
# PYDANTIC MODELS
# ----------------------------------------------------
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    products: list = []
    is_product_query: bool = False

class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 4
    session_id: Optional[str] = None


# ----------------------------------------------------
# ROUTE: HEALTH
# ----------------------------------------------------
@app.get("/health")
def health():
    try:
        if qdrant:
            _ = qdrant.get_collections()
        with get_pg_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1;")
        return {"status": "ok", "message": "Backend, Postgres, Qdrant healthy ✅"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ----------------------------------------------------
# ROUTE: CHAT (For simple chat interface)
# ----------------------------------------------------
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chat messages and return JSON response"""
    try:
        message = request.message.lower().strip()
        logger.info(f"Received message: {message}")
        
        # Simple greeting responses
        greetings = ["hi", "hello", "hey", "greetings"]
        if message in greetings:
            return ChatResponse(
                response="Hello! I'm your fragrance assistant. How can I help you find the perfect scent today?",
                products=[],
                is_product_query=False
            )
        
        # Check if it's a product-related query
        product_keywords = ["perfume", "fragrance", "scent", "cologne", "smell", "aroma", "product", "show", "find", "woody", "floral", "fresh", "oriental", "feel good", "stone"]
        
        if any(keyword in message for keyword in product_keywords):
            # Extract price filters
            price_filters = extract_price_filter(message)
            logger.info(f"Price filters: {price_filters}")
            
            # Perform semantic search
            if not qdrant or not embedder:
                logger.error("Qdrant or embedder not initialized")
                return ChatResponse(
                    response="Search service is currently unavailable. Please make sure Qdrant is running.",
                    products=[],
                    is_product_query=False
                )
            
            try:
                # Encode query
                query_vector = embedder.encode(message).tolist()
                logger.info(f"Generated embedding vector of size: {len(query_vector)}")
                
                # Build Qdrant filter
                qdrant_filter = None
                if price_filters["min_price"] is not None or price_filters["max_price"] is not None:
                    conditions = []
                    
                    if price_filters["min_price"] is not None:
                        conditions.append(
                            models.FieldCondition(
                                key="price",
                                range=models.Range(gte=price_filters["min_price"])
                            )
                        )
                    
                    if price_filters["max_price"] is not None:
                        conditions.append(
                            models.FieldCondition(
                                key="price",
                                range=models.Range(lte=price_filters["max_price"])
                            )
                        )
                    
                    qdrant_filter = models.Filter(must=conditions)
                    logger.info(f"Applied price filter: {qdrant_filter}")
                
                # Search in Qdrant with filters
                logger.info(f"Searching in collection: {QDRANT_COLLECTION}")
                search_results = qdrant.search(
                    collection_name=QDRANT_COLLECTION,
                    query_vector=query_vector,
                    query_filter=qdrant_filter,
                    limit=10
                )
                
                logger.info(f"Found {len(search_results)} results from Qdrant")
                
                if search_results and len(search_results) > 0:
                    products = []
                    for idx, r in enumerate(search_results):
                        try:
                            payload = r.payload or {}
                            
                            product_id = payload.get("id") or f"product_{idx}_{int(time.time())}"
                            
                            # Safely get price
                            price = payload.get("price")
                            if price is None:
                                price = 0
                            else:
                                try:
                                    price = float(price)
                                except (ValueError, TypeError):
                                    price = 0
                            
                            # Safely get images
                            images = payload.get("images", [])
                            if not isinstance(images, list):
                                images = []
                            
                            product = {
                                "id": str(product_id),
                                "title": str(payload.get("title", "Untitled Product")),
                                "description": str(payload.get("description", "No description available")),
                                "price": price,
                                "images": images,
                                "score": float(r.score)
                            }
                            products.append(product)
                            logger.info(f"Product {idx+1}: {product['title']} - ${product['price']} (Score: {product['score']:.3f})")
                        except Exception as product_error:
                            logger.error(f"Error processing product {idx}: {product_error}")
                            continue
                    
                    if len(products) > 0:
                        # Build response message
                        response_msg = f"I found {len(products)} fragrances"
                        if price_filters["max_price"]:
                            response_msg += f" under ${price_filters['max_price']}"
                        if price_filters["min_price"]:
                            response_msg += f" above ${price_filters['min_price']}"
                        response_msg += " matching your search:"
                        
                        return ChatResponse(
                            response=response_msg,
                            products=products,
                            is_product_query=True
                        )
                
                # No results found
                filter_msg = ""
                if price_filters["max_price"]:
                    filter_msg = f" under ${price_filters['max_price']}"
                elif price_filters["min_price"]:
                    filter_msg = f" above ${price_filters['min_price']}"
                
                return ChatResponse(
                    response=f"I couldn't find any products{filter_msg} matching '{message}'. Try different keywords like 'perfume', 'cologne', or 'fragrance'.",
                    products=[],
                    is_product_query=True
                )
                
            except Exception as search_error:
                logger.error(f"Search error: {str(search_error)}")
                import traceback
                traceback.print_exc()
                
                return ChatResponse(
                    response=f"Sorry, I encountered an error while searching. Error: {str(search_error)}",
                    products=[],
                    is_product_query=False
                )
        else:
            return ChatResponse(
                response="I can help you find fragrances! Try asking about perfumes, colognes, or specific scents. You can also specify a price range like 'under 500' or 'between 100 and 300'.",
                products=[],
                is_product_query=False
            )
            
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return ChatResponse(
            response="Sorry, I encountered an unexpected error. Please try again or rephrase your question.",
            products=[],
            is_product_query=False
        )


# ----------------------------------------------------
# ROUTE: API QUERY (For orchestrator)
# ----------------------------------------------------
@app.post("/api/query")
async def api_query(req: QueryRequest, request: Request):
    """POST /api/query"""
    try:
        if orchestrate_query is not None:
            result_html = orchestrate_query(req.query)
            return {"status": "ok", "response": result_html}
        else:
            demo_response = "I can help you find fragrances! Try asking about perfumes or scents."
            return {"status": "ok", "response": demo_response}
    except Exception as e:
        logger.error(f"API query error: {str(e)}")
        return {"status": "error", "response": str(e)}


# ----------------------------------------------------
# MAIN ENTRY
# ----------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
