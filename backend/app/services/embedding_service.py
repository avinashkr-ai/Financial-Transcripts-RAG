from typing import List, Dict, Any, Optional
import numpy as np
import logging
import os
from pathlib import Path
import pickle
import hashlib

from ..core.config import get_settings

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"SentenceTransformers not available: {e}")
    SentenceTransformer = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and managing text embeddings"""
    
    def __init__(self):
        self.settings = get_settings()
        self.model: Optional[SentenceTransformer] = None
        self.model_name = self.settings.EMBEDDING_MODEL
        self.device = self.settings.EMBEDDING_DEVICE
        self.batch_size = self.settings.BATCH_SIZE
        
        # Cache for embeddings
        self.cache_dir = Path(self.settings.EMBEDDINGS_PATH)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def is_available(self) -> bool:
        """Check if the embedding service is available"""
        return SENTENCE_TRANSFORMERS_AVAILABLE
    
    def load_model(self) -> SentenceTransformer:
        """Load or get cached sentence transformer model"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "SentenceTransformers is not available. "
                "Please install compatible sentence-transformers package or fix compatibility issues."
            )
            
        if self.model is None:
            try:
                logger.info(f"Loading embedding model: {self.model_name}")
                self.model = SentenceTransformer(self.model_name, device=self.device)
                logger.info(f"Model loaded successfully on device: {self.device}")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise
        
        return self.model
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings from the model"""
        model = self.load_model()
        return model.get_sentence_embedding_dimension()
    
    def encode_texts(self, texts: List[str], show_progress: bool = True) -> np.ndarray:
        """Encode a list of texts into embeddings"""
        if not texts:
            return np.array([])
        
        try:
            model = self.load_model()
            
            logger.info(f"Encoding {len(texts)} texts with batch size {self.batch_size}")
            
            embeddings = model.encode(
                texts,
                batch_size=self.batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True,
                normalize_embeddings=True  # Normalize for better similarity search
            )
            
            logger.info(f"Generated embeddings shape: {embeddings.shape}")
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to encode texts: {e}")
            raise
    
    def encode_single_text(self, text: str) -> np.ndarray:
        """Encode a single text into embedding"""
        return self.encode_texts([text], show_progress=False)[0]
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Compute cosine similarity between two embeddings"""
        try:
            # Ensure embeddings are normalized
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Compute cosine similarity
            similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to compute similarity: {e}")
            return 0.0
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path for embedding"""
        return self.cache_dir / f"{cache_key}.pkl"
    
    def save_embedding_to_cache(self, text: str, embedding: np.ndarray) -> None:
        """Save embedding to cache"""
        try:
            cache_key = self._get_cache_key(text)
            cache_path = self._get_cache_path(cache_key)
            
            with open(cache_path, 'wb') as f:
                pickle.dump({
                    'text': text,
                    'embedding': embedding,
                    'model': self.model_name
                }, f)
                
        except Exception as e:
            logger.warning(f"Failed to save embedding to cache: {e}")
    
    def load_embedding_from_cache(self, text: str) -> Optional[np.ndarray]:
        """Load embedding from cache if available"""
        try:
            cache_key = self._get_cache_key(text)
            cache_path = self._get_cache_path(cache_key)
            
            if not cache_path.exists():
                return None
            
            with open(cache_path, 'rb') as f:
                data = pickle.load(f)
            
            # Check if the model matches
            if data.get('model') != self.model_name:
                return None
            
            return data['embedding']
            
        except Exception as e:
            logger.warning(f"Failed to load embedding from cache: {e}")
            return None
    
    def encode_with_cache(self, texts: List[str], use_cache: bool = True) -> np.ndarray:
        """Encode texts with caching support"""
        if not use_cache:
            return self.encode_texts(texts)
        
        embeddings = []
        texts_to_encode = []
        indices_to_encode = []
        
        # Check cache for each text
        for i, text in enumerate(texts):
            cached_embedding = self.load_embedding_from_cache(text)
            if cached_embedding is not None:
                embeddings.append(cached_embedding)
            else:
                embeddings.append(None)
                texts_to_encode.append(text)
                indices_to_encode.append(i)
        
        # Encode uncached texts
        if texts_to_encode:
            logger.info(f"Encoding {len(texts_to_encode)} uncached texts")
            new_embeddings = self.encode_texts(texts_to_encode)
            
            # Save to cache and update results
            for i, (text, embedding) in enumerate(zip(texts_to_encode, new_embeddings)):
                self.save_embedding_to_cache(text, embedding)
                embeddings[indices_to_encode[i]] = embedding
        
        return np.array(embeddings)
    
    def clear_cache(self) -> int:
        """Clear embedding cache"""
        try:
            cache_files = list(self.cache_dir.glob("*.pkl"))
            for cache_file in cache_files:
                cache_file.unlink()
            
            logger.info(f"Cleared {len(cache_files)} cached embeddings")
            return len(cache_files)
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return 0
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about embedding cache"""
        try:
            cache_files = list(self.cache_dir.glob("*.pkl"))
            total_size = sum(f.stat().st_size for f in cache_files)
            
            return {
                "cached_embeddings": len(cache_files),
                "cache_size_mb": round(total_size / (1024 * 1024), 2),
                "cache_directory": str(self.cache_dir),
                "model_name": self.model_name
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache info: {e}")
            return {
                "cached_embeddings": 0,
                "cache_size_mb": 0,
                "cache_directory": str(self.cache_dir),
                "model_name": self.model_name
            }


# Global embedding service instance
embedding_service = EmbeddingService()


def get_embedding_service() -> EmbeddingService:
    """Dependency to get embedding service instance"""
    return embedding_service 