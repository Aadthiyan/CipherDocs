"""
LLM Integration Module - Handles Groq API for answer generation
"""

import logging
from typing import Optional, List
from groq import Groq
from app.core.config import Settings

logger = logging.getLogger(__name__)


class GroqAnswerGenerator:
    """Generate synthesized answers using Groq LLM based on retrieved chunks"""
    
    def __init__(self, settings: Settings):
        """Initialize Groq client with API key"""
        self.settings = settings
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL
        self.max_tokens = settings.LLM_MAX_TOKENS
        self.temperature = settings.LLM_TEMPERATURE
    
    def generate_answer(
        self,
        query: str,
        retrieved_chunks: List[dict],
        tenant_id: str = "system"
    ) -> dict:
        """
        Generate a synthesized answer from retrieved chunks using Groq
        
        Args:
            query: Original user query
            retrieved_chunks: List of retrieved document chunks with metadata
            tenant_id: Tenant ID for logging
            
        Returns:
            dict with keys:
                - answer: The synthesized answer
                - sources: List of sources used
                - confidence: Confidence score
                - tokens_used: Number of tokens used
                - disclaimer: Warning if general knowledge might be used
        """
        try:
            # Format context from retrieved chunks
            context = self._format_context(retrieved_chunks)
            
            # Check confidence threshold
            confidence = self._calculate_confidence(retrieved_chunks)
            disclaimer = None
            
            if confidence < 0.5:
                disclaimer = "⚠️ Low confidence: Limited relevant information found in documents. Answer may include general knowledge."
                logger.warning(f"[{tenant_id}] Low confidence answer (score: {confidence})")
            
            # Build prompt with strict instructions
            prompt = self._build_prompt(query, context, confidence)
            
            # Call Groq API
            message = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            answer = message.choices[0].message.content
            
            # Extract sources
            sources = self._extract_sources(retrieved_chunks)
            
            logger.info(
                f"[{tenant_id}] Generated answer using {message.usage.total_tokens} tokens"
            )
            
            return {
                "answer": answer,
                "sources": sources,
                "confidence": confidence,
                "tokens_used": message.usage.total_tokens,
                "model": self.model,
                "disclaimer": disclaimer,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"[{tenant_id}] Error generating answer: {str(e)}")
            return {
                "answer": None,
                "error": str(e),
                "success": False
            }
    
    def _get_system_prompt(self) -> str:
        """Get strict system prompt that enforces document-only answers"""
        return """You are a document-based question answering assistant. 

CRITICAL INSTRUCTIONS:
1. ONLY answer based on the provided document context
2. If the context doesn't contain relevant information, say so explicitly
3. Do NOT use general knowledge, common sense, or information from outside the documents
4. If asked about something not in the documents, respond with: "This information is not available in the provided documents."
5. Always cite which source document the information comes from
6. Be accurate and concise

Remember: Your role is to synthesize ONLY the provided document excerpts, not to provide general knowledge."""
    
    def _format_context(self, chunks: List[dict]) -> str:
        """Format retrieved chunks into context string
        
        Optimized to reduce token usage:
        - Only use top 3-4 most relevant results
        - Truncate each result to 800 chars max
        """
        if not chunks:
            return "No relevant information found."
        
        # Use only top 3-4 results to stay within token limits
        max_chunks = min(4, len(chunks))
        relevant_chunks = chunks[:max_chunks]
        
        context_parts = []
        for i, chunk in enumerate(relevant_chunks, 1):
            text = chunk.get("text", "")
            score = chunk.get("similarity_score", 0)
            source = chunk.get("source", "Unknown")
            
            # Truncate text to max 800 characters to reduce token usage
            if text and len(text) > 800:
                text = text[:800] + "..."
            
            context_parts.append(
                f"[Source {i}: {source} (Relevance: {score:.2f})]\n{text}"
            )
        
        return "\n\n".join(context_parts)
    
    def _build_prompt(self, query: str, context: str, confidence: float = 1.0) -> str:
        """Build the complete prompt for LLM with confidence-based warnings"""
        
        # Add warning if confidence is low
        confidence_note = ""
        if confidence < 0.5:
            confidence_note = "\n⚠️ NOTE: The retrieved context has limited relevance. Only use information that is explicitly present in the documents."
        
        return f"""Based on the following retrieved document excerpts, answer the user's question accurately and concisely.{confidence_note}

User Question: {query}

Document Context:
{context}

Instructions:
1. ONLY answer based on the provided document context
2. If the context doesn't contain relevant information, explicitly state: "This information is not available in the provided documents."
3. Do NOT use general knowledge or external information
4. Cite the sources when relevant
5. Be concise but comprehensive
6. If multiple perspectives exist in the context, present them fairly

Answer:"""
    
    def _extract_sources(self, chunks: List[dict]) -> List[dict]:
        """Extract source information from chunks with metadata"""
        sources = []
        seen = set()
        
        logger.info(f"Extracting sources from {len(chunks)} chunks")
        
        for i, chunk in enumerate(chunks):
            chunk_id = chunk.get("id") or chunk.get("chunk_id", "")
            metadata = chunk.get("metadata", {})
            
            logger.info(f"Chunk {i}: id={chunk_id}, metadata keys={list(metadata.keys()) if metadata else 'EMPTY'}")
            
            # Use metadata if available, otherwise use source field
            filename = metadata.get("filename", chunk.get("source", "Unknown"))
            page_number = metadata.get("page_number")
            section = metadata.get("section")
            relevance = chunk.get("similarity_score", 0)
            
            logger.info(f"Chunk {i}: filename={filename}, page={page_number}, section={section}")
            
            source_key = f"{filename}_{chunk_id}"
            if source_key not in seen:
                source_entry = {
                    "id": chunk_id,
                    "filename": filename,
                    "relevance": relevance
                }
                if page_number:
                    source_entry["page_number"] = page_number
                if section:
                    source_entry["section"] = section
                    
                sources.append(source_entry)
                seen.add(source_key)
        
        logger.info(f"Extracted {len(sources)} unique sources: {[s.get('filename') for s in sources]}")
        return sources
    
    def _calculate_confidence(self, chunks: List[dict]) -> float:
        """Calculate confidence score based on retrieval quality"""
        if not chunks:
            return 0.0
        
        # Average similarity score
        avg_similarity = sum(
            chunk.get("similarity_score", 0) for chunk in chunks
        ) / len(chunks)
        
        # Boost confidence with more chunks
        chunk_count_factor = min(len(chunks) / 5, 1.0)  # Max boost at 5 chunks
        
        # Combine factors
        confidence = (avg_similarity * 0.7) + (chunk_count_factor * 0.3)
        
        return round(confidence, 2)


