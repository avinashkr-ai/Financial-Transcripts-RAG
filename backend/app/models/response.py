from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class SourceDocument(BaseModel):
    """Information about a source document"""
    company: str = Field(..., description="Company symbol (e.g., AAPL)")
    date: str = Field(..., description="Transcript date")
    quarter: Optional[str] = Field(None, description="Financial quarter (e.g., Q3 2020)")
    chunk: str = Field(..., description="Relevant text excerpt")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score (0.0-1.0)")
    document_id: str = Field(..., description="Unique document identifier")
    chunk_index: Optional[int] = Field(None, description="Index of chunk within document")
    
    class Config:
        schema_extra = {
            "example": {
                "company": "AAPL",
                "date": "2020-07-30",
                "quarter": "Q3 2020",
                "chunk": "We continue to see strong performance in our Services business...",
                "similarity_score": 0.85,
                "document_id": "aapl_2020_q3_001",
                "chunk_index": 5
            }
        }


class QueryMetadata(BaseModel):
    """Metadata about query processing"""
    processing_time: str = Field(..., description="Time taken to process query")
    total_chunks_searched: int = Field(..., description="Total number of chunks searched")
    model_used: str = Field(..., description="Embedding model used")
    llm_model: str = Field(..., description="LLM model used for generation")
    similarity_threshold: float = Field(..., description="Similarity threshold applied")
    max_results: int = Field(..., description="Maximum results requested")
    
    class Config:
        schema_extra = {
            "example": {
                "processing_time": "1.2s",
                "total_chunks_searched": 1250,
                "model_used": "all-MiniLM-L6-v2",
                "llm_model": "gemini-pro",
                "similarity_threshold": 0.7,
                "max_results": 5
            }
        }


class QueryResponse(BaseModel):
    """Response model for RAG queries"""
    query: str = Field(..., description="Original user question")
    answer: str = Field(..., description="Generated answer based on retrieved context")
    sources: List[SourceDocument] = Field([], description="Relevant source documents")
    metadata: QueryMetadata = Field(..., description="Query processing metadata")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "What were Apple's main concerns about supply chain in 2020?",
                "answer": "Based on Apple's 2020 earnings calls, the main supply chain concerns were...",
                "sources": [
                    {
                        "company": "AAPL",
                        "date": "2020-07-30",
                        "quarter": "Q3 2020",
                        "chunk": "Supply chain challenges due to COVID-19 impacted our operations...",
                        "similarity_score": 0.85,
                        "document_id": "aapl_2020_q3_001",
                        "chunk_index": 5
                    }
                ],
                "metadata": {
                    "processing_time": "1.2s",
                    "total_chunks_searched": 1250,
                    "model_used": "all-MiniLM-L6-v2",
                    "llm_model": "gemini-pro",
                    "similarity_threshold": 0.7,
                    "max_results": 5
                }
            }
        }


class SearchResult(BaseModel):
    """Single search result"""
    document_id: str = Field(..., description="Document identifier")
    company: str = Field(..., description="Company symbol")
    date: str = Field(..., description="Document date")
    content: str = Field(..., description="Document content")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class SearchResponse(BaseModel):
    """Response model for vector similarity search"""
    query: str = Field(..., description="Original search query")
    results: List[SearchResult] = Field([], description="Search results")
    total_results: int = Field(..., description="Total number of results found")
    processing_time: str = Field(..., description="Time taken to process search")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "revenue growth cloud services",
                "results": [
                    {
                        "document_id": "msft_2020_q4_003",
                        "company": "MSFT",
                        "date": "2020-07-22",
                        "content": "Azure revenue grew 47% year over year...",
                        "similarity_score": 0.92,
                        "metadata": {"quarter": "Q4 2020"}
                    }
                ],
                "total_results": 15,
                "processing_time": "0.8s"
            }
        }


class CompanyInfo(BaseModel):
    """Information about a company's transcripts"""
    symbol: str = Field(..., description="Company symbol")
    name: str = Field(..., description="Company full name")
    transcript_count: int = Field(..., description="Number of available transcripts")
    date_range: Dict[str, str] = Field(..., description="Available date range")
    latest_transcript: Optional[str] = Field(None, description="Date of latest transcript")
    
    class Config:
        schema_extra = {
            "example": {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "transcript_count": 19,
                "date_range": {"start": "2016-01-26", "end": "2020-07-30"},
                "latest_transcript": "2020-07-30"
            }
        }


class CompaniesResponse(BaseModel):
    """Response model for companies endpoint"""
    companies: List[CompanyInfo] = Field(..., description="List of available companies")
    total_companies: int = Field(..., description="Total number of companies")
    total_transcripts: int = Field(..., description="Total number of transcripts")
    
    class Config:
        schema_extra = {
            "example": {
                "companies": [
                    {
                        "symbol": "AAPL",
                        "name": "Apple Inc.",
                        "transcript_count": 19,
                        "date_range": {"start": "2016-01-26", "end": "2020-07-30"},
                        "latest_transcript": "2020-07-30"
                    }
                ],
                "total_companies": 10,
                "total_transcripts": 187
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Current timestamp")
    version: str = Field(..., description="API version")
    database_status: str = Field(..., description="Database connection status")
    embeddings_status: str = Field(..., description="Embedding model status")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2023-12-01T12:00:00Z",
                "version": "1.0.0",
                "database_status": "connected",
                "embeddings_status": "loaded"
            }
        }


class EmbeddingStatus(BaseModel):
    """Status of embedding generation"""
    status: str = Field(..., description="Current status")
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)")
    total_documents: Optional[int] = Field(None, description="Total documents to process")
    processed_documents: Optional[int] = Field(None, description="Documents processed")
    current_company: Optional[str] = Field(None, description="Currently processing company")
    estimated_time_remaining: Optional[str] = Field(None, description="Estimated time remaining")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "processing",
                "progress": 45.5,
                "total_documents": 187,
                "processed_documents": 85,
                "current_company": "AAPL",
                "estimated_time_remaining": "5m 30s"
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    
    class Config:
        schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid company symbol provided",
                "details": {"invalid_symbols": ["INVALID"]}
            }
        } 