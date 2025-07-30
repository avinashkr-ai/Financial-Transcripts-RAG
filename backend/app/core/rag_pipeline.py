from typing import List, Dict, Any, Optional, Tuple
import logging
import time
from datetime import datetime

from ..services.chroma_service import get_chroma_service
from ..services.gemini_service import get_gemini_service
from ..services.embedding_service import get_embedding_service
from ..models.query import QueryRequest
from ..models.response import QueryResponse, QueryMetadata, SourceDocument
from ..core.config import get_settings

logger = logging.getLogger(__name__)


class RAGPipeline:
    """RAG Pipeline orchestrating retrieval and generation"""
    
    def __init__(self):
        self.settings = get_settings()
        self.chroma_service = get_chroma_service()
        self.gemini_service = get_gemini_service()
        self.embedding_service = get_embedding_service()
    
    async def process_query(self, request: QueryRequest) -> QueryResponse:
        """Process a complete RAG query"""
        start_time = time.time()
        
        try:
            logger.info(f"Processing RAG query: {request.question[:100]}...")
            
            # Extract parameters
            question = request.question
            company_filter = [c.value for c in request.company_filter] if request.company_filter else None
            max_results = request.max_results
            similarity_threshold = request.similarity_threshold or self.settings.SIMILARITY_THRESHOLD
            temperature = request.temperature or self.settings.TEMPERATURE
            
            # Build date filter
            date_filter = None
            if request.date_range:
                date_filter = {}
                if request.date_range.start:
                    date_filter["start"] = request.date_range.start
                if request.date_range.end:
                    date_filter["end"] = request.date_range.end
            
            # Step 1: Retrieve similar chunks
            logger.info("Retrieving similar chunks from ChromaDB...")
            similar_chunks = self.chroma_service.search_similar_chunks(
                query=question,
                company_filter=company_filter,
                max_results=max_results,
                similarity_threshold=similarity_threshold,
                date_filter=date_filter
            )
            
            logger.info(f"Found {len(similar_chunks)} relevant chunks")
            
            # Step 2: Generate response
            logger.info("Generating response with Gemini Pro...")
            generated_answer = self.gemini_service.generate_response(
                question=question,
                sources=similar_chunks,
                temperature=temperature
            )
            
            if not generated_answer:
                generated_answer = "I apologize, but I couldn't generate a response to your question. Please try rephrasing your question or check if the system is properly configured."
            
            # Step 3: Format sources
            sources = self._format_sources(similar_chunks)
            
            # Step 4: Create metadata
            end_time = time.time()
            processing_time = f"{end_time - start_time:.2f}s"
            
            metadata = QueryMetadata(
                processing_time=processing_time,
                total_chunks_searched=self._estimate_total_chunks_searched(company_filter),
                model_used=self.settings.EMBEDDING_MODEL,
                llm_model="gemini-pro",
                similarity_threshold=similarity_threshold,
                max_results=max_results
            )
            
            # Step 5: Create response
            response = QueryResponse(
                query=question,
                answer=generated_answer,
                sources=sources,
                metadata=metadata
            )
            
            logger.info(f"RAG query completed in {processing_time}")
            return response
            
        except Exception as e:
            logger.error(f"RAG pipeline failed: {e}")
            
            # Return error response
            end_time = time.time()
            processing_time = f"{end_time - start_time:.2f}s"
            
            metadata = QueryMetadata(
                processing_time=processing_time,
                total_chunks_searched=0,
                model_used=self.settings.EMBEDDING_MODEL,
                llm_model="gemini-pro",
                similarity_threshold=similarity_threshold or 0.7,
                max_results=max_results
            )
            
            return QueryResponse(
                query=question,
                answer=f"An error occurred while processing your query: {str(e)}",
                sources=[],
                metadata=metadata
            )
    
    def _format_sources(self, chunks: List[Dict[str, Any]]) -> List[SourceDocument]:
        """Format raw chunks into SourceDocument objects"""
        sources = []
        
        for chunk in chunks:
            try:
                # Extract quarter from date if possible
                quarter = self._extract_quarter(chunk.get("date", ""))
                
                source = SourceDocument(
                    company=chunk.get("company", "Unknown"),
                    date=chunk.get("date", "Unknown"),
                    quarter=quarter,
                    chunk=chunk.get("content", ""),
                    similarity_score=round(chunk.get("similarity_score", 0.0), 3),
                    document_id=chunk.get("document_id", "unknown"),
                    chunk_index=chunk.get("chunk_index")
                )
                sources.append(source)
                
            except Exception as e:
                logger.warning(f"Failed to format source: {e}")
                continue
        
        return sources
    
    def _extract_quarter(self, date_str: str) -> Optional[str]:
        """Extract quarter information from date string"""
        if not date_str:
            return None
        
        try:
            # Parse date and determine quarter
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            month = date_obj.month
            year = date_obj.year
            
            if month in [1, 2, 3]:
                return f"Q1 {year}"
            elif month in [4, 5, 6]:
                return f"Q2 {year}"
            elif month in [7, 8, 9]:
                return f"Q3 {year}"
            else:
                return f"Q4 {year}"
                
        except (ValueError, TypeError):
            # If date parsing fails, try to extract from filename patterns
            import re
            
            # Common patterns: Apr-2020, 2020-Apr-30, etc.
            patterns = [
                r'(\w{3})-(\d{4})',  # Apr-2020
                r'(\d{4})-(\w{3})',  # 2020-Apr
            ]
            
            for pattern in patterns:
                match = re.search(pattern, date_str)
                if match:
                    try:
                        if pattern.startswith(r'(\w{3})'):
                            month_str, year_str = match.groups()
                        else:
                            year_str, month_str = match.groups()
                        
                        month_map = {
                            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
                            'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
                            'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
                        }
                        
                        month = month_map.get(month_str, 1)
                        year = int(year_str)
                        
                        if month in [1, 2, 3]:
                            return f"Q1 {year}"
                        elif month in [4, 5, 6]:
                            return f"Q2 {year}"
                        elif month in [7, 8, 9]:
                            return f"Q3 {year}"
                        else:
                            return f"Q4 {year}"
                            
                    except (ValueError, KeyError):
                        continue
            
            return None
    
    def _estimate_total_chunks_searched(self, company_filter: Optional[List[str]]) -> int:
        """Estimate total number of chunks searched"""
        try:
            if company_filter:
                companies = company_filter
            else:
                companies = list(self.chroma_service.company_names.keys())
            
            total_chunks = 0
            for company in companies:
                stats = self.chroma_service.get_company_stats(company)
                total_chunks += stats.get("chunk_count", 0)
            
            return total_chunks
            
        except Exception as e:
            logger.warning(f"Failed to estimate chunks searched: {e}")
            return 0
    
    def generate_insights(
        self,
        topic: str,
        companies: Optional[List[str]] = None,
        date_range: Optional[Dict[str, str]] = None,
        max_sources: int = 10
    ) -> Dict[str, Any]:
        """Generate insights on a specific topic"""
        try:
            logger.info(f"Generating insights for topic: {topic}")
            
            # Search for relevant content
            chunks = self.chroma_service.search_similar_chunks(
                query=topic,
                company_filter=companies,
                max_results=max_sources,
                similarity_threshold=0.6,
                date_filter=date_range
            )
            
            if not chunks:
                return {
                    "topic": topic,
                    "summary": "No relevant information found for this topic.",
                    "key_points": [],
                    "sentiment": {"sentiment": "neutral", "confidence": 0.0},
                    "sources_count": 0
                }
            
            # Generate summary
            summary = self.gemini_service.generate_summary(chunks, topic)
            
            # Extract key points
            key_points = self.gemini_service.extract_key_points(chunks, max_points=5)
            
            # Analyze overall sentiment
            combined_text = " ".join([chunk.get("content", "") for chunk in chunks[:3]])
            sentiment = self.gemini_service.analyze_sentiment(combined_text)
            
            return {
                "topic": topic,
                "summary": summary or "Unable to generate summary.",
                "key_points": key_points,
                "sentiment": sentiment,
                "sources_count": len(chunks),
                "companies_covered": list(set(chunk.get("company", "") for chunk in chunks)),
                "date_range_covered": self._get_date_range_from_chunks(chunks)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate insights: {e}")
            return {
                "topic": topic,
                "summary": f"Error generating insights: {str(e)}",
                "key_points": [],
                "sentiment": {"sentiment": "unknown", "confidence": 0.0},
                "sources_count": 0
            }
    
    def _get_date_range_from_chunks(self, chunks: List[Dict[str, Any]]) -> Dict[str, Optional[str]]:
        """Extract date range from chunks"""
        dates = [chunk.get("date") for chunk in chunks if chunk.get("date")]
        dates = [d for d in dates if d]  # Filter out None values
        
        if not dates:
            return {"start": None, "end": None}
        
        dates.sort()
        return {"start": dates[0], "end": dates[-1]}


# Global RAG pipeline instance
rag_pipeline = RAGPipeline()


def get_rag_pipeline() -> RAGPipeline:
    """Dependency to get RAG pipeline instance"""
    return rag_pipeline 