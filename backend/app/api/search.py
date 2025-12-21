from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
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
from app.core.retriever import CyborgDBRetriever
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
        
    # 2. Encrypt Query Vector
    try:
        tenant_key = KeyManager.get_tenant_key(db, tenant_id)
        # Encrypt vector to base64 string
        encrypted_query = VectorEncryptor.encrypt_vector(query_vector, tenant_key)
    except ValueError as e:
        logger.error(f"Key retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Encryption key error"
        )
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Query encryption failed"
        )
        
    # 3. Search CyborgDB
    try:
        # Convert tenant_key (base64 string) to bytes for CyborgDB index_key
        import base64
        index_key = base64.urlsafe_b64decode(tenant_key)
        raw_results = CyborgDBManager.search(
            str(tenant_id),
            encrypted_query,
            top_k=request.top_k,
            index_key=index_key
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
    Advanced search with Context Augmentation and Reranking.
    Uses LangChain Retriever integration.
    """
    start_time = time.time()
    query_id = str(uuid.uuid4())
    logger.info(f"Advanced search {query_id} for tenant {current_user.tenant_id}")
    
    retriever = CyborgDBRetriever(
        tenant_id=str(current_user.tenant_id),
        db_session=db,
        top_k=request.top_k,
        augment_context=request.augment
    )
    
    try:
        # 1. Retrieve (LangChain Interface)
        docs = retriever.get_relevant_documents(request.query)
        
        # 2. Rerank (Keyword Boost)
        if request.rerank and docs:
            query_terms = request.query.lower().split()
            for d in docs:
                 text = d.page_content.lower()
                 match_count = sum(1 for term in query_terms if term in text)
                 # Add 5% boost per matching term
                 current_score = d.metadata.get('score', 0.0)
                 d.metadata['score'] = current_score * (1 + (0.05 * match_count))
                 
            # Re-sort descending
            docs.sort(key=lambda x: x.metadata.get('score', 0.0), reverse=True)
            
        # 3. Format Response
        formatted_results = []
        for d in docs:
            formatted_results.append(SearchResultItem(
                id=d.metadata.get("source", ""),
                score=d.metadata.get("score", 0.0),
                text=d.page_content,
                metadata=d.metadata
            ))
            
        elapsed_ms = (time.time() - start_time) * 1000
        
        # 4. Generate LLM Answer (Optional)
        llm_answer = None
        llm_result = None
        if llm_service.enabled and len(formatted_results) > 0:
            try:
                logger.info(f"Generating LLM answer for advanced search {query_id}")
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
                logger.info(f"Advanced LLM input results (first 2):")
                for i, result in enumerate(llm_input_results[:2]):
                    logger.info(f"  Result {i}: metadata keys={list(result.get('metadata', {}).keys())}")
                    logger.info(f"            metadata={result.get('metadata', {})}")
                    
                llm_result = llm_service.generate_answer_from_search(
                    query=request.query,
                    search_results=llm_input_results,
                    tenant_id=str(current_user.tenant_id)
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
        
    except Exception as e:
        logger.error(f"Advanced search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Advanced search processing failed: {str(e)}"
        )
