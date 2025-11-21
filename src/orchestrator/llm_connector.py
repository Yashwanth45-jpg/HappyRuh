# src/orchestrator/llm_connector.py
import os
import json
import requests
import time
import inspect
from datetime import datetime
from typing import Callable, TypeVar, Any, List, Dict
from dotenv import load_dotenv

load_dotenv()

# Try to import ollama client
try:
    from ollama import Client
    OLLAMA_CLIENT_AVAILABLE = True
    print("[INFO] Ollama client available")
except ImportError:
    OLLAMA_CLIENT_AVAILABLE = False
    print("[INFO] Ollama client not available - will use requests fallback")

# ============================
# Logging Decorator
# ============================
F = TypeVar("F", bound=Callable[..., Any])


def log_llm_call(name: str) -> Callable[[F], F]:
    """
    Decorator to log any function (sync/async) call to DB.
    Logs arguments, result (if str), exceptions, timestamps, and latency.
    """
    print(f"[DEBUG] Setting up log_llm_call decorator for {name}")
    def decorator(func: F) -> F:
        print(f"[DEBUG] Decorating function {func.__name__} with {name}")
        if inspect.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                print(f"[DEBUG] Entering async_wrapper for {name}")
                request_ts = datetime.utcnow()
                start_time = time.time()
                print(f"[AsyncLog] {name} called with args={args}, kwargs={kwargs}")
                result = None
                error = None
                try:
                    print(f"[DEBUG] Calling actual function {func.__name__}")
                    result = await func(*args, **kwargs)
                    error = None
                    print(f"[DEBUG] Function {func.__name__} completed successfully")
                    return result
                except Exception as e:
                    result = None
                    error = str(e)
                    print(f"[AsyncLog] {name} raised exception: {error}")
                    raise
                finally:
                    latency_ms = int((time.time() - start_time) * 1000)
                    response_ts = datetime.utcnow()
                    print(f"[DEBUG] Preparing to log to DB for {name}")
                    try:
                        from ..db_logger.logger import log_llm_response
                        response_type = type(result).__name__
                        response_preview = str(result)[:100] if result else "None"
                        print(f"[DEBUG] Logging to DB - Response type: {response_type}, Preview: {response_preview}")
                        log_llm_response(
                            response_html=result if isinstance(result, str) else f"<non-str result: {type(result).__name__}>",
                            model=name,
                            request_ts=request_ts,
                            response_ts=response_ts,
                            latency_ms=latency_ms,
                            error=error
                        )
                        print(f"[AsyncLog] {name} logged to DB successfully.")
                    except Exception as db_err:
                        print(f"[AsyncLog] Failed to log {name} to DB: {db_err}")
                    print(f"[AsyncLog] {name} completed in {latency_ms}ms")
            return async_wrapper  # type: ignore
        else:
            def sync_wrapper(*args, **kwargs):
                print(f"[DEBUG] Entering sync_wrapper for {name}")
                request_ts = datetime.utcnow()
                start_time = time.time()
                print(f"[Log] {name} called with args={args}, kwargs={kwargs}")
                result = None
                error = None
                try:
                    print(f"[DEBUG] Calling actual function {func.__name__}")
                    result = func(*args, **kwargs)
                    error = None
                    print(f"[DEBUG] Function {func.__name__} completed successfully")
                    return result
                except Exception as e:
                    result = None
                    error = str(e)
                    print(f"[Log] {name} raised exception: {error}")
                    raise
                finally:
                    latency_ms = int((time.time() - start_time) * 1000)
                    response_ts = datetime.utcnow()
                    print(f"[DEBUG] Preparing to log to DB for {name}")
                    try:
                        from ..db_logger.logger import log_llm_response
                        response_type = type(result).__name__
                        response_preview = str(result)[:100] if result else "None"
                        print(f"[DEBUG] Logging to DB - Response type: {response_type}, Preview: {response_preview}")
                        log_llm_response(
                            response_html=result if isinstance(result, str) else f"<non-str result: {type(result).__name__}>",
                            model=name,
                            request_ts=request_ts,
                            response_ts=response_ts,
                            latency_ms=latency_ms,
                            error=error
                        )
                        print(f"[Log] {name} logged to DB successfully.")
                    except Exception as db_err:
                        print(f"[Log] Failed to log {name} to DB: {db_err}")
                    print(f"[Log] {name} completed in {latency_ms}ms")
            return sync_wrapper  # type: ignore
    return decorator

# ============================
# LLM Configuration - Dual Setup
# ============================

