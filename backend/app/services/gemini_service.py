import google.generativeai as genai
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import time

from ..core.config import get_settings

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for Google Gemini Pro API interactions"""
    
    def __init__(self):
        self.settings = get_settings()
        self.model = None
        self.api_key = self.settings.GOOGLE_API_KEY
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize Gemini API client"""
        try:
            if not self.api_key or self.api_key == "your_gemini_api_key_here":
                logger.error("Google API key not configured")
                return
            
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
            logger.info("Gemini Pro model initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
    
    def _create_rag_prompt(
        self, 
        question: str, 
        sources: List[Dict[str, Any]],
        temperature: float = 0.7
    ) -> str:
        """Create a RAG prompt with sources and question"""
        
        # Build context from sources
        context_parts = []
        for i, source in enumerate(sources, 1):
            company = source.get("company", "Unknown")
            date = source.get("date", "Unknown date")
            quarter = source.get("quarter", "")
            content = source.get("content", "")
            similarity = source.get("similarity_score", 0)
            
            quarter_info = f" ({quarter})" if quarter else ""
            
            context_parts.append(
                f"Source {i} - {company}{quarter_info} - {date} (Relevance: {similarity:.2f}):\n"
                f"{content}\n"
            )
        
        context = "\n".join(context_parts)
        
        prompt = f"""You are a financial analyst AI assistant specialized in analyzing earnings call transcripts. 
Your task is to provide accurate, insightful answers based on the provided financial transcript excerpts.

CONTEXT FROM FINANCIAL TRANSCRIPTS:
{context}

QUESTION: {question}

INSTRUCTIONS:
1. Base your answer primarily on the provided transcript excerpts
2. Provide specific, factual information with clear attribution to companies and time periods
3. If the question asks about trends, compare information across different time periods or companies
4. If the provided context doesn't fully answer the question, acknowledge the limitations
5. Use financial terminology appropriately and explain complex concepts when necessary
6. Structure your response clearly with key points highlighted
7. When referencing specific information, mention the company and time period

RESPONSE:"""

        return prompt
    
    def generate_response(
        self,
        question: str,
        sources: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Optional[str]:
        """Generate response using Gemini Pro"""
        try:
            if not self.model:
                logger.error("Gemini model not initialized")
                return None
            
            if not sources:
                return self._generate_no_context_response(question)
            
            # Create RAG prompt
            prompt = self._create_rag_prompt(question, sources, temperature)
            
            # Generate response
            start_time = time.time()
            
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                top_p=0.9,
                top_k=40
            )
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            if response.text:
                logger.info(f"Generated response in {processing_time:.2f}s")
                return response.text.strip()
            else:
                logger.warning("Empty response from Gemini")
                return None
                
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return None
    
    def _generate_no_context_response(self, question: str) -> str:
        """Generate response when no relevant context is found"""
        return (
            f"I couldn't find relevant information in the available financial transcripts "
            f"to answer your question: '{question}'. This could be because:\n\n"
            f"1. The topic isn't covered in the available earnings call transcripts\n"
            f"2. The information might be in transcripts outside the covered time period (2016-2020)\n"
            f"3. The question might need to be rephrased to match the content better\n\n"
            f"Try refining your question or asking about topics commonly discussed in earnings calls "
            f"such as revenue, growth, market conditions, or business strategy."
        )
    
    def generate_summary(
        self,
        sources: List[Dict[str, Any]],
        topic: str = "financial performance"
    ) -> Optional[str]:
        """Generate a summary of sources on a specific topic"""
        try:
            if not self.model or not sources:
                return None
            
            # Build context
            context_parts = []
            for source in sources:
                company = source.get("company", "Unknown")
                date = source.get("date", "Unknown")
                content = source.get("content", "")
                
                context_parts.append(f"{company} ({date}):\n{content}\n")
            
            context = "\n".join(context_parts)
            
            prompt = f"""Analyze and summarize the following financial transcript excerpts related to {topic}:

{context}

Provide a comprehensive summary that:
1. Identifies key themes and trends
2. Highlights company-specific insights
3. Notes any significant changes over time
4. Summarizes the overall sentiment

Summary:"""
            
            response = self.model.generate_content(prompt)
            return response.text.strip() if response.text else None
            
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return None
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of financial text"""
        try:
            if not self.model:
                return {"sentiment": "unknown", "confidence": 0.0, "reasoning": "Model not available"}
            
            prompt = f"""Analyze the sentiment of this financial text excerpt. Consider the business context and financial implications.

Text: {text}

Provide your analysis in this format:
Sentiment: [Positive/Negative/Neutral]
Confidence: [0.0-1.0]
Reasoning: [Brief explanation]

Analysis:"""
            
            response = self.model.generate_content(prompt)
            
            if response.text:
                # Parse response (simplified parsing)
                lines = response.text.strip().split('\n')
                sentiment = "neutral"
                confidence = 0.5
                reasoning = "Unable to determine"
                
                for line in lines:
                    if line.startswith("Sentiment:"):
                        sentiment = line.split(":", 1)[1].strip().lower()
                    elif line.startswith("Confidence:"):
                        try:
                            confidence = float(line.split(":", 1)[1].strip())
                        except ValueError:
                            pass
                    elif line.startswith("Reasoning:"):
                        reasoning = line.split(":", 1)[1].strip()
                
                return {
                    "sentiment": sentiment,
                    "confidence": confidence,
                    "reasoning": reasoning
                }
            
        except Exception as e:
            logger.error(f"Failed to analyze sentiment: {e}")
        
        return {"sentiment": "unknown", "confidence": 0.0, "reasoning": "Analysis failed"}
    
    def extract_key_points(
        self,
        sources: List[Dict[str, Any]],
        max_points: int = 5
    ) -> List[str]:
        """Extract key points from sources"""
        try:
            if not self.model or not sources:
                return []
            
            # Combine sources
            combined_text = ""
            for source in sources:
                company = source.get("company", "")
                date = source.get("date", "")
                content = source.get("content", "")
                combined_text += f"[{company} - {date}] {content}\n\n"
            
            prompt = f"""Extract the {max_points} most important key points from these financial transcript excerpts:

{combined_text}

Format as a numbered list of clear, concise points:

Key Points:"""
            
            response = self.model.generate_content(prompt)
            
            if response.text:
                # Parse numbered list
                lines = response.text.strip().split('\n')
                key_points = []
                
                for line in lines:
                    line = line.strip()
                    if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                        # Remove numbering and clean up
                        point = line.split('.', 1)[-1].strip() if '.' in line else line
                        point = point.lstrip('- •').strip()
                        if point:
                            key_points.append(point)
                
                return key_points[:max_points]
            
        except Exception as e:
            logger.error(f"Failed to extract key points: {e}")
        
        return []
    
    def check_api_health(self) -> Dict[str, Any]:
        """Check if Gemini API is accessible"""
        try:
            if not self.model:
                return {
                    "status": "error",
                    "message": "Model not initialized",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Simple test generation
            test_prompt = "Reply with 'OK' if you're working."
            response = self.model.generate_content(test_prompt)
            
            if response.text and "OK" in response.text:
                return {
                    "status": "healthy",
                    "message": "API responding normally",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "warning",
                    "message": "Unexpected response from API",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"API health check failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Global gemini service instance
gemini_service = GeminiService()


def get_gemini_service() -> GeminiService:
    """Dependency to get gemini service instance"""
    return gemini_service 