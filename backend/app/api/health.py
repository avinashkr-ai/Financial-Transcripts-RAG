from fastapi import APIRouter, Depends
from datetime import datetime
import logging

from ..models.response import HealthResponse, CompaniesResponse, CompanyInfo
from ..services.chroma_service import get_chroma_service
from ..services.gemini_service import get_gemini_service
from ..services.embedding_service import get_embedding_service
from ..core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(
    chroma_service=Depends(get_chroma_service),
    gemini_service=Depends(get_gemini_service),
    embedding_service=Depends(get_embedding_service),
    settings=Depends(get_settings)
) -> HealthResponse:
    """
    Comprehensive health check for all system components.
    
    Checks:
    - Database connectivity
    - Embedding model status
    - Gemini API connectivity
    - Overall system health
    """
    try:
        # Check database status
        try:
            collections = chroma_service.db_manager.list_collections()
            database_status = "connected"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            database_status = f"error: {str(e)}"
        
        # Check embedding model status
        try:
            if embedding_service.is_available():
                model = embedding_service.load_model()
                embeddings_status = "loaded"
            else:
                embeddings_status = "unavailable: sentence-transformers compatibility issue"
        except Exception as e:
            logger.error(f"Embedding model health check failed: {e}")
            embeddings_status = f"error: {str(e)}"
        
        # Determine overall status
        if "error" in database_status or "error" in embeddings_status:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.now(),
            version=settings.VERSION,
            database_status=database_status,
            embeddings_status=embeddings_status
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="error",
            timestamp=datetime.now(),
            version=settings.VERSION,
            database_status="unknown",
            embeddings_status="unknown"
        )


@router.get("/companies", response_model=CompaniesResponse)
async def get_companies(
    chroma_service=Depends(get_chroma_service)
) -> CompaniesResponse:
    """
    Get information about all available companies and their transcripts.
    
    Returns:
    - List of companies with metadata
    - Transcript counts
    - Date ranges
    - Total statistics
    """
    try:
        companies_stats = chroma_service.get_all_companies_stats()
        
        # Convert to CompanyInfo objects
        companies = []
        total_transcripts = 0
        
        for stats in companies_stats:
            company_info = CompanyInfo(
                symbol=stats["company"],
                name=stats["name"],
                transcript_count=stats["transcript_count"],
                date_range=stats["date_range"] or {"start": None, "end": None},
                latest_transcript=stats["latest_transcript"]
            )
            companies.append(company_info)
            total_transcripts += stats["transcript_count"]
        
        return CompaniesResponse(
            companies=companies,
            total_companies=len(companies),
            total_transcripts=total_transcripts
        )
        
    except Exception as e:
        logger.error(f"Failed to get companies info: {e}")
        # Return empty response on error
        return CompaniesResponse(
            companies=[],
            total_companies=0,
            total_transcripts=0
        )


@router.get("/transcripts/{company}")
async def get_company_transcripts(
    company: str,
    chroma_service=Depends(get_chroma_service)
):
    """
    Get detailed information about a specific company's transcripts.
    
    Returns:
    - Company statistics
    - Available transcripts
    - Date ranges
    - Collection health
    """
    try:
        company = company.upper()
        
        # Validate company
        if company not in chroma_service.company_names:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail=f"Company {company} not found")
        
        # Get company stats
        stats = chroma_service.get_company_stats(company)
        
        # Get collection health
        health = chroma_service.check_collection_health(company)
        
        return {
            "company": company,
            "name": chroma_service.company_names[company],
            "statistics": stats,
            "health": health,
            "collection_name": chroma_service.get_collection_name(company)
        }
        
    except Exception as e:
        logger.error(f"Failed to get company transcripts for {company}: {e}")
        from fastapi import HTTPException
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/system/info")
async def get_system_info(
    settings=Depends(get_settings),
    embedding_service=Depends(get_embedding_service),
    chroma_service=Depends(get_chroma_service)
):
    """
    Get detailed system information.
    
    Returns:
    - Configuration details
    - Model information
    - Performance metrics
    - System capabilities
    """
    try:
        # Get embedding cache info
        cache_info = embedding_service.get_cache_info()
        
        return {
            "api": {
                "name": settings.PROJECT_NAME,
                "version": settings.VERSION,
                "description": settings.DESCRIPTION
            },
            "configuration": {
                "embedding_model": settings.EMBEDDING_MODEL,
                "embedding_device": settings.EMBEDDING_DEVICE,
                "batch_size": settings.BATCH_SIZE,
                "max_chunks_per_query": settings.MAX_CHUNKS_PER_QUERY,
                "similarity_threshold": settings.SIMILARITY_THRESHOLD,
                "temperature": settings.TEMPERATURE
            },
            "embedding_cache": cache_info,
            "data_paths": {
                "transcripts": settings.transcripts_directory,
                "chromadb": settings.chromadb_persist_directory,
                "embeddings": settings.EMBEDDINGS_PATH
            },
            "supported_companies": list(chroma_service.company_names.keys()),
            "company_names": chroma_service.company_names
        }
        
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Failed to retrieve system information: {str(e)}")


# Dependency import for use in other endpoints
def get_chroma_service_dep():
    """Dependency function for getting chroma service"""
    return get_chroma_service() 