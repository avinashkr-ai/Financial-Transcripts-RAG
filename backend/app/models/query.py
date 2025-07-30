from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class CompanySymbol(str, Enum):
    """Valid company symbols"""
    AAPL = "AAPL"
    AMD = "AMD"
    AMZN = "AMZN"
    ASML = "ASML"
    CSCO = "CSCO"
    GOOGL = "GOOGL"
    INTC = "INTC"
    MSFT = "MSFT"
    MU = "MU"
    NVDA = "NVDA"


class DateRange(BaseModel):
    """Date range filter for queries"""
    start: Optional[str] = Field(None, description="Start date (YYYY-MM-DD format)")
    end: Optional[str] = Field(None, description="End date (YYYY-MM-DD format)")
    
    @validator('start', 'end')
    def validate_date_format(cls, v):
        if v is not None:
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                raise ValueError('Date must be in YYYY-MM-DD format')
        return v


class QueryRequest(BaseModel):
    """Request model for RAG queries"""
    question: str = Field(..., min_length=1, max_length=1000, description="User question about financial transcripts")
    company_filter: Optional[List[CompanySymbol]] = Field(
        None, 
        description="Filter results by specific companies",
        example=["AAPL", "MSFT"]
    )
    date_range: Optional[DateRange] = Field(None, description="Filter results by date range")
    max_results: int = Field(5, ge=1, le=20, description="Maximum number of relevant chunks to retrieve")
    similarity_threshold: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=1.0, 
        description="Minimum similarity score for results (0.0-1.0)"
    )
    temperature: Optional[float] = Field(
        None,
        ge=0.0,
        le=2.0,
        description="LLM temperature for response generation (0.0-2.0)"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "question": "What were Apple's main concerns about supply chain in 2020?",
                "company_filter": ["AAPL"],
                "date_range": {
                    "start": "2020-01-01",
                    "end": "2020-12-31"
                },
                "max_results": 5,
                "similarity_threshold": 0.7,
                "temperature": 0.7
            }
        }


class SearchRequest(BaseModel):
    """Request model for direct vector similarity search"""
    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    company_filter: Optional[List[CompanySymbol]] = Field(None, description="Filter by companies")
    max_results: int = Field(10, ge=1, le=50, description="Maximum number of results")
    similarity_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum similarity score")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "revenue growth cloud services",
                "company_filter": ["MSFT", "AMZN"],
                "max_results": 10,
                "similarity_threshold": 0.6
            }
        }


class EmbeddingRequest(BaseModel):
    """Request model for creating embeddings"""
    force_recreate: bool = Field(False, description="Force recreation of existing embeddings")
    companies: Optional[List[CompanySymbol]] = Field(None, description="Process specific companies only")
    batch_size: int = Field(32, ge=1, le=100, description="Batch size for processing")
    
    class Config:
        schema_extra = {
            "example": {
                "force_recreate": False,
                "companies": ["AAPL", "MSFT"],
                "batch_size": 32
            }
        } 