# Ollama for conversational responses (slower but better quality)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct")

# LM Studio for fast summarization (faster, local)
LMSTUDIO_BASE_URL = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
LMSTUDIO_MODEL = os.getenv("LMSTUDIO_MODEL", "qwen2.5-1.5b-instruct")  # Fast lightweight model

# Try to import transformers for local summarization fallback
try:
    from transformers import pipeline
    print("[INFO] Transformers available - will use local summarization if LM Studio unavailable")
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    print("[INFO] Transformers not available - install with: pip install transformers torch")
    TRANSFORMERS_AVAILABLE = False

# ============================
# LLMConnector Class - Optimized for Context & Conversation
# ============================

class LLMConnector:
    """
    Handles LLM interactions with Ollama (Llama 3.1 8B) for conversational responses.
    Manages conversation history and product context injection.
    """
    
    def __init__(self):
        """Initialize the LLM connector with dual Ollama clients."""
        # Client 1: "Sales Expert" - Llama 3.1 8B (for product recommendations)
        self.llama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.llama_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct")
        
        # Client 2: "Fast Talker" - Qwen 2.5 1.5B (for general chat/fallback)
        self.qwen_url = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:11435")
        self.qwen_model = os.getenv("OLLAMA_SUMMARIZER_MODEL", "qwen2.5:1.5b")
        
        # Initialize clients if available
        if OLLAMA_CLIENT_AVAILABLE:
            self.llama_client = Client(host=self.llama_url)
            self.qwen_client = Client(host=self.qwen_url)
            print(f"[INFO] LLMConnector initialized:")
            print(f"  - Llama 3.1 8B (Sales) at {self.llama_url}")
            print(f"  - Qwen 2.5 1.5B (Chat) at {self.qwen_url}")
        else:
            self.llama_client = None
            self.qwen_client = None
            print(f"[INFO] LLMConnector initialized with requests fallback")
        
        # THE PERSONA - Core system instruction for 'Ruh' the HappyRuh assistant
        self.sales_system_instruction = """
You're Ruh, a buddy helping friends find their perfect vibe at HappyRuh!

BE LIKE THIS:
- Talk like you're texting a friend - keep it SHORT (2-4 sentences max)
- Get straight to the point - no fluff
- Use casual, warm language: "Hey!", "Perfect for...", "This one's amazing because..."
- Mention 2-3 products MAX (don't overwhelm them)
- Quick reason WHY each product fits + price in ₹
- End with ONE simple question to help them decide
- Be excited but chill - like you genuinely found something cool for them

DON'T:
- Write essays or long paragraphs
- List every single product
- Use overly formal language
- Hallucinate products not in the context

VIBE: Your friend who has great taste and actually knows what they're talking about.
"""
        
        self.chat_system_instruction = """
You're Ruh - helping your friend find something cool!

SITUATION: They asked for something, but nothing matched. No worries!

RESPOND LIKE THIS:
- Keep it SUPER short (1-2 sentences max)
- Be understanding and casual: "Hmm, didn't find that exactly..."
- Quickly pivot with a helpful question
- Match their energy (if they're playful, be playful; if serious, be helpful)

EXAMPLES:
- "Heading to a wedding" → "Nice! What's the vibe - traditional elegant or modern chic?"
- "something for confidence" → "Love it! Do you prefer bold and spicy or fresh and uplifting scents?"
- Random query → "Haha, interesting! Tell me more - what's the occasion or mood you're going for?"

VIBE: Your chill friend who's here to help, not lecture.
"""
    
    def format_product_context(self, products_text: str) -> str:
        """
        Converts product search results into a formatted context string.
        
        Args:
            products_text: String containing product details from semantic search
            
        Returns:
            Formatted context string for LLM
        """
        if not products_text or products_text.strip() == "":
            return "No specific products found for this query."
        
        # The products_text from orchestrator already contains formatted products
        # We just need to wrap it with a clear header
        context_str = "HERE ARE THE PRODUCTS AVAILABLE IN STOCK:\n\n" + products_text
        return context_str
    
    def get_chat_response(self, user_message: str, chat_history: List[Dict[str, str]], search_results: str, intent_metadata: Dict = None) -> str:
        """
        Router Logic:
        - If products found -> Use Llama 3.1 8B to create sales pitch
        - If NO products -> Use Qwen 2.5 1.5B for fast general chat/fallback
        
        Args:
            user_message: Current user query
            chat_history: List of previous messages [{'role': 'user/assistant', 'content': '...'}]
            search_results: Formatted product search results from Qdrant
            intent_metadata: Intent classification metadata from LLM (needs_clarification, reasoning, strategy, etc.)
            
        Returns:
            LLM-generated response as string
        """
        print(f"[DEBUG] LLMConnector.get_chat_response called")
        print(f"[DEBUG] User message: {user_message[:100]}...")
        print(f"[DEBUG] Chat history length: {len(chat_history)}")
        print(f"[DEBUG] Search results length: {len(search_results)} chars")
        print(f"[DEBUG] Intent metadata: {intent_metadata}")
        
        # Router: Check if we have products to sell
        has_products = search_results and search_results.strip() and len(search_results) > 50
        
        if has_products:
            print(f"[ROUTER] Products found -> Using Llama 3.1 8B for sales pitch")
            return self._generate_sales_pitch(user_message, chat_history, search_results, intent_metadata)
        else:
            print(f"[ROUTER] No products found -> Using Qwen 2.5 1.5B for general chat")
            return self._generate_general_chat(user_message, chat_history, intent_metadata)
    
    def _generate_sales_pitch(self, user_message: str, chat_history: List[Dict[str, str]], search_results: str, intent_metadata: Dict = None) -> str:
        """
        SCENARIO A: PRODUCTS FOUND
        Uses Llama 3.1 8B to create persuasive product recommendations.
        """
        print(f"[LLAMA 3.1] Generating sales pitch...")
        
        # Format product context
        product_context = self.format_product_context(search_results)
        
        # Add intent context if LLM was used for classification
        intent_context = ""
        if intent_metadata and intent_metadata.get('strategy') in ['llm_classification', 'hybrid_llm_validation']:
            needs_clarification = intent_metadata.get('needs_clarification', False)
            reasoning = intent_metadata.get('reasoning', '')
            
            intent_context = f"""

IMPORTANT CONTEXT FROM INTENT ANALYSIS:
- The user's query was analyzed and classified
- Reasoning: {reasoning}
- Needs clarification: {'Yes - the query might be ambiguous, so ask a clarifying question' if needs_clarification else 'No - the intent is clear'}
"""
        
        # Create dynamic system prompt with products
        system_prompt = f"""{self.sales_system_instruction}

Their request: "{user_message}"{intent_context}

{product_context}

Pick 2-3 perfect matches. Tell them WHY + price. Keep it SHORT and friendly. Ask ONE question to help them choose.
{'Ask what they need to narrow it down.' if intent_metadata and intent_metadata.get('needs_clarification') else 'Be specific and helpful!'}
"""
        
        # Build message chain
        messages = [{'role': 'system', 'content': system_prompt}]
        
        # Add recent history (last 5 exchanges for context)
        if chat_history:
            messages.extend(chat_history[-5:])
        
        # Add current message
        messages.append({'role': 'user', 'content': user_message})
        
        # Call Llama 3.1
        try:
            if self.llama_client and OLLAMA_CLIENT_AVAILABLE:
                response = self.llama_client.chat(
                    model=self.llama_model,
                    messages=messages,
                    stream=False,
                    options={
                        'temperature': 0.7,
                        'top_p': 0.85,
                        'num_predict': 200,
                    }
                )
                response_text = response['message']['content']
                print(f"[LLAMA 3.1] Response: {len(response_text)} chars")
                return response_text
            else:
                # Fallback to requests
                payload = {
                    'model': self.llama_model,
                    'messages': messages,
                    'stream': False,
                    'options': {'temperature': 0.8, 'top_p': 0.9, 'num_predict': 400}
                }
                r = requests.post(f"{self.llama_url}/api/chat", json=payload, timeout=120)
                r.raise_for_status()
                return r.json()['message']['content']
        except Exception as e:
            print(f"[ERROR] Llama 3.1 call failed: {e}")
            return "I'm having trouble connecting right now. Please try again in a moment!"
    
    def _generate_general_chat(self, user_message: str, chat_history: List[Dict[str, str]], intent_metadata: Dict = None) -> str:
        """
        SCENARIO B: NO PRODUCTS / WEIRD QUERY
        Uses Qwen 2.5 1.5B for fast, lightweight conversational responses.
        Handles fallback scenarios with empathy and pivots back to products.
        """
        print(f"[QWEN 2.5] Generating general chat response...")
        
        # Build message chain with chat-focused system prompt
        messages = [{'role': 'system', 'content': self.chat_system_instruction}]
        
        # Add recent history (last 5 for speed)
        if chat_history:
            messages.extend(chat_history[-5:])
        
        # Add current message
        messages.append({'role': 'user', 'content': user_message})
        
        # Call Qwen 2.5 1.5B (fast and efficient)
        try:
            if self.qwen_client and OLLAMA_CLIENT_AVAILABLE:
                response = self.qwen_client.chat(
                    model=self.qwen_model,
                    messages=messages,
                    stream=False,
                    options={
                        'temperature': 0.7,  # Slightly lower for focused responses
                        'top_p': 0.85,
                        'num_predict': 150,  # Shorter responses for chat
                    }
                )
                response_text = response['message']['content']
                print(f"[QWEN 2.5] Response: {len(response_text)} chars")
                return response_text
            else:
                # Fallback to requests
                payload = {
                    'model': self.qwen_model,
                    'messages': messages,
                    'stream': False,
                    'options': {'temperature': 0.7, 'top_p': 0.85, 'num_predict': 150}
                }
                r = requests.post(f"{self.qwen_url}/api/chat", json=payload, timeout=60)
                r.raise_for_status()
                return r.json()['message']['content']
        except Exception as e:
            print(f"[ERROR] Qwen 2.5 call failed: {e}")
            # Fallback to simple response
            return "I'd love to help you find the perfect scent! Could you tell me more about what you're looking for? Are you interested in something floral, woody, or fresh?"

