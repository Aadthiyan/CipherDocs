from app.db.database import SessionLocal
from app.models.database import SearchLog
from sqlalchemy import func, desc
import uuid
import logging

logger = logging.getLogger(__name__)

def log_search_background(
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    query: str,
    latency_ms: float,
    result_count: int,
    top_k: int
):
    """
    Background task to log search queries to the database.
    Creates a dedicated DB session to ensure persistence after request/response cycle.
    """
    db = SessionLocal()
    try:
        log_entry = SearchLog(
            tenant_id=tenant_id,
            user_id=user_id,
            query_text=query[:1000],  # Truncate if needed
            query_latency_ms=int(latency_ms),
            result_count=result_count,
            top_k=top_k
        )
        db.add(log_entry)
        db.commit()
        # logger.debug(f"Logged search query: {query[:20]}...")
    except Exception as e:
        logger.error(f"Failed to log search analytics: {e}")
        db.rollback()
    finally:
        db.close()
