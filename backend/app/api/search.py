from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
import time
import uuid
import logging

from app.api.deps import get_db, get_current_user
from app.schemas.search import SearchRequest, SearchResponse, SearchResultItem, AdvancedSearchRequest
from app.core.config import settings
from app.core.embedding import get_embedding_service
from app.core.encryption import KeyManager
from app.core.vector_encryption import VectorEncryptor
from app.core.cyborg import CyborgDBManager
from app.core.analytics import log_search_background
from app.core.llm import LLMAnswerService
from app.models.database import User, Document, DocumentChunk
from fastapi import BackgroundTasks

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize LLM service
llm_service = LLMAnswerService(settings)

@router.post("/", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Perform a semantic search over encrypted documents.
    1. Embeds the query.
    2. Encrypts the query vector using the tenant's key.
    3. Searches the tenant's encrypted index in CyborgDB.
    """
    start_time = time.time()
    tenant_id = current_user.tenant_id
    query_id = str(uuid.uuid4())
    
    logger.info(f"Processing search request {query_id} for tenant {tenant_id}")
    
    # 1. Generate Query Embedding
    try:
        embedding_service = get_embedding_service()
        # Returns List[List[float]]
        embeddings = embedding_service.generate_embeddings([request.query])
        query_vector = embeddings[0]
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process query embedding"
        )
        
    # 2. Get Tenant Key (for CyborgDB encrypted index)
    try:
        tenant_key = KeyManager.get_tenant_key(db, tenant_id)
    except ValueError as e:
        logger.error(f"Key retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Encryption key error"
        )
        
    # 3. Search CyborgDB
    try:
        # CyborgDB handles encryption internally - pass raw query vector, not encrypted string
        # Convert tenant_key to index_key format (list of integers)
        import base64
        index_key_bytes = base64.urlsafe_b64decode(tenant_key)
        index_key_list = list(index_key_bytes[:32])
        # Pad with zeros if needed
        while len(index_key_list) < 32:
            index_key_list.append(0)
        
        # Pass RAW query_vector (not encrypted_query) to CyborgDB
        raw_results = CyborgDBManager.search(
            str(tenant_id),
            query_vector,  # Use raw vector, not encrypted string
            top_k=request.top_k,
            index_key=index_key_list
        )
    except Exception as e:
        logger.error(f"CyborgDB search failed: {e}")
        # If it's a "not found" error, it implies index missing -> return empty
        if "not found" in str(e).lower() or "no index" in str(e).lower():
             logger.warning(f"Index not found for tenant {tenant_id}, returning empty results")
             raw_results = []
        else:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Search service unavailable"
            )
            
    # 4. Fetch Result Details from DB
    formatted_results = []
    
    if raw_results:
        # Extract IDs and map scores
        chunk_ids = []
        scores_map = {}
        meta_map = {}
        
        logger.info(f"Processing {len(raw_results)} raw results from CyborgDB")
        
        for match in raw_results:
            # Handle dict or object response
            mid = match.get('id') if isinstance(match, dict) else getattr(match, 'id', None)
            if mid:
                mid_str = str(mid)
                chunk_ids.append(mid_str)
                
                # CyborgDB returns 'distance' (lower is better, 0 = identical)
                # Convert distance to similarity percentage (higher is better, 100% = identical)
                if isinstance(match, dict):
                    distance = match.get('distance')
                    if distance is not None:
                        # For cosine distance: typically 0-2 range, but often 0-1
                        # Convert to similarity: similarity = 1 - distance
                        # Then to percentage: * 100
                        similarity = max(0.0, 1.0 - float(distance))
                        score_val = similarity
                        logger.info(f"Chunk {mid_str}: distance={distance}, similarity={similarity}")
                    else:
                        # Fallback to score or similarity fields
                        score_val = match.get('score') or match.get('similarity') or 0.0
                        logger.info(f"Chunk {mid_str}: using fallback score={score_val}")
                else:
                    distance = getattr(match, 'distance', None)
                    if distance is not None:
                        similarity = max(0.0, 1.0 - float(distance))
                        score_val = similarity
                    else:
                        score_val = getattr(match, 'score', None) or getattr(match, 'similarity', None) or 0.0
                
                scores_map[mid_str] = float(score_val) if score_val is not None else 0.0
                
                # Handle metadata
                meta_val = match.get('metadata') if isinstance(match, dict) else getattr(match, 'metadata', {})
                meta_map[mid_str] = meta_val or {}
                
        # Query DB for text content
        try:
            # We fetch chunks matching the IDs found in index
            db_chunks = db.query(DocumentChunk).filter(
                DocumentChunk.id.in_(chunk_ids),
                DocumentChunk.tenant_id == tenant_id
            ).all()
            
            chunks_map = {str(c.id): c for c in db_chunks}
            
            # Fetch associated documents for filenames
            doc_ids = list(set([c.doc_id for c in db_chunks]))
            if doc_ids:
                documents = db.query(Document).filter(Document.id.in_(doc_ids)).all()
                docs_map = {d.id: d for d in documents}
            else:
                docs_map = {}
                
            # Assemble results respecting original rank order
            for mid in chunk_ids:
                chunk = chunks_map.get(mid)
                if not chunk:
                    # Skip if not found in DB (e.g. deleted but in index)
                    continue
                    
                doc = docs_map.get(chunk.doc_id)
                
                # Combine metadata
                result_meta = meta_map.get(mid, {}).copy()
                result_meta.update({
                    "filename": doc.filename if doc else "Unknown",
                    "doc_id": str(chunk.doc_id),
                    "page_number": chunk.page_number,
                    "section": chunk.section_heading
                })
                
                formatted_results.append(SearchResultItem(
                    id=mid,
                    score=scores_map.get(mid, 0.0),
                    text=chunk.text,  # Rehydrated content
                    metadata=result_meta
                ))
                
        except Exception as e:
            logger.error(f"Failed to rehydrate search results: {e}")
            # Fallback: Return what we have from index (IDs only)
            for mid in chunk_ids:
                formatted_results.append(SearchResultItem(
                    id=mid,
                    score=scores_map.get(mid, 0.0),
                    text=None,
                    metadata={"error": "Detail retrieval failed"}
                ))
            
    elapsed_ms = (time.time() - start_time) * 1000
    
    logger.info(f"Search request {query_id} completed in {elapsed_ms:.2f}ms with {len(formatted_results)} results")
    
    # 5. Generate LLM Answer (Optional)
    llm_answer = None
    llm_result = None
    if llm_service.enabled and len(formatted_results) > 0:
        try:
            logger.info(f"Generating LLM answer for query {query_id}")
            # Convert search results to format expected by LLM service
            llm_input_results = [
                {
                    "text": r.text,
                    "id": r.id,
                    "similarity_score": r.score,
                    "metadata": r.metadata
                }
                for r in formatted_results
            ]
            logger.info(f"LLM input results (first 2):")
            for i, result in enumerate(llm_input_results[:2]):
                logger.info(f"  Result {i}: metadata keys={list(result.get('metadata', {}).keys())}")
                logger.info(f"            metadata={result.get('metadata', {})}")
                
            llm_result = llm_service.generate_answer_from_search(
                query=request.query,
                search_results=llm_input_results,
                tenant_id=str(tenant_id)
            )
            if llm_result.get("success"):
                llm_answer = llm_result.get("answer")
                logger.info(f"LLM answer generated using {llm_result.get('tokens_used', 0)} tokens")
                logger.info(f"LLM sources returned: {llm_result.get('sources', [])}")
            else:
                logger.warning(f"LLM answer generation failed: {llm_result.get('error', 'Unknown error')}")
        except Exception as e:
            logger.error(f"Error generating LLM answer: {e}", exc_info=True)
            # Don't fail the search if LLM fails - return results anyway
    
    # Log analytics
    background_tasks.add_task(
        log_search_background,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        query=request.query,
        latency_ms=elapsed_ms,
        result_count=len(formatted_results),
        top_k=request.top_k
    )
    
    response_data = {
        "results": formatted_results,
        "query_id": query_id,
        "latency_ms": elapsed_ms,
        "total_results": len(formatted_results)
    }
    
    # Add LLM answer if available
    if llm_answer:
        response_data["llm_answer"] = llm_answer
        response_data["llm_sources"] = llm_result.get("sources", [])
        response_data["llm_confidence"] = llm_result.get("confidence", 0.0)
        response_data["llm_disclaimer"] = llm_result.get("disclaimer")
    
    return SearchResponse(**response_data)


@router.post("/advanced", response_model=SearchResponse)
async def advanced_search(
    request: AdvancedSearchRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Advanced search with reranking.
    Simplified to avoid LangChain recursion issues.
    """
    start_time = time.time()
    query_id = str(uuid.uuid4())
    tenant_id = current_user.tenant_id
    logger.info(f"Advanced search {query_id} for tenant {tenant_id}")
    
    try:
        # 1. Generate Query Embedding
        embedding_service = get_embedding_service()
        embeddings = embedding_service.generate_embeddings([request.query])
        query_vector = embeddings[0]
        
        # 2. Get encryption key
        try:
            tenant_key = KeyManager.get_tenant_key(db, tenant_id)
        except ValueError:
            logger.warning(f"No encryption key found for tenant {tenant_id}, creating new one")
            KeyManager.create_tenant_key(db, tenant_id)
            tenant_key = KeyManager.get_tenant_key(db, tenant_id)
        
        # 3. Search CyborgDB (it handles encryption internally)
        import base64
        index_key = base64.urlsafe_b64decode(tenant_key)
        # Pass raw query_vector to CyborgDB, not encrypted string
        raw_results = CyborgDBManager.search(str(tenant_id), query_vector, request.top_k, index_key=list(index_key[:32]))
        
        if not raw_results:
            logger.info(f"No search results found for tenant {tenant_id}")
            elapsed_ms = (time.time() - start_time) * 1000
            return SearchResponse(results=[], query_id=query_id, latency_ms=elapsed_ms, total_results=0)
        
        # 5. Extract chunk IDs and scores
        chunk_ids = []
        scores_map = {}
        for res in raw_results:
            mid = res.get('id') if isinstance(res, dict) else getattr(res, 'id', None)
            if mid:
                chunk_ids.append(str(mid))
                # CyborgDB already returns computed score (not distance)
                if isinstance(res, dict):
                    score = res.get('score', 0.0)
                else:
                    score = getattr(res, 'score', 0.0)
                
                logger.info(f"Chunk {mid}: score={score}")
                scores_map[str(mid)] = float(score)
        
        if not chunk_ids:
            elapsed_ms = (time.time() - start_time) * 1000
            return SearchResponse(results=[], query_id=query_id, latency_ms=elapsed_ms, total_results=0)
        
        # 6. Fetch chunks from database with document relationship
        chunks = db.query(DocumentChunk).options(
            joinedload(DocumentChunk.document)
        ).filter(
            DocumentChunk.id.in_(chunk_ids),
            DocumentChunk.tenant_id == tenant_id
        ).all()
        
        # 7. Rerank if requested
        formatted_results = []
        for chunk in chunks:
            chunk_id_str = str(chunk.id)
            score = scores_map.get(chunk_id_str, 0.0)
            
            # Apply reranking boost based on query term matches
            if request.rerank:
                query_terms = request.query.lower().split()
                text = chunk.text.lower()
                match_count = sum(1 for term in query_terms if term in text)
                score = score * (1 + (0.05 * match_count))
            
            formatted_results.append(SearchResultItem(
                id=chunk_id_str,
                score=score,
                text=chunk.text,
                metadata={
                    "document_id": str(chunk.doc_id),
                    "chunk_index": chunk.chunk_sequence,
                    "filename": chunk.document.filename if chunk.document else "Unknown",
                    "page_number": chunk.page_number
                }
            ))
        
        # Sort by score descending
        formatted_results.sort(key=lambda x: x.score, reverse=True)
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        # 8. Generate LLM Answer (Optional)
        llm_answer = None
        llm_result = None
        if llm_service.enabled and len(formatted_results) > 0:
            try:
                logger.info(f"Generating LLM answer for advanced search {query_id}")
                llm_input_results = [
                    {
                        "text": r.text,
                        "id": r.id,
                        "similarity_score": r.score,
                        "metadata": r.metadata
                    }
                    for r in formatted_results[:5]  # Top 5 results for LLM
                ]
                
                llm_result = llm_service.generate_answer_from_search(
                    query=request.query,
                    search_results=llm_input_results,
                    tenant_id=str(tenant_id)
                )
                
                if llm_result and llm_result.get("success"):
                    llm_answer = llm_result.get("answer")
                    
            except Exception as e:
                logger.warning(f"LLM answer generation failed: {e}")
        
        response_data = {
            "query_id": query_id,
            "results": formatted_results,
            "total_results": len(formatted_results),
            "latency_ms": elapsed_ms,
            "llm_answer": llm_answer,
            "llm_sources": llm_result.get("sources", []) if llm_result else [],
            "llm_confidence": llm_result.get("confidence", 0.0) if llm_result else 0.0,
            "llm_disclaimer": llm_result.get("disclaimer") if llm_result else None
        }
        
        # Log search analytics in background
        if background_tasks:
            background_tasks.add_task(
                log_search_background,
                tenant_id=tenant_id,
                user_id=current_user.id,
                query=request.query,
                latency_ms=elapsed_ms,
                result_count=len(formatted_results),
                top_k=request.top_k
            )
        
        return SearchResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Advanced search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Advanced search processing failed: {str(e)}"
        )