# ============================
# Global LLMConnector Instance
# ============================

_llm_connector = None

def get_llm_connector() -> LLMConnector:
    """Get or create the global LLMConnector instance."""
    global _llm_connector
    if _llm_connector is None:
        _llm_connector = LLMConnector()
    return _llm_connector

# ============================
# Legacy Function for Backward Compatibility
# ============================

MASTER_PROMPT = """
You are a friendly shopping assistant helping customers find the perfect products. You're knowledgeable, helpful, and genuinely care about finding the right match for each customer.

Your personality:
- Professional but warm and approachable
- Enthusiastic about helping customers find what they need
- Listen carefully to understand their specific needs and preferences
- Ask clarifying questions when needed (budget, occasion, preferences)
- Provide personalized recommendations based on their situation
- Explain why each product is a good match for them
- Use friendly, conversational language (not too formal, not too casual)

When customers ask about products:
- UNDERSTAND their context: What's the occasion? Who is it for? What's their style?
- LISTEN to budget constraints and preferences
- RECOMMEND products that truly fit their needs
- EXPLAIN the key features and why it's perfect for them
- COMPARE options when they're deciding between products
- BE HONEST if something might not be the best fit

Conversation style:
- "Hi! I'd love to help you find the perfect fragrance. What's the occasion?"
- "Great choice! This one has amazing staying power and the notes are perfect for evening wear."
- "Let me show you a few options in your budget that match what you're looking for..."
- "Based on what you've told me, I think this would be ideal because..."
- "Would you prefer something more subtle for daily wear, or something bold for special occasions?"

Rules:
- Always be helpful and customer-focused
- Understand the context before recommending
- Explain your recommendations clearly
- Ask questions to better understand their needs
- Keep responses clear and concise (3-5 sentences usually)
- Make customers feel valued and understood
"""

