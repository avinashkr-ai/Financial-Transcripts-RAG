import streamlit as st
from typing import Dict, Any, List
import plotly.express as px
import pandas as pd


class ResultsDisplay:
    """Component for displaying query results and visualizations"""
    
    def __init__(self):
        """Initialize the results display"""
        pass
    
    def render_response(self, response: Dict[str, Any]):
        """Render a complete query response"""
        # Answer
        st.subheader("📝 Answer")
        st.write(response.get("answer", "No answer provided"))
        
        # Sources
        sources = response.get("sources", [])
        if sources:
            st.subheader("📚 Sources")
            self.render_sources(sources)
        
        # Metadata
        metadata = response.get("metadata", {})
        if metadata:
            st.subheader("ℹ️ Query Information")
            self.render_metadata(metadata)
    
    def render_sources(self, sources: List[Dict[str, Any]]):
        """Render source documents"""
        for i, source in enumerate(sources):
            with st.expander(f"Source {i+1}: {source.get('company', 'Unknown')} - {source.get('date', 'Unknown')}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(source.get("chunk", "No content"))
                
                with col2:
                    st.metric("Similarity", f"{source.get('similarity_score', 0):.3f}")
                    st.write(f"**Company:** {source.get('company', 'Unknown')}")
                    st.write(f"**Date:** {source.get('date', 'Unknown')}")
                    if source.get('quarter'):
                        st.write(f"**Quarter:** {source.get('quarter')}")
    
    def render_metadata(self, metadata: Dict[str, Any]):
        """Render query metadata"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Processing Time", metadata.get("processing_time", "Unknown"))
        
        with col2:
            chunks_searched = metadata.get("total_chunks_searched", 0)
            st.metric("Chunks Searched", f"{chunks_searched:,}")
        
        with col3:
            st.metric("Model", metadata.get("model_used", "Unknown"))
    
    def render_similarity_chart(self, sources: List[Dict[str, Any]]):
        """Render similarity scores as a chart"""
        if not sources:
            return
        
        # Prepare data
        data = []
        for source in sources:
            data.append({
                "Company": source.get("company", "Unknown"),
                "Date": source.get("date", "Unknown"),
                "Similarity": source.get("similarity_score", 0),
                "Source": f"{source.get('company', 'Unknown')} - {source.get('date', 'Unknown')}"
            })
        
        df = pd.DataFrame(data)
        
        # Create chart
        fig = px.bar(
            df, 
            x="Source", 
            y="Similarity",
            color="Company",
            title="Source Similarity Scores",
            labels={"Similarity": "Similarity Score", "Source": "Source Document"}
        )
        
        fig.update_xaxis(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    
    def render_company_distribution(self, sources: List[Dict[str, Any]]):
        """Render distribution of sources by company"""
        if not sources:
            return
        
        # Count sources by company
        company_counts = {}
        for source in sources:
            company = source.get("company", "Unknown")
            company_counts[company] = company_counts.get(company, 0) + 1
        
        # Create pie chart
        fig = px.pie(
            values=list(company_counts.values()),
            names=list(company_counts.keys()),
            title="Sources by Company"
        )
        
        st.plotly_chart(fig, use_container_width=True) 