from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging

from ..models.query import QueryRequest, SearchRequest
from ..models.response import QueryResponse, SearchResponse, SearchResult
from ..core.rag_pipeline import get_rag_pipeline
from ..services.chroma_service import get_chroma_service
from ..core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def process_rag_query(
    request: QueryRequest,
    rag_pipeline=Depends(get_rag_pipeline),
    chroma_service=Depends(get_chroma_service)
) -> QueryResponse:
    """
    Process a RAG query and return AI-generated response based on financial transcripts.
    
    This endpoint:
    1. Searches for relevant transcript chunks using semantic similarity
    2. Generates a comprehensive response using Gemini Pro
    3. Returns the answer with source attribution and metadata
    """
    try:
        logger.info(f"Received RAG query: {request.question[:100]}...")
        
        # Check if embedding services are available
        if not chroma_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="Embedding services are currently unavailable. "
                       "Please check that sentence-transformers is properly installed and configured."
            )
        
        # Validate request
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Process through RAG pipeline
        response = await rag_pipeline.process_query(request)
        
        logger.info(f"RAG query processed successfully")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process RAG query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while processing query: {str(e)}"
        )


@router.post("/search", response_model=SearchResponse)
async def vector_similarity_search(
    request: SearchRequest,
    chroma_service=Depends(get_chroma_service)
) -> SearchResponse:
    """
    Perform direct vector similarity search without LLM generation.
    
    This endpoint:
    1. Converts the query to embeddings
    2. Searches for similar document chunks
    3. Returns raw results with similarity scores
    """
    try:
        logger.info(f"Vector search query: {request.query[:100]}...")
        
        # Check if embedding services are available
        if not chroma_service.is_available():
            raise HTTPException(
                status_code=503,
                detail="Embedding services are currently unavailable. "
                       "Please check that sentence-transformers is properly installed and configured."
            )
        
        # Validate request
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        import time
        start_time = time.time()
        
        # Convert company filter
        company_filter = [c.value for c in request.company_filter] if request.company_filter else None
        
        # Search for similar chunks
        chunks = chroma_service.search_similar_chunks(
            query=request.query,
            company_filter=company_filter,
            max_results=request.max_results,
            similarity_threshold=request.similarity_threshold or 0.5
        )
        
        # Format results
        results = []
        for chunk in chunks:
            result = SearchResult(
                document_id=chunk.get("document_id", "unknown"),
                company=chunk.get("company", "Unknown"),
                date=chunk.get("date", "Unknown"),
                content=chunk.get("content", ""),
                similarity_score=round(chunk.get("similarity_score", 0.0), 3),
                metadata=chunk.get("metadata", {})
            )
            results.append(result)
        
        end_time = time.time()
        processing_time = f"{end_time - start_time:.2f}s"
        
        response = SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            processing_time=processing_time
        )
        
        logger.info(f"Vector search completed: {len(results)} results in {processing_time}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to perform vector search: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during search: {str(e)}"
        )


@router.post("/insights")
async def generate_insights(
    topic: str,
    companies: list[str] = None,
    date_start: str = None,
    date_end: str = None,
    max_sources: int = 10,
    rag_pipeline=Depends(get_rag_pipeline)
) -> Dict[str, Any]:
    """
    Generate insights on a specific topic across companies and time periods.
    
    This endpoint provides:
    1. Topic summary based on relevant transcripts
    2. Key points extraction
    3. Sentiment analysis
    4. Coverage statistics
    """
    try:
        logger.info(f"Generating insights for topic: {topic}")
        
        if not topic.strip():
            raise HTTPException(status_code=400, detail="Topic cannot be empty")
        
        # Build date range filter
        date_range = None
        if date_start or date_end:
            date_range = {}
            if date_start:
                date_range["start"] = date_start
            if date_end:
                date_range["end"] = date_end
        
        # Generate insights
        insights = rag_pipeline.generate_insights(
            topic=topic,
            companies=companies,
            date_range=date_range,
            max_sources=min(max_sources, 20)  # Limit max sources
        )
        
        logger.info(f"Generated insights for topic: {topic}")
        return insights
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate insights: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while generating insights: {str(e)}"
        ) 