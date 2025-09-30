#!/usr/bin/env python3
"""
Comprehensive Test Script for All Scrapers
Tests Flipkart, Meesho, and Myntra scrapers with various product types
"""

import subprocess
import json
import time
import sys
from datetime import datetime

def run_scraper(scraper_name, query, headless=True):
    """Run a scraper and return the results"""
    print(f"\n{'='*60}")
    print(f"TESTING {scraper_name.upper()} SCRAPER")
    print(f"Query: {query}")
    print(f"{'='*60}")
    
    try:
        cmd = f"python {scraper_name}_search.py \"{query}\" --headless"
        if not headless:
            cmd = f"python {scraper_name}_search.py \"{query}\""
        
        print(f"Running: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"✅ {scraper_name} scraper completed successfully")
            return True, result.stdout
        else:
            print(f"❌ {scraper_name} scraper failed")
            print(f"Error: {result.stderr}")
            return False, result.stderr
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {scraper_name} scraper timed out")
        return False, "Timeout"
    except Exception as e:
        print(f"❌ {scraper_name} scraper error: {e}")
        return False, str(e)

def test_scraper_data_extraction(output, scraper_name):
    """Test if the scraper extracted the expected data fields"""
    print(f"\n🔍 ANALYZING {scraper_name.upper()} DATA EXTRACTION")
    
    expected_fields = {
        'flipkart': ['price', 'mrp', 'discount_percentage', 'discount_amount', 'rating', 'brand', 'title'],
        'meesho': ['price', 'rating', 'brand', 'title', 'availability'],
        'myntra': ['price', 'rating', 'brand', 'title', 'discount']
    }
    
    fields_found = {}
    for field in expected_fields.get(scraper_name, []):
        if field in output.lower():
            fields_found[field] = True
            print(f"  ✅ {field}: Found")
        else:
            fields_found[field] = False
            print(f"  ❌ {field}: Missing")
    
    return fields_found

def main():
    """Main test function"""
    print("🚀 COMPREHENSIVE SCRAPER TEST SUITE")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test queries for different product types
    test_queries = [
        "laptop",
        "phone", 
        "helmet",
        "shoes",
        "watch"
    ]
    
    scrapers = ['flipkart', 'meesho']  # Add 'myntra' if needed
    
    results = {}
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"TESTING QUERY: {query.upper()}")
        print(f"{'='*80}")
        
        query_results = {}
        
        for scraper in scrapers:
            success, output = run_scraper(scraper, query, headless=True)
            
            if success:
                data_analysis = test_scraper_data_extraction(output, scraper)
                query_results[scraper] = {
                    'success': True,
                    'data_extraction': data_analysis,
                    'output_length': len(output)
                }
            else:
                query_results[scraper] = {
                    'success': False,
                    'error': output,
                    'data_extraction': {}
                }
            
            # Add delay between scrapers to avoid overwhelming the sites
            time.sleep(2)
        
        results[query] = query_results
        
        # Add delay between queries
        time.sleep(3)
    
    # Generate test report
    print(f"\n{'='*80}")
    print("TEST REPORT SUMMARY")
    print(f"{'='*80}")
    
    total_tests = len(test_queries) * len(scrapers)
    successful_tests = 0
    
    for query, query_results in results.items():
        print(f"\n📊 Query: {query}")
        for scraper, result in query_results.items():
            if result['success']:
                successful_tests += 1
                print(f"  ✅ {scraper}: SUCCESS")
                
                # Show data extraction summary
                data_extraction = result['data_extraction']
                fields_found = sum(1 for found in data_extraction.values() if found)
                total_fields = len(data_extraction)
                print(f"     Data extraction: {fields_found}/{total_fields} fields")
            else:
                print(f"  ❌ {scraper}: FAILED")
                print(f"     Error: {result.get('error', 'Unknown error')[:100]}...")
    
    success_rate = (successful_tests / total_tests) * 100
    print(f"\n📈 OVERALL SUCCESS RATE: {success_rate:.1f}% ({successful_tests}/{total_tests})")
    
    if success_rate >= 80:
        print("🎉 EXCELLENT! Scrapers are working well!")
    elif success_rate >= 60:
        print("⚠️ GOOD! Some scrapers need attention.")
    else:
        print("❌ POOR! Multiple scrapers need fixing.")
    
    # Save detailed results
    report_filename = f"scraper_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Detailed report saved to: {report_filename}")
    print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
