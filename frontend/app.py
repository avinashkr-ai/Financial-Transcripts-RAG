import streamlit as st
import requests
import json
from datetime import datetime, date
import time
import os
from typing import Dict, Any, List

from components.chat import ChatInterface
from components.sidebar import Sidebar
from components.results import ResultsDisplay
from utils.api_client import APIClient
from utils.formatters import format_response, format_sources

# Page configuration
st.set_page_config(
    page_title="Financial Transcripts RAG",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .source-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e6e9ef;
        margin-bottom: 1rem;
    }
    .similarity-score {
        background-color: #e8f4fd;
        padding: 0.2rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .status-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 0.5rem;
    }
    .status-healthy { background-color: #28a745; }
    .status-warning { background-color: #ffc107; }
    .status-error { background-color: #dc3545; }
    .api-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

class RAGApp:
    def __init__(self):
        """Initialize the RAG application"""
        self.api_client = APIClient()
        self.initialize_session_state()
        self.sidebar = Sidebar(self.api_client)
    
    def initialize_session_state(self):
        """Initialize session state variables"""
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'companies_data' not in st.session_state:
            st.session_state.companies_data = None
        if 'system_status' not in st.session_state:
            st.session_state.system_status = None
        if 'embedding_status' not in st.session_state:
            st.session_state.embedding_status = None
        if 'last_response' not in st.session_state:
            st.session_state.last_response = None
        if 'current_tab' not in st.session_state:
            st.session_state.current_tab = "chat"
        if 'sample_query' not in st.session_state:
            st.session_state.sample_query = ""
    
    def render_header(self):
        """Render the application header"""
        st.markdown("""
        <div class="main-header">
            <h1>💰 Financial Transcripts RAG</h1>
            <p>AI-powered analysis of earnings call transcripts (2016-2020)</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Connection status in header
        connection_status = self.api_client.test_connection()
        if connection_status:
            st.success("🟢 Connected to Backend API")
        else:
            st.error("🔴 Backend API Connection Failed")
    
    def render_main_interface(self):
        """Render the main interface with tabs"""
        # Enhanced sidebar
        self.sidebar.render_complete_sidebar()
        
        # Main content tabs
        tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "🔍 Search", "📊 Analytics", "🔧 System"])
        
        with tab1:
            self.render_chat_interface()
        
        with tab2:
            self.render_search_interface()
        
        with tab3:
            self.render_analytics_interface()
        
        with tab4:
            self.render_system_interface()
    
    def render_chat_interface(self):
        """Render the main chat interface"""
        st.subheader("🤖 Ask Questions About Financial Transcripts")
        st.info("💡 **Best Results:** Use financial terms like 'revenue', 'quarterly earnings', 'cloud computing'. Similarity threshold 0.3-0.4 works optimally!")
        
        # Handle sample query from sidebar
        default_query = ""
        if hasattr(st.session_state, 'sample_query') and st.session_state.sample_query:
            default_query = st.session_state.sample_query
            st.session_state.sample_query = ""  # Clear it
        
        # Query input
        with st.form("query_form", clear_on_submit=True):
            query = st.text_area(
                "Your Question:",
                value=default_query,
                placeholder="e.g., Which companies discussed cloud computing revenue growth? What were Microsoft's cloud service results?",
                height=100
            )
            
            # Query options
            col1, col2, col3 = st.columns(3)
            
            with col1:
                companies = st.multiselect(
                    "Filter by Companies:",
                    options=["AAPL", "AMD", "AMZN", "ASML", "CSCO", "GOOGL", "INTC", "MSFT", "MU", "NVDA"],
                    default=None
                )
            
            with col2:
                max_results = st.slider("Max Results", 1, 20, 5)
                similarity_threshold = st.slider("Similarity Threshold", 0.0, 1.0, 0.35)
            
            with col3:
                temperature = st.slider("Temperature", 0.0, 2.0, 0.7)
                use_date_filter = st.checkbox("Use Date Filter")
            
            # Date range (if enabled)
            date_range = {}
            if use_date_filter:
                col_start, col_end = st.columns(2)
                with col_start:
                    start_date = st.date_input("Start Date", value=None)
                with col_end:
                    end_date = st.date_input("End Date", value=None)
                
                if start_date:
                    date_range["start"] = start_date.strftime("%Y-%m-%d")
                if end_date:
                    date_range["end"] = end_date.strftime("%Y-%m-%d")
            
            submitted = st.form_submit_button("🚀 Ask Question", type="primary")
        
        # Process query
        if submitted and query.strip():
            self.process_query(query, companies, max_results, similarity_threshold, temperature, date_range)
        
        # Display conversation
        self.display_conversation()
    
    def render_search_interface(self):
        """Render vector search interface"""
        st.subheader("🔍 Vector Similarity Search")
        st.markdown("Perform direct vector searches without LLM generation")
        st.info("💡 **Tip:** Similarity threshold of 0.3-0.4 works best for finding relevant financial content!")
        
        with st.form("search_form"):
            search_query = st.text_input(
                "Search Query:",
                placeholder="e.g., cloud computing revenue, Q4 earnings performance, quarterly results"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                search_companies = st.multiselect(
                    "Filter by Companies:",
                    options=["AAPL", "AMD", "AMZN", "ASML", "CSCO", "GOOGL", "INTC", "MSFT", "MU", "NVDA"]
                )
            
            with col2:
                search_max_results = st.slider("Max Results", 1, 50, 10)
                search_threshold = st.slider("Min Similarity", 0.0, 1.0, 0.35)
            
            search_submitted = st.form_submit_button("🔍 Search", type="primary")
        
        if search_submitted and search_query.strip():
            self.process_search(search_query, search_companies, search_max_results, search_threshold)
    
    def render_analytics_interface(self):
        """Render analytics and insights interface"""
        st.subheader("📊 Analytics & Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📈 System Metrics")
            
            # Get system metrics
            health = self.api_client.get_health()
            companies_data = self.api_client.get_companies()
            embedding_status = self.api_client.get_embedding_status()
            
            if health:
                st.metric("System Status", health.get('status', 'Unknown').title())
                st.metric("Database Status", health.get('database_status', 'Unknown').title())
                st.metric("Embeddings Status", health.get('embeddings_status', 'Unknown').title())
            
            if companies_data:
                companies = companies_data.get('companies', [])
                total_files = sum(c.get('transcript_count', 0) for c in companies)
                st.metric("Total Companies", len(companies))
                st.metric("Total Transcript Files", total_files)
            
            if embedding_status:
                processed = embedding_status.get('processed_documents', 0)
                st.metric("Processed Documents", processed)
                progress = embedding_status.get('progress', 0)
                st.metric("Processing Progress", f"{progress:.1f}%")
        
        with col2:
            st.markdown("### 📊 Company Overview")
            
            if companies_data:
                companies = companies_data.get('companies', [])
                
                # Company data table
                company_table_data = []
                for company in companies:
                    company_table_data.append({
                        "Company": company.get('symbol', 'Unknown'),
                        "Name": company.get('name', 'Unknown'),
                        "Files": company.get('transcript_count', 0),
                        "Date Range": f"{company.get('date_range', {}).get('start', 'N/A')} - {company.get('date_range', {}).get('end', 'N/A')}"
                    })
                
                st.dataframe(company_table_data, use_container_width=True)
        
        # Insights generation
        st.markdown("### 🧠 Generate Insights")
        with st.form("insights_form"):
            insight_topic = st.text_input(
                "Topic for Analysis:",
                placeholder="e.g., AI strategy, supply chain challenges, revenue growth"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                insight_companies = st.multiselect(
                    "Focus Companies:",
                    options=["AAPL", "AMD", "AMZN", "ASML", "CSCO", "GOOGL", "INTC", "MSFT", "MU", "NVDA"]
                )
            
            with col2:
                max_sources = st.slider("Max Sources", 5, 20, 10)
            
            insights_submitted = st.form_submit_button("🧠 Generate Insights", type="primary")
        
        if insights_submitted and insight_topic.strip():
            self.generate_insights(insight_topic, insight_companies, max_sources)
    
    def render_system_interface(self):
        """Render system management interface"""
        st.subheader("🔧 System Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🌐 API Endpoints")
            
            endpoints = [
                ("Health Check", "/health", "GET"),
                ("Companies List", "/companies", "GET"),
                ("RAG Query", "/api/v1/query", "POST"),
                ("Vector Search", "/api/v1/search", "POST"),
                ("Generate Insights", "/api/v1/insights", "POST"),
                ("Embedding Status", "/api/v1/embeddings/status", "GET"),
                ("Create Embeddings", "/api/v1/embeddings/create", "POST"),
                ("Clear Embeddings", "/api/v1/embeddings/clear", "DELETE"),
                ("Cache Info", "/api/v1/embeddings/cache/info", "GET"),
                ("System Info", "/system/info", "GET")
            ]
            
            for name, endpoint, method in endpoints:
                status = self.test_endpoint_detailed(endpoint)
                icon = "🟢" if status else "🔴"
                st.markdown(f"{icon} **{name}** `{method} {endpoint}`")
        
        with col2:
            st.markdown("### ⚙️ System Actions")
            
            # Test all endpoints
            if st.button("🔍 Test All Endpoints", type="primary"):
                self.test_all_endpoints()
            
            # Refresh data
            if st.button("🔄 Refresh System Data"):
                st.cache_data.clear()
                st.rerun()
            
            # System information
            if st.button("📊 Show System Info"):
                system_info = self.api_client.get_system_info()
                if system_info:
                    st.json(system_info)
                else:
                    st.error("❌ Unable to fetch system info")
            
            # Embedding management
            st.markdown("#### 🧠 Embedding Management")
            
            col_create, col_clear = st.columns(2)
            
            with col_create:
                if st.button("🚀 Create Embeddings"):
                    self.create_all_embeddings()
            
            with col_clear:
                if st.button("🗑️ Clear Embeddings"):
                    if st.button("⚠️ Confirm Clear"):
                        self.clear_all_embeddings()
    
    def process_query(self, query: str, companies: List[str], max_results: int, 
                     similarity_threshold: float, temperature: float, date_range: Dict):
        """Process a RAG query"""
        with st.spinner("🤖 Processing your question..."):
            query_data = {
                "question": query,
                "max_results": max_results,
                "similarity_threshold": similarity_threshold,
                "temperature": temperature
            }
            
            if companies:
                query_data["company_filter"] = companies
            
            if date_range:
                query_data["date_range"] = date_range
            
            response = self.api_client.query(query_data)
            
            if response:
                st.session_state.messages.append({
                    "role": "user",
                    "content": query,
                    "timestamp": datetime.now()
                })
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response,
                    "timestamp": datetime.now()
                })
                st.session_state.last_response = response
                st.rerun()
            else:
                st.error("❌ Failed to get response from API")
    
    def process_search(self, query: str, companies: List[str], max_results: int, threshold: float):
        """Process a vector search"""
        with st.spinner("🔍 Searching..."):
            search_data = {
                "query": query,
                "max_results": max_results,
                "similarity_threshold": threshold
            }
            
            if companies:
                search_data["company_filter"] = companies
            
            response = self.api_client.search(search_data)
            
            if response:
                st.success(f"✅ Found {len(response.get('results', []))} results")
                
                for i, result in enumerate(response.get('results', [])):
                    with st.expander(f"Result {i+1}: {result.get('company', 'Unknown')} - Score: {result.get('similarity_score', 0):.3f}"):
                        st.markdown(f"**Document:** `{result.get('document_id', 'Unknown')}`")
                        st.markdown(f"**Date:** {result.get('date', 'Unknown')}")
                        st.markdown(f"**Quarter:** {result.get('quarter', 'Unknown')}")
                        
                        # Use 'chunk' instead of 'content'
                        chunk_content = result.get('chunk', result.get('content', 'No content available'))
                        if chunk_content and chunk_content != 'No content available':
                            st.markdown(f"**Content:** _{chunk_content[:400]}{'...' if len(chunk_content) > 400 else ''}_")
                        else:
                            st.warning("⚠️ No content available for this result")
            else:
                st.error("❌ Search failed")
    
    def generate_insights(self, topic: str, companies: List[str], max_sources: int):
        """Generate insights on a topic"""
        with st.spinner("🧠 Generating insights..."):
            response = self.api_client.generate_insights(
                topic=topic,
                companies=companies,
                max_sources=max_sources
            )
            
            if response:
                st.success("✅ Insights generated successfully!")
                
                # Display insights
                insights = response.get('insights', 'No insights generated')
                st.markdown("### 📋 Generated Insights")
                st.markdown(insights)
                
                # Display sources
                sources = response.get('sources', [])
                if sources:
                    st.markdown("### 📚 Sources")
                    for i, source in enumerate(sources):
                        with st.expander(f"Source {i+1}: {source.get('company', 'Unknown')}"):
                            st.markdown(f"**Document:** {source.get('document_id', 'Unknown')}")
                            st.markdown(f"**Content:** {source.get('content', 'No content')}")
            else:
                st.error("❌ Failed to generate insights")
    
    def test_endpoint_detailed(self, endpoint: str) -> bool:
        """Test a specific endpoint"""
        try:
            if endpoint == "/health":
                result = self.api_client.get_health()
            elif endpoint == "/companies":
                result = self.api_client.get_companies()
            elif endpoint == "/api/v1/embeddings/status":
                result = self.api_client.get_embedding_status()
            elif endpoint == "/system/info":
                result = self.api_client.get_system_info()
            elif endpoint == "/api/v1/embeddings/cache/info":
                result = self.api_client.get_cache_info()
            else:
                return True  # Assume accessible for POST/DELETE endpoints
            
            return result is not None
        except Exception:
            return False
    
    def test_all_endpoints(self):
        """Test all API endpoints"""
        st.markdown("### 🔍 Endpoint Test Results")
        
        endpoints = [
            ("/health", "Health Check"),
            ("/companies", "Companies List"),
            ("/api/v1/embeddings/status", "Embedding Status"),
            ("/system/info", "System Info"),
            ("/api/v1/embeddings/cache/info", "Cache Info")
        ]
        
        results = []
        for endpoint, name in endpoints:
            status = self.test_endpoint_detailed(endpoint)
            results.append({
                "Endpoint": name,
                "URL": endpoint,
                "Status": "✅ Working" if status else "❌ Failed"
            })
        
        st.dataframe(results, use_container_width=True)
    
    def create_all_embeddings(self):
        """Create embeddings for all companies"""
        embedding_data = {
            "force_recreate": False,
            "companies": None,
            "batch_size": 32
        }
        
        result = self.api_client.create_embeddings(embedding_data)
        if result:
            st.success("✅ Embedding creation started!")
            st.json(result)
        else:
            st.error("❌ Failed to start embedding creation")
    
    def clear_all_embeddings(self):
        """Clear all embeddings"""
        result = self.api_client.clear_embeddings()
        if result:
            st.success("✅ All embeddings cleared!")
        else:
            st.error("❌ Failed to clear embeddings")
    
    def display_conversation(self):
        """Display the conversation history"""
        if st.session_state.messages:
            st.markdown("### 💬 Conversation")
            
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    if message["role"] == "user":
                        st.markdown(message["content"])
                    else:
                        # Display AI response
                        response_data = message["content"]
                        
                        if isinstance(response_data, dict):
                            # Display the answer
                            answer = response_data.get("answer", "No answer provided")
                            st.markdown(answer)
                            
                            # Display sources
                            sources = response_data.get("sources", [])
                            if sources:
                                with st.expander(f"📚 Sources ({len(sources)})"):
                                    for i, source in enumerate(sources):
                                        st.markdown(f"**{i+1}. {source.get('company', 'Unknown')} - {source.get('date', 'Unknown')}** (Score: {source.get('similarity_score', 0):.3f})")
                                        st.markdown(f"**Document:** `{source.get('document_id', 'Unknown')}`")
                                        
                                        # Use 'chunk' instead of 'content'
                                        chunk_content = source.get('chunk', source.get('content', 'No content available'))
                                        if chunk_content and chunk_content != 'No content available':
                                            st.markdown(f"**Content:** _{chunk_content[:300]}{'...' if len(chunk_content) > 300 else ''}_")
                                        else:
                                            st.warning("⚠️ No content available for this source")
                                        st.markdown("---")
                        else:
                            st.markdown(str(response_data))
    
    def run(self):
        """Run the Streamlit application"""
        self.render_header()
        self.render_main_interface()


# Main execution
if __name__ == "__main__":
    app = RAGApp()
    app.run() 