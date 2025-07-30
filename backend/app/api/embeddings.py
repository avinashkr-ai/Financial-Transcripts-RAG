from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any
import logging

from ..models.query import EmbeddingRequest
from ..models.response import EmbeddingStatus
from ..services.embedding_service import get_embedding_service
from ..services.chroma_service import get_chroma_service
from ..core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Global status tracking for embedding generation
embedding_status = {
    "status": "idle",
    "progress": 0.0,
    "total_documents": 0,
    "processed_documents": 0,
    "current_company": None,
    "estimated_time_remaining": None,
    "error": None
}


@router.get("/status", response_model=EmbeddingStatus)
async def get_embedding_status() -> EmbeddingStatus:
    """
    Get the current status of embedding generation process.
    
    Returns information about:
    - Current processing status
    - Progress percentage
    - Documents processed/remaining
    - Estimated completion time
    """
    try:
        global embedding_status
        
        return EmbeddingStatus(
            status=embedding_status["status"],
            progress=embedding_status["progress"],
            total_documents=embedding_status["total_documents"],
            processed_documents=embedding_status["processed_documents"],
            current_company=embedding_status["current_company"],
            estimated_time_remaining=embedding_status["estimated_time_remaining"]
        )
        
    except Exception as e:
        logger.error(f"Failed to get embedding status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve embedding status: {str(e)}"
        )


@router.post("/create")
async def create_embeddings(
    request: EmbeddingRequest,
    background_tasks: BackgroundTasks,
    embedding_service=Depends(get_embedding_service),
    chroma_service=Depends(get_chroma_service),
    settings=Depends(get_settings)
) -> Dict[str, Any]:
    """
    Start the embedding generation process for financial transcripts.
    
    This endpoint:
    1. Processes transcript files from the Transcripts directory
    2. Generates embeddings using sentence transformers
    3. Stores embeddings in ChromaDB
    4. Runs as a background task with status tracking
    """
    try:
        global embedding_status
        
        # Check if already processing
        if embedding_status["status"] == "processing":
            raise HTTPException(
                status_code=409,
                detail="Embedding generation is already in progress"
            )
        
        # Reset status
        embedding_status.update({
            "status": "starting",
            "progress": 0.0,
            "total_documents": 0,
            "processed_documents": 0,
            "current_company": None,
            "estimated_time_remaining": None,
            "error": None
        })
        
        # Start background task
        background_tasks.add_task(
            _generate_embeddings_background,
            request,
            embedding_service,
            chroma_service,
            settings
        )
        
        logger.info("Started embedding generation background task")
        
        return {
            "message": "Embedding generation started",
            "status": "starting",
            "force_recreate": request.force_recreate,
            "companies": [c.value for c in request.companies] if request.companies else "all",
            "batch_size": request.batch_size
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start embedding generation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start embedding generation: {str(e)}"
        )


@router.delete("/clear")
async def clear_embeddings(
    company: str = None,
    chroma_service=Depends(get_chroma_service),
    embedding_service=Depends(get_embedding_service)
) -> Dict[str, Any]:
    """
    Clear embeddings for a specific company or all companies.
    
    This endpoint:
    1. Removes embeddings from ChromaDB
    2. Clears embedding cache
    3. Provides cleanup statistics
    """
    try:
        if company:
            # Clear specific company
            success = chroma_service.delete_company_data(company.upper())
            if success:
                message = f"Cleared embeddings for {company.upper()}"
            else:
                message = f"Failed to clear embeddings for {company.upper()}"
        else:
            # Clear all companies
            companies = list(chroma_service.company_names.keys())
            cleared_count = 0
            
            for comp in companies:
                if chroma_service.delete_company_data(comp):
                    cleared_count += 1
            
            # Clear embedding cache
            cache_cleared = embedding_service.clear_cache()
            
            message = f"Cleared embeddings for {cleared_count}/{len(companies)} companies and {cache_cleared} cached embeddings"
        
        logger.info(f"Embeddings cleared: {message}")
        
        return {
            "message": message,
            "company": company or "all",
            "timestamp": str(import_datetime().now())
        }
        
    except Exception as e:
        logger.error(f"Failed to clear embeddings: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear embeddings: {str(e)}"
        )


@router.get("/cache/info")
async def get_cache_info(
    embedding_service=Depends(get_embedding_service)
) -> Dict[str, Any]:
    """
    Get information about the embedding cache.
    
    Returns:
    - Number of cached embeddings
    - Cache size in MB
    - Cache directory path
    - Model information
    """
    try:
        cache_info = embedding_service.get_cache_info()
        return cache_info
        
    except Exception as e:
        logger.error(f"Failed to get cache info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve cache information: {str(e)}"
        )


