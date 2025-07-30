#!/usr/bin/env python3
"""
Script to load and validate financial transcript data.
Provides utilities for checking data integrity and structure.
"""

import os
import sys
from pathlib import Path
import argparse
from typing import Dict, List, Any
import re
from datetime import datetime


def scan_transcripts_directory(transcripts_path: str) -> Dict[str, Any]:
    """Scan the transcripts directory and return summary statistics"""
    transcripts_dir = Path(transcripts_path)
    
    if not transcripts_dir.exists():
        raise FileNotFoundError(f"Transcripts directory not found: {transcripts_path}")
    
    companies = {}
    total_files = 0
    total_size = 0
    
    # Expected companies
    expected_companies = ["AAPL", "AMD", "AMZN", "ASML", "CSCO", "GOOGL", "INTC", "MSFT", "MU", "NVDA"]
    
    for company_dir in transcripts_dir.iterdir():
        if company_dir.is_dir() and company_dir.name in expected_companies:
            company_name = company_dir.name
            companies[company_name] = {
                "files": [],
                "file_count": 0,
                "total_size": 0,
                "date_range": {"earliest": None, "latest": None},
                "missing_files": [],
                "invalid_files": []
            }
            
            # Scan transcript files
            for transcript_file in company_dir.glob("*.txt"):
                try:
                    file_size = transcript_file.stat().st_size
                    file_info = {
                        "filename": transcript_file.name,
                        "size": file_size,
                        "path": str(transcript_file)
                    }
                    
                    # Extract date from filename
                    date_match = extract_date_from_filename(transcript_file.name)
                    if date_match:
                        file_info["date"] = date_match
                        
                        # Update date range
                        if companies[company_name]["date_range"]["earliest"] is None or date_match < companies[company_name]["date_range"]["earliest"]:
                            companies[company_name]["date_range"]["earliest"] = date_match
                        
                        if companies[company_name]["date_range"]["latest"] is None or date_match > companies[company_name]["date_range"]["latest"]:
                            companies[company_name]["date_range"]["latest"] = date_match
                    else:
                        companies[company_name]["invalid_files"].append(transcript_file.name)
                    
                    companies[company_name]["files"].append(file_info)
                    companies[company_name]["file_count"] += 1
                    companies[company_name]["total_size"] += file_size
                    
                    total_files += 1
                    total_size += file_size
                    
                except Exception as e:
                    print(f"Error processing {transcript_file}: {e}")
                    companies[company_name]["invalid_files"].append(transcript_file.name)
    
    return {
        "total_files": total_files,
        "total_size": total_size,
        "companies": companies,
        "summary": generate_summary(companies)
    }


def extract_date_from_filename(filename: str) -> str:
    """Extract date from transcript filename"""
    # Common patterns in filenames
    patterns = [
        r'(\d{4})-(\w{3})-(\d{1,2})',  # 2020-Apr-30
        r'(\w{3})-(\d{4})',            # Apr-2020
        r'(\d{4})-(\d{2})-(\d{2})',    # 2020-04-30
    ]
    
    month_map = {
        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
        'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
        'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
    }
    
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            groups = match.groups()
            
            if len(groups) == 3:  # YYYY-MMM-DD format
                year, month_str, day = groups
                month = month_map.get(month_str, '01')
                return f"{year}-{month}-{day.zfill(2)}"
            
            elif len(groups) == 2:  # MMM-YYYY format
                month_str, year = groups
                month = month_map.get(month_str, '01')
                return f"{year}-{month}-01"  # Default to 1st of month
    
    return None


def generate_summary(companies: Dict[str, Any]) -> Dict[str, Any]:
    """Generate summary statistics"""
    total_companies = len(companies)
    companies_with_data = sum(1 for c in companies.values() if c["file_count"] > 0)
    
    total_files = sum(c["file_count"] for c in companies.values())
    total_size = sum(c["total_size"] for c in companies.values())
    
    # Date range across all companies
    all_dates = []
    for company_data in companies.values():
        if company_data["date_range"]["earliest"]:
            all_dates.append(company_data["date_range"]["earliest"])
        if company_data["date_range"]["latest"]:
            all_dates.append(company_data["date_range"]["latest"])
    
    overall_date_range = {
        "earliest": min(all_dates) if all_dates else None,
        "latest": max(all_dates) if all_dates else None
    }
    
    return {
        "total_companies": total_companies,
        "companies_with_data": companies_with_data,
        "total_files": total_files,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "overall_date_range": overall_date_range,
        "average_files_per_company": round(total_files / companies_with_data, 1) if companies_with_data > 0 else 0
    }


