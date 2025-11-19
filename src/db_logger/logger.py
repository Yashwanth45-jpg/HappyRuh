# app/db_logger/logger.py
from datetime import datetime
from .db import get_db_session
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
    Save an LLM response log into the database using a managed session.
    """
    print(f"[DB-LOGGER] Attempting to log response for model='{model}'")
    try:
        with get_db_session() as db:
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
        # The session will be rolled back automatically by the context manager on exception
        print(f"[DB-LOGGER] Failed to log response! Exception: {e}")
    finally:
        print(f"[DB-LOGGER] DB session context finished.")