@log_llm_call(name="LLM_Generate_Response")
def generate_response(user_query: str, context: str) -> str:
    """
    Calls Ollama to generate a conversational, context-aware response like a best friend would.
    """
    print(f"[DEBUG] generate_response called with user_query='{user_query[:50]}...', context_length={len(context)}")
    
    # Create a dynamic prompt that encourages natural, contextual responses
    prompt = f"""{MASTER_PROMPT}

Your friend just said: "{user_query}"

Here are the products you found that might work:
{context}

Now respond naturally as their best friend. Understand what they REALLY need based on their situation. Don't just list products - have a real conversation. Help them find the PERFECT match.

Your response:"""
    
    print(f"[DEBUG] Prompt length: {len(prompt)} characters")

    if LLM_PROVIDER.lower() == "ollama":
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.9,  # Higher creativity for natural conversation
                "top_p": 0.95,
                "top_k": 50,
                "max_tokens": 400,
                "repeat_penalty": 1.1  # Avoid repetitive language
            }
        }
        print(f"[DEBUG] Sending request to {OLLAMA_BASE_URL}/api/generate with model {OLLAMA_MODEL}")
        try:
            r = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=120)
            print(f"[DEBUG] Received response with status code: {r.status_code}")
            r.raise_for_status()
            
            # Parse the response
            response_data = r.json()
            response_text = response_data.get("response", "").strip()
            print(f"[DEBUG] Response text length: {len(response_text)} characters")
            
            if response_text:
                # Format as conversational text with proper styling
                formatted_html = f'<div style="color: #e5e7eb; line-height: 1.7; font-size: 15px;">{response_text}</div>'
                print(f"[DEBUG] Returning formatted HTML")
                return formatted_html
            else:
                print(f"[DEBUG] No response generated")
                return '<p style="color: #fca5a5;">Hmm give me a sec, my brain just froze 😅 Try asking again?</p>'
                
        except Exception as e:
            print(f"[DEBUG] Exception in generate_response: {e}")
            return f'<p style="color: #fca5a5;">Ugh my connection is being weird right now 🤦 Can you try again?</p>'

    else:
        print(f"[DEBUG] LLM provider not available")
        return '<p style="color: #fca5a5;">Yo I can\'t access my product knowledge right now, gimme a minute! 🔄</p>'