async def _generate_embeddings_background(
    request: EmbeddingRequest,
    embedding_service,
    chroma_service,
    settings
):
    """Background task for generating embeddings"""
    global embedding_status
    
    try:
        import os
        import time
        from pathlib import Path
        
        logger.info("Starting background embedding generation")
        
        # Update status
        embedding_status["status"] = "processing"
        
        # Get transcript directory
        transcripts_dir = Path(settings.transcripts_directory)
        
        if not transcripts_dir.exists():
            raise Exception(f"Transcripts directory not found: {transcripts_dir}")
        
        # Determine companies to process
        if request.companies:
            companies = [c.value for c in request.companies]
        else:
            companies = list(chroma_service.company_names.keys())
        
        # Count total documents
        total_docs = 0
        for company in companies:
            company_dir = transcripts_dir / company
            if company_dir.exists():
                total_docs += len(list(company_dir.glob("*.txt")))
        
        embedding_status["total_documents"] = total_docs
        
        processed_docs = 0
        start_time = time.time()
        
        # Process each company
        for company in companies:
            embedding_status["current_company"] = company
            
            company_dir = transcripts_dir / company
            if not company_dir.exists():
                logger.warning(f"Company directory not found: {company_dir}")
                continue
            
            # Get transcript files
            transcript_files = list(company_dir.glob("*.txt"))
            
            for transcript_file in transcript_files:
                try:
                    # Read transcript
                    with open(transcript_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extract metadata from filename
                    filename = transcript_file.stem
                    parts = filename.split('-')
                    if len(parts) >= 3:
                        date_str = f"{parts[0]}-{parts[1]}-{parts[2]}"
                    else:
                        date_str = "unknown"
                    
                    # Split content into chunks (simple sentence-based chunking)
                    chunks = _split_into_chunks(content, max_chunk_size=512)
                    
                    # Create document ID
                    document_id = f"{company.lower()}_{filename}"
                    
                    # Prepare metadata
                    metadata = {
                        "date": date_str,
                        "company": company,
                        "filename": transcript_file.name,
                        "quarter": _extract_quarter_from_filename(filename)
                    }
                    
                    # Store in ChromaDB
                    success = chroma_service.store_document_chunks(
                        company=company,
                        document_id=document_id,
                        chunks=chunks,
                        metadata=metadata
                    )
                    
                    if success:
                        logger.info(f"Processed {transcript_file.name} - {len(chunks)} chunks")
                    else:
                        logger.error(f"Failed to process {transcript_file.name}")
                    
                    processed_docs += 1
                    
                    # Update progress
                    progress = (processed_docs / total_docs) * 100
                    embedding_status["progress"] = round(progress, 1)
                    embedding_status["processed_documents"] = processed_docs
                    
                    # Estimate remaining time
                    elapsed_time = time.time() - start_time
                    if processed_docs > 0:
                        avg_time_per_doc = elapsed_time / processed_docs
                        remaining_docs = total_docs - processed_docs
                        estimated_remaining = avg_time_per_doc * remaining_docs
                        
                        # Convert to human readable format
                        if estimated_remaining < 60:
                            time_str = f"{int(estimated_remaining)}s"
                        elif estimated_remaining < 3600:
                            time_str = f"{int(estimated_remaining // 60)}m {int(estimated_remaining % 60)}s"
                        else:
                            hours = int(estimated_remaining // 3600)
                            minutes = int((estimated_remaining % 3600) // 60)
                            time_str = f"{hours}h {minutes}m"
                        
                        embedding_status["estimated_time_remaining"] = time_str
                    
                except Exception as e:
                    logger.error(f"Failed to process {transcript_file}: {e}")
                    continue
        
        # Completion
        embedding_status.update({
            "status": "completed",
            "progress": 100.0,
            "current_company": None,
            "estimated_time_remaining": None
        })
        
        total_time = time.time() - start_time
        logger.info(f"Embedding generation completed in {total_time:.2f}s")
        
    except Exception as e:
        logger.error(f"Background embedding generation failed: {e}")
        embedding_status.update({
            "status": "error",
            "error": str(e)
        })


def _split_into_chunks(text: str, max_chunk_size: int = 512) -> list[str]:
    """Split text into chunks based on sentences"""
    import re
    
    # Split by sentences
    sentences = re.split(r'[.!?]+', text)
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        # Check if adding this sentence would exceed max chunk size
        if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            current_chunk += " " + sentence if current_chunk else sentence
    
    # Add the last chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks


def _extract_quarter_from_filename(filename: str) -> str:
    """Extract quarter information from filename"""
    import re
    
    # Pattern for dates in filename
    date_patterns = [
        r'(\d{4})-(\w{3})-\d{2}',  # 2020-Apr-30
        r'(\w{3})-(\d{4})',        # Apr-2020
    ]
    
    month_to_quarter = {
        'Jan': 'Q1', 'Feb': 'Q1', 'Mar': 'Q1',
        'Apr': 'Q2', 'May': 'Q2', 'Jun': 'Q2',
        'Jul': 'Q3', 'Aug': 'Q3', 'Sep': 'Q3',
        'Oct': 'Q4', 'Nov': 'Q4', 'Dec': 'Q4'
    }
    
    for pattern in date_patterns:
        match = re.search(pattern, filename)
        if match:
            if pattern.startswith(r'(\d{4})'):
                year, month = match.groups()
            else:
                month, year = match.groups()
            
            quarter = month_to_quarter.get(month, 'Q1')
            return f"{quarter} {year}"
    
    return "Unknown"


def import_datetime():
    """Helper to import datetime for string formatting"""
    from datetime import datetime
    return datetime 