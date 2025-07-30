import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import Optional, List, Dict, Any
import logging
from pathlib import Path

from .config import get_settings

logger = logging.getLogger(__name__)


class ChromaDBManager:
    """Manages ChromaDB connections and collections"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client: Optional[chromadb.PersistentClient] = None
        self.collections: Dict[str, chromadb.Collection] = {}
    
    def initialize_client(self) -> chromadb.PersistentClient:
        """Initialize ChromaDB client"""
        try:
            # Ensure the persist directory exists
            persist_dir = Path(self.settings.chromadb_persist_directory)
            persist_dir.mkdir(parents=True, exist_ok=True)
            
            # Create ChromaDB client
            self.client = chromadb.PersistentClient(
                path=str(persist_dir),
                settings=ChromaSettings(
                    allow_reset=True,
                    anonymized_telemetry=False
                )
            )
            
            logger.info(f"ChromaDB client initialized with persist directory: {persist_dir}")
            return self.client
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}")
            raise
    
    def get_client(self) -> chromadb.PersistentClient:
        """Get or create ChromaDB client"""
        if self.client is None:
            self.client = self.initialize_client()
        return self.client
    
    def get_or_create_collection(self, collection_name: str) -> chromadb.Collection:
        """Get or create a ChromaDB collection"""
        if collection_name in self.collections:
            return self.collections[collection_name]
        
        try:
            client = self.get_client()
            
            # Try to get existing collection first
            try:
                collection = client.get_collection(collection_name)
                logger.info(f"Retrieved existing collection: {collection_name}")
            except ValueError:
                # Collection doesn't exist, create it
                collection = client.create_collection(
                    name=collection_name,
                    metadata={"description": f"Financial transcripts for {collection_name}"}
                )
                logger.info(f"Created new collection: {collection_name}")
            
            self.collections[collection_name] = collection
            return collection
            
        except Exception as e:
            logger.error(f"Failed to get/create collection {collection_name}: {e}")
            raise
    
    def list_collections(self) -> List[str]:
        """List all collections in ChromaDB"""
        try:
            client = self.get_client()
            collections = client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get information about a collection"""
        try:
            collection = self.get_or_create_collection(collection_name)
            count = collection.count()
            
            return {
                "name": collection_name,
                "count": count,
                "metadata": collection.metadata or {}
            }
        except Exception as e:
            logger.error(f"Failed to get collection info for {collection_name}: {e}")
            return {"name": collection_name, "count": 0, "metadata": {}}
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection"""
        try:
            client = self.get_client()
            client.delete_collection(collection_name)
            
            # Remove from cache
            if collection_name in self.collections:
                del self.collections[collection_name]
            
            logger.info(f"Deleted collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection {collection_name}: {e}")
            return False
    
    def reset_database(self) -> bool:
        """Reset the entire database (use with caution)"""
        try:
            client = self.get_client()
            client.reset()
            self.collections.clear()
            logger.warning("ChromaDB database has been reset")
            return True
        except Exception as e:
            logger.error(f"Failed to reset database: {e}")
            return False


# Global database manager instance
db_manager = ChromaDBManager()


def get_db_manager() -> ChromaDBManager:
    """Dependency to get database manager instance"""
    return db_manager 