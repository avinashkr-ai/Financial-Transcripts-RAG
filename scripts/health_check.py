#!/usr/bin/env python3
"""
Health check script for the Financial Transcripts RAG system.
Monitors all components and provides detailed status information.
"""

import sys
import argparse
import requests
import time
from typing import Dict, Any, List
from datetime import datetime


def check_backend_api(backend_url: str) -> Dict[str, Any]:
    """Check FastAPI backend health"""
    try:
        # Basic connectivity
        start_time = time.time()
        response = requests.get(f"{backend_url}/health", timeout=10)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            health_data = response.json()
            
            return {
                "status": "healthy",
                "response_time": f"{response_time:.3f}s",
                "details": health_data,
                "api_accessible": True
            }
        else:
            return {
                "status": "error",
                "response_time": f"{response_time:.3f}s",
                "details": {"error": f"HTTP {response.status_code}"},
                "api_accessible": False
            }
    
    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "response_time": "N/A",
            "details": {"error": "Connection refused - API may not be running"},
            "api_accessible": False
        }
    
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "response_time": ">10s",
            "details": {"error": "Request timeout"},
            "api_accessible": False
        }
    
    except Exception as e:
        return {
            "status": "error",
            "response_time": "N/A",
            "details": {"error": str(e)},
            "api_accessible": False
        }


def check_companies_data(backend_url: str) -> Dict[str, Any]:
    """Check companies data availability"""
    try:
        response = requests.get(f"{backend_url}/companies", timeout=15)
        response.raise_for_status()
        
        data = response.json()
        companies = data.get("companies", [])
        
        # Analyze company data
        total_companies = len(companies)
        companies_with_data = sum(1 for c in companies if c.get("transcript_count", 0) > 0)
        total_transcripts = sum(c.get("transcript_count", 0) for c in companies)
        
        return {
            "status": "healthy" if companies_with_data > 0 else "warning",
            "total_companies": total_companies,
            "companies_with_data": companies_with_data,
            "total_transcripts": total_transcripts,
            "details": companies
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "total_companies": 0,
            "companies_with_data": 0,
            "total_transcripts": 0
        }


def check_embedding_status(backend_url: str) -> Dict[str, Any]:
    """Check embedding generation status"""
    try:
        response = requests.get(f"{backend_url}/api/v1/embeddings/status", timeout=10)
        response.raise_for_status()
        
        status_data = response.json()
        current_status = status_data.get("status", "unknown")
        
        # Determine health based on status
        if current_status in ["completed", "idle"]:
            health_status = "healthy"
        elif current_status == "processing":
            health_status = "working"
        else:
            health_status = "warning"
        
        return {
            "status": health_status,
            "embedding_status": current_status,
            "details": status_data
        }
    
    except Exception as e:
        return {
            "status": "error",
            "embedding_status": "unknown",
            "error": str(e)
        }


def check_system_info(backend_url: str) -> Dict[str, Any]:
    """Get system information"""
    try:
        response = requests.get(f"{backend_url}/system/info", timeout=10)
        response.raise_for_status()
        
        return {
            "status": "healthy",
            "details": response.json()
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def test_query_functionality(backend_url: str) -> Dict[str, Any]:
    """Test basic query functionality"""
    try:
        test_query = {
            "question": "What is revenue?",
            "max_results": 1,
            "similarity_threshold": 0.5
        }
        
        start_time = time.time()
        response = requests.post(
            f"{backend_url}/api/v1/query",
            json=test_query,
            timeout=30
        )
        query_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get("answer", "")
            sources = result.get("sources", [])
            
            return {
                "status": "healthy",
                "query_time": f"{query_time:.3f}s",
                "answer_length": len(answer),
                "sources_count": len(sources),
                "functional": True
            }
        else:
            return {
                "status": "error",
                "query_time": f"{query_time:.3f}s",
                "error": f"HTTP {response.status_code}",
                "functional": False
            }
    
    except Exception as e:
        return {
            "status": "error",
            "query_time": "N/A",
            "error": str(e),
            "functional": False
        }


def run_comprehensive_health_check(backend_url: str) -> Dict[str, Any]:
    """Run all health checks"""
    print(f"🏥 Running comprehensive health check for {backend_url}")
    print("=" * 60)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "backend_url": backend_url,
        "checks": {}
    }
    
    # 1. Backend API Health
    print("1️⃣ Checking backend API health...")
    results["checks"]["api_health"] = check_backend_api(backend_url)
    print(f"   Status: {results['checks']['api_health']['status']}")
    
    if not results["checks"]["api_health"]["api_accessible"]:
        print("❌ Backend API is not accessible. Stopping health check.")
        return results
    
    # 2. Companies Data
    print("2️⃣ Checking companies data...")
    results["checks"]["companies_data"] = check_companies_data(backend_url)
    print(f"   Status: {results['checks']['companies_data']['status']}")
    
    # 3. Embedding Status
    print("3️⃣ Checking embedding status...")
    results["checks"]["embedding_status"] = check_embedding_status(backend_url)
    print(f"   Status: {results['checks']['embedding_status']['status']}")
    
    # 4. System Information
    print("4️⃣ Getting system information...")
    results["checks"]["system_info"] = check_system_info(backend_url)
    print(f"   Status: {results['checks']['system_info']['status']}")
    
    # 5. Query Functionality Test
    print("5️⃣ Testing query functionality...")
    results["checks"]["query_test"] = test_query_functionality(backend_url)
    print(f"   Status: {results['checks']['query_test']['status']}")
    
    return results


