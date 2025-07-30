from typing import Dict, Any, List
from datetime import datetime
import re


def format_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """Format API response for display"""
    formatted = {
        "query": response.get("query", ""),
        "answer": format_answer_text(response.get("answer", "")),
        "sources": format_sources(response.get("sources", [])),
        "metadata": format_metadata(response.get("metadata", {}))
    }
    
    return formatted


def format_answer_text(text: str) -> str:
    """Format answer text for better readability"""
    if not text:
        return "No answer provided."
    
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Add line breaks after sentences for better readability
    text = re.sub(r'(\. )([A-Z])', r'\1\n\n\2', text)
    
    return text


def format_sources(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format source documents for display"""
    formatted_sources = []
    
    for source in sources:
        formatted_source = {
            "company": source.get("company", "Unknown"),
            "company_name": get_company_name(source.get("company", "")),
            "date": format_date(source.get("date", "")),
            "quarter": source.get("quarter", ""),
            "chunk": format_chunk_text(source.get("chunk", "")),
            "similarity_score": round(source.get("similarity_score", 0.0), 3),
            "document_id": source.get("document_id", ""),
            "chunk_index": source.get("chunk_index")
        }
        formatted_sources.append(formatted_source)
    
    return formatted_sources


def format_chunk_text(text: str, max_length: int = 300) -> str:
    """Format chunk text for display"""
    if not text:
        return "No content available."
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Truncate if too long
    if len(text) > max_length:
        # Try to break at sentence boundary
        sentences = text.split('.')
        truncated = ""
        for sentence in sentences:
            if len(truncated + sentence) > max_length - 10:
                break
            truncated += sentence + "."
        
        if truncated:
            text = truncated + "..."
        else:
            text = text[:max_length] + "..."
    
    return text


def format_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Format metadata for display"""
    formatted = {}
    
    # Processing time
    processing_time = metadata.get("processing_time", "")
    if processing_time:
        formatted["processing_time"] = processing_time
    
    # Chunks searched
    total_chunks = metadata.get("total_chunks_searched", 0)
    if total_chunks:
        formatted["chunks_searched"] = f"{total_chunks:,}"
    
    # Models used
    embedding_model = metadata.get("model_used", "")
    llm_model = metadata.get("llm_model", "")
    
    if embedding_model or llm_model:
        formatted["models"] = {
            "embedding": embedding_model,
            "llm": llm_model
        }
    
    # Search parameters
    similarity_threshold = metadata.get("similarity_threshold")
    max_results = metadata.get("max_results")
    
    if similarity_threshold is not None or max_results is not None:
        formatted["parameters"] = {}
        if similarity_threshold is not None:
            formatted["parameters"]["similarity_threshold"] = similarity_threshold
        if max_results is not None:
            formatted["parameters"]["max_results"] = max_results
    
    return formatted


def format_date(date_str: str) -> str:
    """Format date string for display"""
    if not date_str or date_str == "Unknown":
        return "Unknown Date"
    
    try:
        # Try to parse different date formats
        date_formats = [
            "%Y-%m-%d",
            "%Y-%b-%d",
            "%b-%Y",
            "%Y-%m-%d"
        ]
        
        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime("%B %d, %Y")
            except ValueError:
                continue
        
        # If no format works, return original
        return date_str
        
    except Exception:
        return date_str


def get_company_name(symbol: str) -> str:
    """Get full company name from symbol"""
    company_names = {
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
    
    return company_names.get(symbol.upper(), symbol)


def format_similarity_score(score: float) -> str:
    """Format similarity score for display"""
    if score >= 0.9:
        return f"🟢 {score:.3f} (Excellent)"
    elif score >= 0.8:
        return f"🟡 {score:.3f} (Good)"
    elif score >= 0.7:
        return f"🟠 {score:.3f} (Fair)"
    else:
        return f"🔴 {score:.3f} (Weak)"


def format_company_stats(stats: Dict[str, Any]) -> Dict[str, Any]:
    """Format company statistics for display"""
    formatted = {
        "symbol": stats.get("company", ""),
        "name": stats.get("name", ""),
        "transcript_count": stats.get("transcript_count", 0),
        "chunk_count": stats.get("chunk_count", 0)
    }
    
    # Date range
    date_range = stats.get("date_range")
    if date_range:
        start_date = format_date(date_range.get("start", ""))
        end_date = format_date(date_range.get("end", ""))
        formatted["date_range"] = f"{start_date} to {end_date}"
    else:
        formatted["date_range"] = "No data available"
    
    # Latest transcript
    latest = stats.get("latest_transcript")
    if latest:
        formatted["latest_transcript"] = format_date(latest)
    else:
        formatted["latest_transcript"] = "Unknown"
    
    return formatted


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"


def format_time_duration(seconds: float) -> str:
    """Format duration in human readable format"""
    if seconds < 1:
        return f"{int(seconds * 1000)}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def format_embedding_status(status: Dict[str, Any]) -> Dict[str, Any]:
    """Format embedding status for display"""
    formatted = {
        "status": status.get("status", "unknown").title(),
        "progress": status.get("progress", 0),
        "total_documents": status.get("total_documents", 0),
        "processed_documents": status.get("processed_documents", 0),
        "current_company": status.get("current_company", "N/A")
    }
    
    # Estimated time remaining
    eta = status.get("estimated_time_remaining")
    if eta:
        formatted["eta"] = eta
    else:
        formatted["eta"] = "Unknown"
    
    # Progress percentage
    if formatted["total_documents"] > 0:
        progress_pct = (formatted["processed_documents"] / formatted["total_documents"]) * 100
        formatted["progress_percentage"] = f"{progress_pct:.1f}%"
    else:
        formatted["progress_percentage"] = "0.0%"
    
    return formatted


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def highlight_search_terms(text: str, search_terms: List[str]) -> str:
    """Highlight search terms in text (for future use with rich text display)"""
    if not search_terms:
        return text
    
    highlighted = text
    for term in search_terms:
        # Simple highlighting (can be enhanced for actual HTML/markdown)
        highlighted = re.sub(
            f"({re.escape(term)})", 
            r"**\1**", 
            highlighted, 
            flags=re.IGNORECASE
        )
    
    return highlighted 