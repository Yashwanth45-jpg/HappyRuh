# src/orchestrator/llm_connector.py
import os
import json
import requests
import time
import inspect
from datetime import datetime
from typing import Callable, TypeVar, Any
from dotenv import load_dotenv

load_dotenv()

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

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct")

MASTER_PROMPT = """
You are an intelligent assistant for HappyRuH Fragrances.
Given a user query and relevant products from the database, create a clean, helpful response.

Guidelines:
- Be concise and friendly
- Highlight key product details (name, price, category, description)
- Focus on products that match the user's query
- Return ONLY a short summary paragraph, NO unnecessary formatting
"""

@log_llm_call(name="LLM_Generate_Response")
def generate_response(user_query: str, context: str) -> str:
    """
    Calls Ollama locally to generate a clean, product-focused response.
    """
    print(f"[DEBUG] generate_response called with user_query='{user_query[:50]}...', context_length={len(context)}")
    prompt = f"{MASTER_PROMPT}\n\nUser Query: {user_query}\n\nRelevant Products:\n{context}\n\nResponse:"
    print(f"[DEBUG] Prompt length: {len(prompt)} characters")

    if LLM_PROVIDER.lower() == "ollama":
        payload = {"model": OLLAMA_MODEL, "prompt": prompt}
        print(f"[DEBUG] Sending request to {OLLAMA_BASE_URL}/api/generate with model {OLLAMA_MODEL}")
        try:
            r = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=120)
            print(f"[DEBUG] Received response with status code: {r.status_code}")
            r.raise_for_status()
            
            # Parse the response
            response_data = r.json()
            response_html = response_data.get("response", "").strip()
            print(f"[DEBUG] Response HTML length: {len(response_html)} characters")
            
            # The mock LLM returns HTML directly, so just return it as-is
            # (The response field is already formatted HTML from llm_mock.py)
            if response_html:
                print(f"[DEBUG] Returning response HTML: {response_html[:100]}...")
                return response_html
            else:
                print(f"[DEBUG] No response generated, returning default message")
                return '<p style="color: #fca5a5;">No response generated</p>'
                
        except Exception as e:
            print(f"[DEBUG] Exception in generate_response: {e}")
            return f'<p style="color: #fca5a5;"><b>Unable to process:</b> {str(e)[:100]}</p>'

    else:
        # fallback response if no provider available
        print(f"[DEBUG] LLM provider not available, returning fallback response")
        return '<p style="color: #fca5a5;">LLM service unavailable</p>'