def print_detailed_report(results: Dict[str, Any]):
    """Print detailed health check report"""
    print("\n" + "=" * 80)
    print("  DETAILED HEALTH CHECK REPORT")
    print("=" * 80)
    
    timestamp = results.get("timestamp", "unknown")
    backend_url = results.get("backend_url", "unknown")
    
    print(f"Timestamp: {timestamp}")
    print(f"Backend URL: {backend_url}")
    print()
    
    checks = results.get("checks", {})
    
    # Overall status
    all_healthy = all(
        check.get("status") == "healthy" 
        for check in checks.values()
    )
    
    overall_status = "🟢 HEALTHY" if all_healthy else "🟡 ISSUES DETECTED"
    print(f"Overall Status: {overall_status}")
    print()
    
    # API Health
    api_health = checks.get("api_health", {})
    print("🔌 API HEALTH")
    print("-" * 40)
    print(f"Status: {api_health.get('status', 'unknown')}")
    print(f"Response Time: {api_health.get('response_time', 'N/A')}")
    if api_health.get("details"):
        details = api_health["details"]
        if isinstance(details, dict):
            print(f"Database: {details.get('database_status', 'unknown')}")
            print(f"Embeddings: {details.get('embeddings_status', 'unknown')}")
    print()
    
    # Companies Data
    companies_data = checks.get("companies_data", {})
    print("🏢 COMPANIES DATA")
    print("-" * 40)
    print(f"Status: {companies_data.get('status', 'unknown')}")
    print(f"Total Companies: {companies_data.get('total_companies', 0)}")
    print(f"Companies with Data: {companies_data.get('companies_with_data', 0)}")
    print(f"Total Transcripts: {companies_data.get('total_transcripts', 0)}")
    print()
    
    # Embedding Status
    embedding_status = checks.get("embedding_status", {})
    print("🔄 EMBEDDING STATUS")
    print("-" * 40)
    print(f"Status: {embedding_status.get('status', 'unknown')}")
    print(f"Embedding Process: {embedding_status.get('embedding_status', 'unknown')}")
    
    if embedding_status.get("details"):
        details = embedding_status["details"]
        if details.get("progress") is not None:
            print(f"Progress: {details.get('progress', 0):.1f}%")
        if details.get("current_company"):
            print(f"Current Company: {details.get('current_company')}")
    print()
    
    # Query Test
    query_test = checks.get("query_test", {})
    print("🔍 QUERY FUNCTIONALITY")
    print("-" * 40)
    print(f"Status: {query_test.get('status', 'unknown')}")
    print(f"Functional: {query_test.get('functional', False)}")
    if query_test.get("query_time"):
        print(f"Query Time: {query_test.get('query_time')}")
    if query_test.get("sources_count") is not None:
        print(f"Sources Found: {query_test.get('sources_count')}")
    print()
    
    # Issues Summary
    issues = []
    for check_name, check_result in checks.items():
        if check_result.get("status") not in ["healthy", "working"]:
            error_msg = check_result.get("error", "Unknown error")
            issues.append(f"{check_name}: {error_msg}")
    
    if issues:
        print("⚠️ ISSUES FOUND")
        print("-" * 40)
        for issue in issues:
            print(f"• {issue}")
        print()
    else:
        print("✅ NO ISSUES FOUND")
        print()


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Health check for Financial Transcripts RAG system")
    
    parser.add_argument(
        "--backend-url",
        default="http://localhost:8000",
        help="Backend API URL (default: http://localhost:8000)"
    )
    
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Show only summary status"
    )
    
    parser.add_argument(
        "--continuous",
        type=int,
        metavar="SECONDS",
        help="Run continuous monitoring with specified interval"
    )
    
    args = parser.parse_args()
    
    try:
        if args.continuous:
            print(f"🔄 Starting continuous monitoring (interval: {args.continuous}s)")
            print("Press Ctrl+C to stop")
            
            while True:
                results = run_comprehensive_health_check(args.backend_url)
                
                if args.summary_only:
                    all_healthy = all(
                        check.get("status") == "healthy" 
                        for check in results.get("checks", {}).values()
                    )
                    status = "HEALTHY" if all_healthy else "ISSUES"
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] System Status: {status}")
                else:
                    print_detailed_report(results)
                
                time.sleep(args.continuous)
        
        else:
            results = run_comprehensive_health_check(args.backend_url)
            
            if args.summary_only:
                all_healthy = all(
                    check.get("status") == "healthy" 
                    for check in results.get("checks", {}).values()
                )
                
                if all_healthy:
                    print("✅ System Status: HEALTHY")
                    sys.exit(0)
                else:
                    print("⚠️ System Status: ISSUES DETECTED")
                    sys.exit(1)
            else:
                print_detailed_report(results)
    
    except KeyboardInterrupt:
        print("\n⏹️ Health check interrupted by user")
        sys.exit(0)
    
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 