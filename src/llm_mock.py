"""
Smart LLM Mock Service with Qdrant Integration
Provides intelligent responses using vector database context
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import logging
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("LLM-Mock")

app = FastAPI(title="LLM Mock Service", version="1.0")

# Configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "semantic_collection")
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL_NAME", "all-MiniLM-L6-v2")

# Initialize clients
embedder = SentenceTransformer(EMBED_MODEL_NAME)

# Try to connect to Qdrant, but continue if unavailable
qdrant = None
try:
    qdrant = QdrantClient(url=QDRANT_URL, prefer_grpc=False)
    qdrant.get_collections()  # Test connection
    print("✓ Connected to Qdrant")
except Exception as e:
    print(f"⚠️ Qdrant unavailable: {e}. Running without Qdrant.")
    qdrant = None


class GenerateRequest(BaseModel):
    model: str
    prompt: str
    stream: Optional[bool] = False


def get_relevant_products(query: str, limit: int = 3) -> list:
    """Search Qdrant for relevant products, with fallback to empty list."""
    if not qdrant:
        return []  # Fallback: no products from Qdrant
    
    try:
        query_vector = embedder.encode(query).tolist()
        results = qdrant.search(
            collection_name=QDRANT_COLLECTION,
            query_vector=("text", query_vector),  # Named vector format
            limit=limit
        )
        
        products = []
        for result in results:
            payload = result.payload
            if payload is not None:
                products.append({
                    "title": payload.get("title", "Unknown"),
                    "description": payload.get("description", ""),
                    "price": payload.get("price"),
                    "type": payload.get("type", ""),
                    "score": result.score,
                })
        return products
    except Exception as e:
        print(f"Error searching Qdrant: {e}")
        return []


def generate_mock_response(prompt: str) -> str:
    """Generate a mock LLM response that prioritizes actual products."""
    # The orchestrator passes context like:
    # "Master Prompt... \n\nUser Query: {query}\n\nRelevant Products:\n{product_context}\n\nResponse:"
    
    # ALWAYS try to extract and display products first
    if "Relevant Products:" in prompt:
        try:
            parts = prompt.split("Relevant Products:")
            if len(parts) > 1:
                products_section = parts[1].split("Response:")[0].strip()
                
                # If we have meaningful product context, display products (ignore keywords)
                if products_section and len(products_section) > 20:
                    # Parse individual products (separated by \n\n)
                    product_lines = [p.strip() for p in products_section.split("\n\n") if p.strip()]
                    
                    if product_lines:
                        response = "<div style='padding: 15px; background: transparent;'>"
                        response += "<h3 style='color: #60a5fa; margin-bottom: 20px; font-weight: bold; font-size: 1.3em;'>🎁 Perfect Matches For You</h3>"
                        response += "<div style='display: flex; flex-direction: column; gap: 15px;'>"
                        
                        for product_text in product_lines[:4]:  # Show up to 4 products
                            if product_text:
                                # Parse product information (ID, Product, Type, Price, Description)
                                lines = product_text.split("\n")
                                
                                # Extract fields
                                product_id = ""
                                title = ""
                                product_type = ""
                                price = ""
                                description = ""
                                
                                for line in lines:
                                    if line.startswith("ID:"):
                                        product_id = line.replace("ID:", "").strip()
                                    elif line.startswith("Product:"):
                                        title = line.replace("Product:", "").strip()
                                    elif line.startswith("Type:"):
                                        product_type = line.replace("Type:", "").strip()
                                    elif line.startswith("Price:"):
                                        price = line.replace("Price:", "").strip()
                                    elif line.startswith("Description:"):
                                        description = line.replace("Description:", "").strip()
                                
                                if not title:
                                    title = lines[0] if lines else "Product"
                                
                                # Original full product card structure
                                response += f"""
                                <div style='display: flex; gap: 15px; padding: 15px; background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'>
                                    <!-- Product Image Placeholder -->
                                    <div style='flex-shrink: 0; width: 100px; height: 100px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-size: 2em;'>🎁</div>
                                    
                                    <!-- Product Details -->
                                    <div style='flex: 1; display: flex; flex-direction: column;'>
                                        <!-- Title -->
                                        <h4 style='color: #1f2937; font-size: 1.05em; font-weight: 600; margin: 0 0 8px 0; line-height: 1.4;'>{title}</h4>
                                        
                                        <!-- Product ID -->
                                        {f'<div style="color: #9ca3af; font-size: 0.85em; margin-bottom: 6px;">ID: {product_id}</div>' if product_id else ''}
                                        
                                        <!-- Product Type -->
                                        {f'<div style="color: #6b7280; font-size: 0.9em; margin-bottom: 6px;"><strong>Category:</strong> {product_type}</div>' if product_type else ''}
                                        
                                        <!-- Price -->
                                        <div style='margin-bottom: 8px;'>
                                            <span style='color: #22c55e; font-size: 1.3em; font-weight: bold;'>{price if price else "Price on request"}</span>
                                        </div>
                                        
                                        <!-- Description -->
                                        {f'<div style="color: #6b7280; font-size: 0.9em; line-height: 1.4; margin-top: 8px;">{description[:200]}...</div>' if description else ''}
                                    </div>
                                </div>
                                """
                        
                        response += "</div>"
                        response += "<p style='color: #9ca3af; font-size: 0.95em; margin-top: 15px; text-align: center;'>💡 Above are your search results</p>"
                        response += "</div>"
                        return response
        except Exception as e:
            print(f"Error parsing products: {e}")
    
    # Only show "no products" message if we couldn't find any
    return "<div style='text-align: center; padding: 20px; color: #9ca3af;'><p>Sorry, no products match your search. Try different keywords like 'floral', 'woody', 'fresh', or 'oud'.</p></div>"


@app.post("/api/generate")
def generate(request: GenerateRequest):
    """Mock LLM generation endpoint compatible with Ollama API."""
    logger.info(f"--- LLM Mock received request ---")
    logger.info(f"Model: {request.model}")
    logger.info(f"Prompt length: {len(request.prompt)} chars")
    
    # Accept any model name for mock purposes - always return success
    logger.info("Accepting model request for mock service")
    
    try:
        logger.info("Generating response from product context...")
        response_text = generate_mock_response(request.prompt)
        
        logger.info(f"Response generated successfully")
        logger.info(f"Response length: {len(response_text)} chars")
        logger.info(f"-------------------------------\n")
        
        # Return in Ollama-compatible format
        return {
            "model": request.model,  # Return the requested model name
            "created_at": "2025-11-12T19:30:00Z",
            "response": response_text,
            "done": True,
            "context": None,
            "total_duration": 1000000000,
            "load_duration": 100000000,
            "prompt_eval_count": 50,
            "prompt_eval_duration": 500000000,
            "eval_count": 100,
            "eval_duration": 400000000,
        }
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tags")
def tags():
    """Return available models."""
    return {
        "models": [
            {
                "name": "llama2:latest",
                "modified_at": "2025-11-12T19:30:00Z",
                "size": 3826087936,
                "digest": "mock",
            },
            {
                "name": "llama3.1:8b-instruct",
                "modified_at": "2025-11-12T19:30:00Z",
                "size": 3826087936,
                "digest": "mock",
            }
        ]
    }


@app.get("/api/version")
def version():
    """Return version info."""
    return {"version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=11434)
