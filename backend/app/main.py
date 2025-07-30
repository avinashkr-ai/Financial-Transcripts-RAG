from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
from datetime import datetime

from .core.config import get_settings
from .api import query, embeddings, health

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Financial Transcripts RAG API")
    logger.info(f"API Version: {settings.VERSION}")
    logger.info(f"Embedding Model: {settings.EMBEDDING_MODEL}")
    
    # Validate paths
    if not settings.validate_paths():
        logger.warning("Some required paths are missing")
    
    # Initialize services (lazy loading will handle actual initialization)
    logger.info("Services initialized (lazy loading)")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Financial Transcripts RAG API")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time, 4))
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )


# HTTP exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": f"HTTP {exc.status_code}",
            "message": exc.detail,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )


# Include API routers
app.include_router(
    query.router,
    prefix=settings.API_V1_PREFIX,
    tags=["RAG Queries"],
    responses={
        400: {"description": "Bad Request"},
        500: {"description": "Internal Server Error"}
    }
)

app.include_router(
    embeddings.router,
    prefix=f"{settings.API_V1_PREFIX}/embeddings",
    tags=["Embeddings"],
    responses={
        400: {"description": "Bad Request"},
        409: {"description": "Conflict"},
        500: {"description": "Internal Server Error"}
    }
)

app.include_router(
    health.router,
    tags=["Health & System"],
    responses={
        500: {"description": "Internal Server Error"}
    }
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Financial Transcripts RAG API",
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
        "docs_url": "/docs",
        "health_check": "/health",
        "api_prefix": settings.API_V1_PREFIX,
        "timestamp": datetime.now().isoformat()
    }


# API information endpoint
@app.get("/info")
async def api_info():
    """Detailed API information"""
    return {
        "api": {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "description": settings.DESCRIPTION
        },
        "endpoints": {
            "query": f"{settings.API_V1_PREFIX}/query",
            "search": f"{settings.API_V1_PREFIX}/search",
            "insights": f"{settings.API_V1_PREFIX}/insights",
            "companies": "/companies",
            "health": "/health",
            "embeddings_status": f"{settings.API_V1_PREFIX}/embeddings/status",
            "embeddings_create": f"{settings.API_V1_PREFIX}/embeddings/create"
        },
        "features": [
            "RAG-based Q&A on financial transcripts",
            "Vector similarity search",
            "Multi-company filtering",
            "Date range filtering",
            "Automated insight generation",
            "Real-time embedding generation",
            "Comprehensive health monitoring"
        ],
        "supported_companies": [
            "AAPL", "AMD", "AMZN", "ASML", "CSCO", 
            "GOOGL", "INTC", "MSFT", "MU", "NVDA"
        ],
        "data_coverage": "2016-2020 earnings call transcripts",
        "models": {
            "embedding": settings.EMBEDDING_MODEL,
            "llm": "Google Gemini Pro"
        }
    }


# Startup message
if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {settings.BACKEND_HOST}:{settings.BACKEND_PORT}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=True,
        log_level="info"
    ) 