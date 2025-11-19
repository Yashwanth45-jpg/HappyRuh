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
    from src.orchestrator.orchestrator import orchestrate_query
    logger.info("✅ Orchestrator imported successfully")
except Exception as e:
    logger.error(f"❌ Failed to import orchestrator: {e}", exc_info=True)
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
class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[list[ChatMessage]] = []

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
# ROUTE: CHAT (For simple chat interface with orchestrator)
# ----------------------------------------------------
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chat messages and return JSON response using orchestrator"""
    try:
        message = request.message.strip()
        logger.info(f"Received message: {message}")
        
        # Convert Pydantic models to dict for orchestrator
        chat_history = [{'role': msg.role, 'content': msg.content} for msg in request.history] if request.history else []
        logger.info(f"Chat history length: {len(chat_history)}")
        
        # Always use orchestrator - it will handle routing to Qwen or Llama based on search results
        if orchestrate_query is not None:
            logger.info(f"Using orchestrator for query: {message}")
            
            # Call orchestrator with chat history (returns HTML)
            html_response = orchestrate_query(
                user_query=message,
                chat_history=chat_history
            )
            
            # Extract price filters for product search
            price_filters = extract_price_filter(message)
            logger.info(f"Price filters: {price_filters}")
            
            # Perform semantic search for products to display in sidebar
            products = []
            try:
                if qdrant and embedder:
                    query_vector = embedder.encode(message).tolist()
                    
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
                    
                    # Search in Qdrant
                    search_results = qdrant.search(
                        collection_name=QDRANT_COLLECTION,
                        query_vector=query_vector,
                        query_filter=qdrant_filter,
                        limit=10
                    )
                    
                    logger.info(f"Found {len(search_results)} products")
                    
                    for idx, r in enumerate(search_results):
                        payload = r.payload or {}
                        product_id = payload.get("id") or f"product_{idx}_{int(time.time())}"
                        price = payload.get("price", 0)
                        if price is None:
                            price = 0
                        else:
                            try:
                                price = float(price)
                            except:
                                price = 0
                        
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
            except Exception as e:
                logger.error(f"Error searching products: {e}")
                products = []
            
            # Extract text from HTML response for display
            import re
            text_response = re.sub(r'<[^>]+>', '', html_response)
            text_response = text_response.strip()
            
            # Return response with products (if any)
            return ChatResponse(
                response=text_response,
                products=products,
                is_product_query=len(products) > 0
            )
        else:
            # Fallback if orchestrator not available
            return ChatResponse(
                response="I can help you find fragrances! Try asking about perfumes, colognes, or specific scents.",
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
