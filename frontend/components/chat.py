import streamlit as st
from typing import Dict, Any, List


class ChatInterface:
    """Chat interface component for conversational interactions"""
    
    def __init__(self):
        """Initialize the chat interface"""
        pass
    
    def render_chat_message(self, message: Dict[str, Any], is_user: bool = False):
        """Render a single chat message"""
        if is_user:
            with st.chat_message("user"):
                st.write(message.get("content", ""))
        else:
            with st.chat_message("assistant"):
                st.write(message.get("content", ""))
                
                # Show sources if available
                sources = message.get("sources", [])
                if sources:
                    with st.expander("📚 Sources"):
                        for i, source in enumerate(sources[:3]):
                            st.write(f"**{source.get('company', 'Unknown')}** - {source.get('date', 'Unknown')}")
                            st.write(f"Similarity: {source.get('similarity_score', 0):.3f}")
                            st.write(source.get('chunk', '')[:200] + "...")
                            st.divider()
    
    def render_chat_input(self):
        """Render chat input field"""
        return st.chat_input("Ask about financial transcripts...")
    
    def render_conversation(self, messages: List[Dict[str, Any]]):
        """Render entire conversation"""
        for message in messages:
            self.render_chat_message(message, message.get("role") == "user") 