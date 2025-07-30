from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Financial Transcripts RAG API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "RAG application for querying financial earnings call transcripts"
    
    # Server Configuration
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = ["http://localhost:8501", "http://127.0.0.1:8501"]
    
    # Google Gemini Pro API
    GOOGLE_API_KEY: str
    
    # ChromaDB Configuration
    CHROMADB_PATH: str = "./data/chromadb"
    CHROMADB_HOST: str = "localhost"
    CHROMADB_PORT: int = 8000
    
    # Embedding Configuration
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DEVICE: str = "cpu"
    BATCH_SIZE: int = 32
    
    # RAG Pipeline Settings
    MAX_CHUNKS_PER_QUERY: int = 5
    SIMILARITY_THRESHOLD: float = 0.7
    TEMPERATURE: float = 0.7
    
    # Data Paths
    TRANSCRIPTS_PATH: str = "../Transcripts"
    DATA_PATH: str = "./data"
    EMBEDDINGS_PATH: str = "./data/embeddings"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def chromadb_persist_directory(self) -> str:
        """Get the ChromaDB persistence directory path"""
        return str(Path(self.CHROMADB_PATH).resolve())
    
    @property
    def transcripts_directory(self) -> str:
        """Get the transcripts directory path"""
        return str(Path(self.TRANSCRIPTS_PATH).resolve())
    
    def validate_paths(self) -> bool:
        """Validate that required paths exist"""
        required_paths = [
            Path(self.TRANSCRIPTS_PATH),
            Path(self.DATA_PATH),
        ]
        
        for path in required_paths:
            if not path.exists():
                print(f"Warning: Required path does not exist: {path}")
                return False
        return True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Dependency to get settings instance"""
    return settings 