# ============================
# Fast Summarization LLM
# ============================

@log_llm_call(name="LLM_Fast_Summarize")
def summarize_description_fast(description: str, max_length: int = 100) -> str:
    """
    Uses a fast, lightweight LLM to quickly summarize product descriptions.
    Tries LM Studio first, then falls back to local transformers, then simple truncation.
    
    Args:
        description: The raw product description to summarize
        max_length: Maximum length of the summary in characters
        
    Returns:
        Summarized description
    """
    if not description or len(description.strip()) == 0:
        return "No description available"
    
    # If description is already short, return it
    if len(description) <= max_length:
        return description.strip()
    
    print(f"[DEBUG] Fast summarization for description length: {len(description)}")
    
    # Try LM Studio first (fastest option)
    try:
        prompt = f"""Summarize this product description in {max_length} characters or less. Be concise and highlight key features:

{description}

Summary:"""
        
        payload = {
            "model": LMSTUDIO_MODEL,
            "messages": [
                {"role": "system", "content": "You are a concise product description summarizer. Keep summaries under the character limit."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,  # Low temperature for consistent summaries
            "max_tokens": 50,
            "stream": False
        }
        
        print(f"[DEBUG] Calling LM Studio at {LMSTUDIO_BASE_URL}/chat/completions")
        r = requests.post(
            f"{LMSTUDIO_BASE_URL}/chat/completions",
            json=payload,
            timeout=10  # Fast timeout for quick summarization
        )
        
        if r.status_code == 200:
            response_data = r.json()
            summary = response_data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            
            if summary and len(summary) > 0:
                print(f"[DEBUG] LM Studio summary generated: {len(summary)} chars")
                # Truncate if still too long
                return summary[:max_length] if len(summary) > max_length else summary
                
    except Exception as e:
        print(f"[DEBUG] LM Studio summarization failed: {e}")
    
    # Fallback to local transformers pipeline
    if TRANSFORMERS_AVAILABLE:
        try:
            print("[DEBUG] Using local transformers summarization")
            summarizer = pipeline("summarization", model="facebook/bart-large-cnn", device=-1)  # CPU
            
            # BART works best with 50-1024 tokens
            summary = summarizer(
                description[:1024],  # Limit input
                max_length=max_length // 4,  # Rough token estimate
                min_length=20,
                do_sample=False
            )[0]['summary_text']
            
            print(f"[DEBUG] Transformers summary generated: {len(summary)} chars")
            return summary
            
        except Exception as e:
            print(f"[DEBUG] Transformers summarization failed: {e}")
    
    # Final fallback: intelligent truncation
    print("[DEBUG] Using intelligent truncation fallback")
    sentences = description.split('. ')
    summary = sentences[0]
    
    for sentence in sentences[1:]:
        if len(summary) + len(sentence) + 2 <= max_length:
            summary += '. ' + sentence
        else:
            break
    
    # Add ellipsis if truncated
    if len(summary) < len(description):
        summary = summary.rstrip() + '...'
    
    return summary[:max_length]


@log_llm_call(name="LLM_Batch_Summarize")
def summarize_descriptions_batch(descriptions: list[str], max_length: int = 100) -> list[str]:
    """
    Batch summarize multiple descriptions for efficiency.
    
    Args:
        descriptions: List of descriptions to summarize
        max_length: Maximum length per summary
        
    Returns:
        List of summarized descriptions
    """
    print(f"[DEBUG] Batch summarizing {len(descriptions)} descriptions")
    
    summaries = []
    for desc in descriptions:
        summary = summarize_description_fast(desc, max_length)
        summaries.append(summary)
    
    return summaries
