from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List
from pydantic import BaseModel

from app.api.deps import get_db, get_current_user
from app.models.database import User, SearchLog

router = APIRouter()

class AnalyticsStats(BaseModel):
    total_searches: int
    avg_latency_ms: float
    p95_latency_ms: float
    zero_result_rate: float

class PopularQuery(BaseModel):
    query_text: str
    count: int
    avg_results: float

@router.get("/search", response_model=AnalyticsStats)
async def get_search_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get search performance metrics"""
    # Simple Access Control
    if current_user.role != 'admin':
        # Allow if we decide metrics are for everyone, but task says Admin-only
        raise HTTPException(status_code=403, detail="Admin access required")
        
    query = db.query(SearchLog).filter(SearchLog.tenant_id == current_user.tenant_id)
    
    total = query.count()
    if total == 0:
        return AnalyticsStats(
            total_searches=0, 
            avg_latency_ms=0.0, 
            p95_latency_ms=0.0, 
            zero_result_rate=0.0
        )
        
    avg_latency = query.with_entities(func.avg(SearchLog.query_latency_ms)).scalar() or 0.0
    
    # Calculate P95
    latencies = [l[0] for l in query.with_entities(SearchLog.query_latency_ms).all()]
    latencies.sort()
    p95_idx = int(total * 0.95)
    # Ensure index is within bounds
    p95_idx = min(p95_idx, total - 1)
    p95 = latencies[p95_idx] if latencies else 0.0
    
    zero_results = query.filter(SearchLog.result_count == 0).count()
    zero_rate = zero_results / total
    
    return AnalyticsStats(
        total_searches=total,
        avg_latency_ms=float(avg_latency),
        p95_latency_ms=float(p95),
        zero_result_rate=zero_rate
    )

@router.get("/popular-queries", response_model=List[PopularQuery])
async def get_popular_queries(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get most frequent search queries"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
        
    results = db.query(
        SearchLog.query_text,
        func.count(SearchLog.id).label('count'),
        func.avg(SearchLog.result_count).label('avg_res')
    ).filter(
        SearchLog.tenant_id == current_user.tenant_id
    ).group_by(
        SearchLog.query_text
    ).order_by(
        desc('count')
    ).limit(limit).all()
    
    return [
        PopularQuery(query_text=r.query_text, count=r.count, avg_results=float(r.avg_res))
        for r in results
    ]

@router.get("/no-results", response_model=List[PopularQuery])
async def get_no_result_queries(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get queries that frequently return zero results"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    results = db.query(
        SearchLog.query_text,
        func.count(SearchLog.id).label('count')
    ).filter(
        SearchLog.tenant_id == current_user.tenant_id,
        SearchLog.result_count == 0
    ).group_by(
        SearchLog.query_text
    ).order_by(
        desc('count')
    ).limit(limit).all()
    
    return [
        PopularQuery(query_text=r.query_text, count=r.count, avg_results=0.0)
        for r in results
    ]
