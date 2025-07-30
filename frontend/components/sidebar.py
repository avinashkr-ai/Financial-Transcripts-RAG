import streamlit as st
from typing import Dict, Any, List, Optional
import time


class Sidebar:
    """Enhanced sidebar component with system overview, files, and embedding management"""
    
    def __init__(self, api_client):
        """Initialize the sidebar with API client"""
        self.api_client = api_client
    
    def render_complete_sidebar(self):
        """Render the complete enhanced sidebar"""
        st.sidebar.title("📊 RAG System Dashboard")
        
        # System Status Section
        self.render_system_status()
        
        # Files & Transcripts Section
        self.render_files_section()
        
        # Embedding Management Section
        self.render_embedding_section()
        
        # API Endpoints Section
        self.render_api_endpoints()
        
        # Quick Actions Section
        self.render_quick_actions()
    
    def render_system_status(self):
        """Render system status indicators"""
        st.sidebar.markdown("### 🔧 System Status")
        
        # Test API connection
        connection_status = self.api_client.test_connection()
        
        if connection_status:
            st.sidebar.markdown("🟢 **Backend Connected**")
            
            # Get health status
            health = self.api_client.get_health()
            if health:
                status = health.get('status', 'unknown')
                db_status = health.get('database_status', 'unknown')
                embeddings_status = health.get('embeddings_status', 'unknown')
                
                st.sidebar.markdown(f"**Overall Status:** `{status}`")
                st.sidebar.markdown(f"**Database:** `{db_status}`")
                st.sidebar.markdown(f"**Embeddings:** `{embeddings_status}`")
        else:
            st.sidebar.markdown("🔴 **Backend Disconnected**")
        
        st.sidebar.markdown("---")
    
    def render_files_section(self):
        """Render files and transcripts information"""
        st.sidebar.markdown("### 📁 Available Files")
        
        # Get companies data
        companies_data = self.api_client.get_companies()
        
        if companies_data:
            total_files = 0
            companies_info = companies_data.get('companies', [])
            
            with st.sidebar.expander("📈 Companies & Files", expanded=True):
                for company_info in companies_info:
                    company = company_info.get('symbol', 'Unknown')
                    file_count = company_info.get('transcript_count', 0)
                    total_files += file_count
                    
                    st.markdown(f"**{company}:** {file_count} files")
                
                st.markdown(f"**📊 Total Files:** {total_files}")
        else:
            st.sidebar.markdown("❌ Unable to load file information")
        
        st.sidebar.markdown("---")
    
    def render_embedding_section(self):
        """Render embedding status and management"""
        st.sidebar.markdown("### 🧠 Embedding Management")
        
        # Get embedding status
        embedding_status = self.api_client.get_embedding_status()
        
        if embedding_status:
            status = embedding_status.get('status', 'unknown')
            progress = embedding_status.get('progress', 0)
            processed = embedding_status.get('processed_documents', 0)
            total = embedding_status.get('total_documents', 0)
            current_company = embedding_status.get('current_company')
            
            # Status indicator
            if status == 'processing':
                st.sidebar.markdown("🔄 **Processing Embeddings**")
                st.sidebar.progress(progress / 100.0)
                st.sidebar.markdown(f"Progress: {progress:.1f}%")
                st.sidebar.markdown(f"Documents: {processed}/{total}")
                if current_company:
                    st.sidebar.markdown(f"Current: {current_company}")
            elif status == 'idle':
                st.sidebar.markdown("⏸️ **Embeddings Idle**")
                if processed > 0:
                    st.sidebar.markdown(f"✅ {processed} documents processed")
            else:
                st.sidebar.markdown(f"📊 **Status:** {status}")
            
            # Embedding actions
            col1, col2 = st.sidebar.columns(2)
            
            with col1:
                if st.button("🚀 Create", key="create_embeddings"):
                    self.create_embeddings()
            
            with col2:
                if st.button("🗑️ Clear", key="clear_embeddings"):
                    self.clear_embeddings()
            
            # Cache info
            cache_info = self.api_client.get_cache_info()
            if cache_info:
                cache_size = cache_info.get('cache_size_mb', 0)
                st.sidebar.markdown(f"💾 Cache: {cache_size:.1f} MB")
        
        st.sidebar.markdown("---")
    
    def render_api_endpoints(self):
        """Render API endpoints status"""
        st.sidebar.markdown("### 🌐 API Endpoints")
        
        with st.sidebar.expander("📡 Endpoint Status", expanded=False):
            endpoints = [
                ("Health Check", "/health"),
                ("RAG Query", "/api/v1/query"),
                ("Vector Search", "/api/v1/search"),
                ("Insights", "/api/v1/insights"),
                ("Companies", "/companies"),
                ("Embeddings Status", "/api/v1/embeddings/status"),
                ("Create Embeddings", "/api/v1/embeddings/create"),
                ("System Info", "/system/info")
            ]
            
            for name, endpoint in endpoints:
                status = self.test_endpoint(endpoint)
                icon = "🟢" if status else "🔴"
                st.markdown(f"{icon} **{name}**")
        
        st.sidebar.markdown("---")
    
    def render_quick_actions(self):
        """Render quick action buttons"""
        st.sidebar.markdown("### ⚡ Quick Actions")
        
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("🔄 Refresh", key="refresh_data"):
                st.rerun()
        
        with col2:
            if st.button("📊 System Info", key="show_system_info"):
                self.show_system_info()
        
        # Sample queries
        with st.sidebar.expander("💡 Sample Queries"):
            sample_queries = [
                "Which companies discussed cloud computing revenue growth?",
                "How did Microsoft perform in cloud services and Office revenue?", 
                "Which companies had strong Q4 performance and earnings?",
                "What companies mentioned data center business growth?",
                "How did Intel's cloud segment perform over time?"
            ]
            
            for i, query in enumerate(sample_queries):
                if st.button(f"📝 {query[:30]}...", key=f"sample_{i}"):
                    st.session_state.sample_query = query
                    st.rerun()
    
    def create_embeddings(self):
        """Create embeddings for all companies"""
        embedding_data = {
            "force_recreate": False,
            "companies": None,
            "batch_size": 32
        }
        
        result = self.api_client.create_embeddings(embedding_data)
        if result:
            st.sidebar.success("✅ Embedding creation started!")
        else:
            st.sidebar.error("❌ Failed to start embedding creation")
    
    def clear_embeddings(self):
        """Clear all embeddings"""
        result = self.api_client.clear_embeddings()
        if result:
            st.sidebar.success("✅ Embeddings cleared!")
        else:
            st.sidebar.error("❌ Failed to clear embeddings")
    
    def test_endpoint(self, endpoint: str) -> bool:
        """Test if an endpoint is accessible"""
        try:
            if endpoint == "/health":
                result = self.api_client.get_health()
            elif endpoint == "/companies":
                result = self.api_client.get_companies()
            elif endpoint == "/api/v1/embeddings/status":
                result = self.api_client.get_embedding_status()
            elif endpoint == "/system/info":
                result = self.api_client.get_system_info()
            else:
                result = True  # Assume accessible for POST endpoints
            
            return result is not None
        except Exception:
            return False
    
    def show_system_info(self):
        """Show detailed system information"""
        system_info = self.api_client.get_system_info()
        if system_info:
            st.sidebar.json(system_info)
        else:
            st.sidebar.error("❌ Unable to fetch system info")
    
    def render_company_filter(self, companies: List[str]) -> List[str]:
        """Render company filter multiselect"""
        return st.multiselect(
            "Filter by Companies:",
            options=companies,
            help="Select companies to focus the search"
        )
    
    def render_date_filter(self) -> Dict[str, Optional[str]]:
        """Render date range filter"""
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input("Start Date", value=None)
        
        with col2:
            end_date = st.date_input("End Date", value=None)
        
        return {
            "start": start_date.strftime("%Y-%m-%d") if start_date else None,
            "end": end_date.strftime("%Y-%m-%d") if end_date else None
        }
    
    def render_advanced_options(self) -> Dict[str, Any]:
        """Render advanced search options"""
        with st.expander("Advanced Options"):
            max_results = st.slider("Max Results", 1, 20, 5)
            similarity_threshold = st.slider("Similarity Threshold", 0.0, 1.0, 0.7)
            temperature = st.slider("Temperature", 0.0, 2.0, 0.7)
            
            return {
                "max_results": max_results,
                "similarity_threshold": similarity_threshold,
                "temperature": temperature
            } 