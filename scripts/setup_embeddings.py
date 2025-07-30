#!/usr/bin/env python3
"""
Script to set up embeddings for financial transcripts.
This script can be run independently to initialize the ChromaDB with embeddings.
"""

import sys
import os
import argparse
from pathlib import Path
import requests
import time

# Add the backend path to sys.path so we can import backend modules
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

def setup_embeddings_via_api(
    backend_url: str = "http://localhost:8000",
    companies: list = None,
    force_recreate: bool = False,
    batch_size: int = 32
):
    """Set up embeddings via the FastAPI backend"""
    api_url = f"{backend_url}/api/v1/embeddings/create"
    
    payload = {
        "force_recreate": force_recreate,
        "batch_size": batch_size
    }
    
    if companies:
        payload["companies"] = companies
    
    print(f"🚀 Starting embedding generation...")
    print(f"Backend URL: {backend_url}")
    print(f"Force recreate: {force_recreate}")
    print(f"Batch size: {batch_size}")
    if companies:
        print(f"Companies: {', '.join(companies)}")
    else:
        print("Companies: All available")
    
    try:
        # Start embedding generation
        response = requests.post(api_url, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ {result.get('message', 'Embedding generation started')}")
        
        # Monitor progress
        status_url = f"{backend_url}/api/v1/embeddings/status"
        
        print("\n📊 Monitoring progress...")
        while True:
            try:
                status_response = requests.get(status_url, timeout=10)
                status_response.raise_for_status()
                status = status_response.json()
                
                current_status = status.get("status", "unknown")
                
                if current_status == "processing":
                    progress = status.get("progress", 0)
                    processed = status.get("processed_documents", 0)
                    total = status.get("total_documents", 0)
                    current_company = status.get("current_company", "N/A")
                    eta = status.get("estimated_time_remaining", "N/A")
                    
                    print(f"\r⏳ Progress: {progress:.1f}% ({processed}/{total}) | "
                          f"Company: {current_company} | ETA: {eta}", end="", flush=True)
                
                elif current_status == "completed":
                    print(f"\n🎉 Embedding generation completed successfully!")
                    return True
                
                elif current_status == "error":
                    error_msg = status.get("error", "Unknown error")
                    print(f"\n❌ Embedding generation failed: {error_msg}")
                    return False
                
                elif current_status in ["idle", "starting"]:
                    print(f"\r🔄 Status: {current_status}", end="", flush=True)
                
                time.sleep(2)  # Check every 2 seconds
                
            except requests.RequestException as e:
                print(f"\n⚠️ Error checking status: {e}")
                time.sleep(5)  # Wait longer on error
                continue
                
            except KeyboardInterrupt:
                print(f"\n⏹️ Monitoring interrupted by user")
                return False
    
    except requests.RequestException as e:
        print(f"❌ Failed to start embedding generation: {e}")
        return False


def check_backend_health(backend_url: str = "http://localhost:8000"):
    """Check if the backend is running and healthy"""
    try:
        response = requests.get(f"{backend_url}/health", timeout=10)
        response.raise_for_status()
        
        health = response.json()
        status = health.get("status", "unknown")
        
        print(f"🏥 Backend health: {status}")
        
        if status != "healthy":
            print("⚠️ Backend is not fully healthy, but will attempt to proceed")
        
        return True
        
    except requests.RequestException as e:
        print(f"❌ Backend health check failed: {e}")
        print("💡 Make sure the FastAPI backend is running on http://localhost:8000")
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Set up embeddings for financial transcripts")
    
    parser.add_argument(
        "--backend-url",
        default="http://localhost:8000",
        help="Backend API URL (default: http://localhost:8000)"
    )
    
    parser.add_argument(
        "--companies",
        nargs="+",
        choices=["AAPL", "AMD", "AMZN", "ASML", "CSCO", "GOOGL", "INTC", "MSFT", "MU", "NVDA"],
        help="Specific companies to process (default: all)"
    )
    
    parser.add_argument(
        "--force-recreate",
        action="store_true",
        help="Force recreation of existing embeddings"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for processing (default: 32)"
    )
    
    parser.add_argument(
        "--check-health-only",
        action="store_true",
        help="Only check backend health and exit"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  Financial Transcripts RAG - Embedding Setup")
    print("=" * 60)
    print()
    
    # Check backend health
    if not check_backend_health(args.backend_url):
        sys.exit(1)
    
    if args.check_health_only:
        print("✅ Backend health check passed")
        sys.exit(0)
    
    print()
    
    # Set up embeddings
    success = setup_embeddings_via_api(
        backend_url=args.backend_url,
        companies=args.companies,
        force_recreate=args.force_recreate,
        batch_size=args.batch_size
    )
    
    if success:
        print("\n🎯 Setup completed successfully!")
        print("💡 You can now start querying the system via the Streamlit interface")
        sys.exit(0)
    else:
        print("\n💥 Setup failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 