class LLMAnswerService:
    """Service to manage LLM answer generation"""
    
    def __init__(self, settings: Settings):
        """Initialize LLM service"""
        self.enabled = settings.LLM_ANSWER_GENERATION_ENABLED
        self.generator = GroqAnswerGenerator(settings) if self.enabled else None
    
    def generate_answer_from_search(
        self,
        query: str,
        search_results: List[dict],
        tenant_id: str = "system"
    ) -> dict:
        """
        Generate answer from search results
        
        Args:
            query: User query
            search_results: Results from vector search
            tenant_id: Tenant ID
            
        Returns:
            dict with answer and metadata
        """
        if not self.enabled or not self.generator:
            logger.warning("LLM answer generation is disabled")
            return {
                "answer": None,
                "enabled": False,
                "message": "LLM answer generation is disabled"
            }
        
        # Format chunks for LLM - preserve full metadata
        chunks = [
            {
                "text": result.get("text", ""),
                "id": result.get("id", ""),
                "similarity_score": result.get("similarity_score", 0),
                "metadata": result.get("metadata", {})  # Preserve full metadata
            }
            for result in search_results
        ]
        
        logger.info(f"[{tenant_id}] Prepared {len(chunks)} chunks for LLM with metadata")
        return self.generator.generate_answer(query, chunks, tenant_id)