def validate_data_integrity(scan_results: Dict[str, Any]) -> List[str]:
    """Validate data integrity and return list of issues"""
    issues = []
    
    companies = scan_results["companies"]
    
    # Check for missing companies
    expected_companies = ["AAPL", "AMD", "AMZN", "ASML", "CSCO", "GOOGL", "INTC", "MSFT", "MU", "NVDA"]
    missing_companies = [c for c in expected_companies if c not in companies or companies[c]["file_count"] == 0]
    
    if missing_companies:
        issues.append(f"Missing data for companies: {', '.join(missing_companies)}")
    
    # Check for companies with very few files
    for company, data in companies.items():
        if data["file_count"] < 5:
            issues.append(f"{company} has only {data['file_count']} transcript files (expected ~19)")
    
    # Check for invalid files
    for company, data in companies.items():
        if data["invalid_files"]:
            issues.append(f"{company} has invalid files: {', '.join(data['invalid_files'])}")
    
    # Check file sizes
    for company, data in companies.items():
        avg_size = data["total_size"] / data["file_count"] if data["file_count"] > 0 else 0
        if avg_size < 1000:  # Less than 1KB average
            issues.append(f"{company} has unusually small files (avg: {avg_size:.0f} bytes)")
    
    return issues


def print_detailed_report(scan_results: Dict[str, Any]):
    """Print a detailed report of the scan results"""
    summary = scan_results["summary"]
    companies = scan_results["companies"]
    
    print("=" * 80)
    print("  FINANCIAL TRANSCRIPTS DATA REPORT")
    print("=" * 80)
    print()
    
    # Summary
    print("📊 SUMMARY")
    print("-" * 40)
    print(f"Total Companies: {summary['total_companies']}")
    print(f"Companies with Data: {summary['companies_with_data']}")
    print(f"Total Transcript Files: {summary['total_files']}")
    print(f"Total Data Size: {summary['total_size_mb']:.2f} MB")
    print(f"Average Files per Company: {summary['average_files_per_company']}")
    
    if summary["overall_date_range"]["earliest"]:
        print(f"Date Range: {summary['overall_date_range']['earliest']} to {summary['overall_date_range']['latest']}")
    
    print()
    
    # Company details
    print("🏢 COMPANY DETAILS")
    print("-" * 40)
    for company, data in sorted(companies.items()):
        print(f"{company}:")
        print(f"  Files: {data['file_count']}")
        print(f"  Size: {data['total_size'] / (1024*1024):.2f} MB")
        
        if data["date_range"]["earliest"]:
            print(f"  Date Range: {data['date_range']['earliest']} to {data['date_range']['latest']}")
        
        if data["invalid_files"]:
            print(f"  ⚠️ Invalid Files: {', '.join(data['invalid_files'])}")
        
        print()
    
    # Validation issues
    issues = validate_data_integrity(scan_results)
    if issues:
        print("⚠️ DATA ISSUES")
        print("-" * 40)
        for issue in issues:
            print(f"• {issue}")
        print()
    else:
        print("✅ DATA VALIDATION PASSED")
        print()


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Load and validate financial transcript data")
    
    parser.add_argument(
        "--transcripts-path",
        default="../Transcripts",
        help="Path to the transcripts directory (default: ../Transcripts)"
    )
    
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Show only summary statistics"
    )
    
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only run validation and show issues"
    )
    
    args = parser.parse_args()
    
    try:
        # Scan the transcripts directory
        print(f"🔍 Scanning transcripts directory: {args.transcripts_path}")
        print()
        
        scan_results = scan_transcripts_directory(args.transcripts_path)
        
        if args.validate_only:
            issues = validate_data_integrity(scan_results)
            if issues:
                print("⚠️ Validation Issues Found:")
                for issue in issues:
                    print(f"• {issue}")
                sys.exit(1)
            else:
                print("✅ All validation checks passed!")
                sys.exit(0)
        
        elif args.summary_only:
            summary = scan_results["summary"]
            print(f"Files: {summary['total_files']}")
            print(f"Size: {summary['total_size_mb']:.2f} MB")
            print(f"Companies: {summary['companies_with_data']}/{summary['total_companies']}")
            if summary["overall_date_range"]["earliest"]:
                print(f"Range: {summary['overall_date_range']['earliest']} to {summary['overall_date_range']['latest']}")
        
        else:
            print_detailed_report(scan_results)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 