import chromadb
from typing import List, Dict, Any, Optional, Tuple
import logging
import uuid
from datetime import datetime
import re

from ..core.database import get_db_manager
from ..services.embedding_service import get_embedding_service
from ..models.query import CompanySymbol

logger = logging.getLogger(__name__)


class ChromaService:
    """Service for ChromaDB vector database operations"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.embedding_service = get_embedding_service()
        
        # Check if embedding service is available
        self.embeddings_available = self.embedding_service.is_available()
        if not self.embeddings_available:
            logger.warning("Embedding service is not available. Vector operations will be disabled.")
        
        # Company name mapping
        self.company_names = {
            "AAPL": "Apple Inc.",
            "AMD": "Advanced Micro Devices Inc.",
            "AMZN": "Amazon.com Inc.",
            "ASML": "ASML Holding N.V.",
            "CSCO": "Cisco Systems Inc.",
            "GOOGL": "Alphabet Inc.",
            "INTC": "Intel Corporation",
            "MSFT": "Microsoft Corporation",
            "MU": "Micron Technology Inc.",
            "NVDA": "NVIDIA Corporation"
        }
    
    def is_available(self) -> bool:
        """Check if ChromaDB service with embeddings is available"""
        return self.embeddings_available
    
    def get_collection_name(self, company: str) -> str:
        """Get standardized collection name for company"""
        return f"transcripts_{company.lower()}"
    
    def store_document_chunks(
        self, 
        company: str, 
        document_id: str, 
        chunks: List[str], 
        metadata: Dict[str, Any]
    ) -> bool:
        """Store document chunks in ChromaDB"""
        try:
            collection_name = self.get_collection_name(company)
            collection = self.db_manager.get_or_create_collection(collection_name)
            
            # Generate embeddings for chunks
            logger.info(f"Generating embeddings for {len(chunks)} chunks from {document_id}")
            embeddings = self.embedding_service.encode_texts(chunks)
            
            # Prepare data for ChromaDB
            ids = []
            documents = []
            metadatas = []
            embeddings_list = []
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_id = f"{document_id}_chunk_{i}"
                chunk_metadata = {
                    **metadata,
                    "chunk_index": i,
                    "document_id": document_id,
                    "company": company,
                    "total_chunks": len(chunks)
                }
                
                ids.append(chunk_id)
                documents.append(chunk)
                metadatas.append(chunk_metadata)
                embeddings_list.append(embedding.tolist())
            
            # Store in ChromaDB
            collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings_list,
                metadatas=metadatas
            )
            
            logger.info(f"Stored {len(chunks)} chunks for document {document_id} in collection {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store document chunks: {e}")
            return False
    
    def search_similar_chunks(
        self,
        query: str,
        company_filter: Optional[List[str]] = None,
        max_results: int = 5,
        similarity_threshold: float = 0.7,
        date_filter: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar chunks across companies"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.encode_single_text(query)
            
            all_results = []
            companies_to_search = company_filter or list(self.company_names.keys())
            
            for company in companies_to_search:
                try:
                    collection_name = self.get_collection_name(company)
                    collection = self.db_manager.get_or_create_collection(collection_name)
                    
                    # Check if collection has documents
                    if collection.count() == 0:
                        logger.warning(f"Collection {collection_name} is empty")
                        continue
                    
                    # Prepare where clause for filtering
                    where_clause = {"company": company}
                    
                    # Add date filtering if specified
                    if date_filter:
                        if date_filter.get("start"):
                            where_clause["date"] = {"$gte": date_filter["start"]}
                        if date_filter.get("end"):
                            if "date" not in where_clause:
                                where_clause["date"] = {}
                            where_clause["date"]["$lte"] = date_filter["end"]
                    
                    # Search in collection
                    results = collection.query(
                        query_embeddings=[query_embedding.tolist()],
                        n_results=min(max_results * 2, 50),  # Get more results to filter
                        where=where_clause,
                        include=["documents", "metadatas", "distances"]
                    )
                    
                    # Process results
                    if results["documents"] and results["documents"][0]:
                        for i, (doc, metadata, distance) in enumerate(zip(
                            results["documents"][0],
                            results["metadatas"][0],
                            results["distances"][0]
                        )):
                            # Convert distance to similarity score
                            similarity_score = 1 - distance
                            
                            if similarity_score >= similarity_threshold:
                                result = {
                                    "company": company,
                                    "document_id": metadata.get("document_id", ""),
                                    "chunk_index": metadata.get("chunk_index", 0),
                                    "date": metadata.get("date", ""),
                                    "quarter": metadata.get("quarter", ""),
                                    "content": doc,
                                    "similarity_score": similarity_score,
                                    "metadata": metadata
                                }
                                all_results.append(result)
                
                except Exception as e:
                    logger.warning(f"Failed to search in collection for {company}: {e}")
                    continue
            
            # Sort by similarity score and limit results
            all_results.sort(key=lambda x: x["similarity_score"], reverse=True)
            return all_results[:max_results]
            
        except Exception as e:
            logger.error(f"Failed to search similar chunks: {e}")
            return []
    
    def get_company_stats(self, company: str) -> Dict[str, Any]:
        """Get statistics for a company's documents"""
        try:
            collection_name = self.get_collection_name(company)
            collection_info = self.db_manager.get_collection_info(collection_name)
            
            if collection_info["count"] == 0:
                return {
                    "company": company,
                    "name": self.company_names.get(company, company),
                    "transcript_count": 0,
                    "chunk_count": 0,
                    "date_range": None,
                    "latest_transcript": None
                }
            
            # Get collection to query metadata
            collection = self.db_manager.get_or_create_collection(collection_name)
            
            # Get all metadata to analyze
            results = collection.get(include=["metadatas"])
            
            if not results["metadatas"]:
                return {
                    "company": company,
                    "name": self.company_names.get(company, company),
                    "transcript_count": 0,
                    "chunk_count": 0,
                    "date_range": None,
                    "latest_transcript": None
                }
            
            # Analyze metadata
            unique_documents = set()
            dates = []
            
            for metadata in results["metadatas"]:
                if metadata.get("document_id"):
                    unique_documents.add(metadata["document_id"])
                if metadata.get("date"):
                    dates.append(metadata["date"])
            
            dates.sort()
            
            return {
                "company": company,
                "name": self.company_names.get(company, company),
                "transcript_count": len(unique_documents),
                "chunk_count": len(results["metadatas"]),
                "date_range": {
                    "start": dates[0] if dates else None,
                    "end": dates[-1] if dates else None
                } if dates else None,
                "latest_transcript": dates[-1] if dates else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get company stats for {company}: {e}")
            return {
                "company": company,
                "name": self.company_names.get(company, company),
                "transcript_count": 0,
                "chunk_count": 0,
                "date_range": None,
                "latest_transcript": None
            }
    
    def get_all_companies_stats(self) -> List[Dict[str, Any]]:
        """Get statistics for all companies"""
        companies_stats = []
        for company in self.company_names.keys():
            stats = self.get_company_stats(company)
            companies_stats.append(stats)
        
        return companies_stats
    
    def delete_company_data(self, company: str) -> bool:
        """Delete all data for a specific company"""
        try:
            collection_name = self.get_collection_name(company)
            return self.db_manager.delete_collection(collection_name)
        except Exception as e:
            logger.error(f"Failed to delete company data for {company}: {e}")
            return False
    
    def get_document_by_id(self, document_id: str, company: str) -> Optional[Dict[str, Any]]:
        """Get a specific document by ID"""
        try:
            collection_name = self.get_collection_name(company)
            collection = self.db_manager.get_or_create_collection(collection_name)
            
            # Search for chunks belonging to this document
            results = collection.get(
                where={"document_id": document_id},
                include=["documents", "metadatas"]
            )
            
            if not results["documents"]:
                return None
            
            # Combine chunks back into document
            chunks = []
            metadata = None
            
            for doc, meta in zip(results["documents"], results["metadatas"]):
                chunks.append({
                    "content": doc,
                    "chunk_index": meta.get("chunk_index", 0)
                })
                if metadata is None:
                    metadata = {k: v for k, v in meta.items() if k != "chunk_index"}
            
            # Sort chunks by index
            chunks.sort(key=lambda x: x["chunk_index"])
            
            return {
                "document_id": document_id,
                "company": company,
                "chunks": chunks,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            return None
    
    def check_collection_health(self, company: str) -> Dict[str, Any]:
        """Check health status of a company's collection"""
        try:
            collection_name = self.get_collection_name(company)
            collection_info = self.db_manager.get_collection_info(collection_name)
            
            # Basic health check
            is_healthy = collection_info["count"] > 0
            
            return {
                "company": company,
                "collection_name": collection_name,
                "status": "healthy" if is_healthy else "empty",
                "document_count": collection_info["count"],
                "last_checked": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check failed for {company}: {e}")
            return {
                "company": company,
                "collection_name": self.get_collection_name(company),
                "status": "error",
                "error": str(e),
                "last_checked": datetime.now().isoformat()
            }


# Global chroma service instance
chroma_service = ChromaService()


def get_chroma_service() -> ChromaService:
    """Dependency to get chroma service instance"""
    return chroma_service 