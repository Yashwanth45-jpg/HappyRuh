# app/db_logger/logger.py
from datetime import datetime
from .db import SessionLocal
from .models import LLMLog

def log_llm_response(
    response_html: str,
    model: str,
    request_ts: datetime,
    response_ts: datetime,
    latency_ms: int,
    error: str | None = None
) -> None:
    """
    Save an LLM response log into the database.
    Adds detailed debugging print statements.
    """
    print(f"[DB-LOGGER] Attempting to log response for model='{model}'")
    print(f"[DB-LOGGER] Request Time: {request_ts}, Response Time: {response_ts}, Latency: {latency_ms}ms")
    if error:
        print(f"[DB-LOGGER] Error detected: {error}")
    
    db = SessionLocal()
    try:
        log_entry = LLMLog(
            response_html=response_html,
            model=model,
            request_ts=request_ts,
            response_ts=response_ts,
            latency_ms=latency_ms,
            error=error,
        )
        db.add(log_entry)
        db.commit()
        print(f"[DB-LOGGER] Successfully logged response for model='{model}'")
    except Exception as e:
        db.rollback()
        print(f"[DB-LOGGER] Failed to log response! Exception: {e}")
    finally:
        db.close()
        print(f"[DB-LOGGER] DB session closed.")