import requests
import os
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class APIClient:
    """Client for communicating with the FastAPI backend"""
    
    def __init__(self):
        """Initialize the API client"""
        self.base_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        self.api_prefix = "/api/v1"
        self.timeout = 60  # 60 seconds timeout for long operations
        
        # Setup session with common headers
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make HTTP request to the API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            # Set timeout if not provided
            if 'timeout' not in kwargs:
                kwargs['timeout'] = self.timeout
            
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for {url}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error for {url}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error {e.response.status_code} for {url}: {e.response.text}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {str(e)}")
            return None
    
    def query(self, query_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Submit a RAG query"""
        endpoint = f"{self.api_prefix}/query"
        return self._make_request("POST", endpoint, json=query_data)
    
    def search(self, search_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Perform vector similarity search"""
        endpoint = f"{self.api_prefix}/search"
        return self._make_request("POST", endpoint, json=search_data)
    
    def generate_insights(
        self, 
        topic: str, 
        companies: Optional[List[str]] = None,
        date_start: Optional[str] = None,
        date_end: Optional[str] = None,
        max_sources: int = 10
    ) -> Optional[Dict[str, Any]]:
        """Generate insights on a topic"""
        endpoint = f"{self.api_prefix}/insights"
        
        params = {"topic": topic, "max_sources": max_sources}
        if companies:
            params["companies"] = companies
        if date_start:
            params["date_start"] = date_start
        if date_end:
            params["date_end"] = date_end
        
        return self._make_request("POST", endpoint, params=params)
    
    def get_health(self) -> Optional[Dict[str, Any]]:
        """Get system health status"""
        endpoint = "/health"
        return self._make_request("GET", endpoint, timeout=10)
    
    def get_companies(self) -> Optional[Dict[str, Any]]:
        """Get information about available companies"""
        endpoint = "/companies"
        return self._make_request("GET", endpoint)
    
    def get_company_transcripts(self, company: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a company's transcripts"""
        endpoint = f"/transcripts/{company}"
        return self._make_request("GET", endpoint)
    
    def get_system_info(self) -> Optional[Dict[str, Any]]:
        """Get detailed system information"""
        endpoint = "/system/info"
        return self._make_request("GET", endpoint)
    
    def get_embedding_status(self) -> Optional[Dict[str, Any]]:
        """Get embedding generation status"""
        endpoint = f"{self.api_prefix}/embeddings/status"
        return self._make_request("GET", endpoint)
    
    def create_embeddings(self, embedding_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Start embedding generation process"""
        endpoint = f"{self.api_prefix}/embeddings/create"
        return self._make_request("POST", endpoint, json=embedding_data)
    
    def clear_embeddings(self, company: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Clear embeddings for a company or all companies"""
        endpoint = f"{self.api_prefix}/embeddings/clear"
        params = {}
        if company:
            params["company"] = company
        
        return self._make_request("DELETE", endpoint, params=params)
    
    def get_cache_info(self) -> Optional[Dict[str, Any]]:
        """Get embedding cache information"""
        endpoint = f"{self.api_prefix}/embeddings/cache/info"
        return self._make_request("GET", endpoint)
    
    def get_api_info(self) -> Optional[Dict[str, Any]]:
        """Get API information"""
        endpoint = "/info"
        return self._make_request("GET", endpoint)
    
    def test_connection(self) -> bool:
        """Test if the API is accessible"""
        try:
            response = self._make_request("GET", "/", timeout=5)
            return response is not None
        except Exception:
            return False 