#!/usr/bin/env python3
"""
Detailed test script to see actual JSON output
"""

import json
from app import AmazonScraper, FlipkartScraper, MeeshoScraper, MyntraScraper

def test_scraper_detailed(scraper, query, name):
    """Test a specific scraper and show detailed output"""
    print(f"\n{'='*60}")
    print(f"Testing {name} scraper with query: '{query}'")
    print(f"{'='*60}")
    
    try:
        result = scraper.search(query, max_results=2)
        
        if result.get('error'):
            print(f"❌ {name} Error: {result['error']}")
        else:
            print(f"✅ {name} Success!")
            print(f"   Found {result.get('total_products', 0)} products")
            
            # Pretty print the JSON
            print("\n📋 Raw JSON Output:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
                
    except Exception as e:
        print(f"❌ {name} Exception: {e}")

def main():
    """Main test function"""
    query = "shoes"
    
    print(f"Testing improved scrapers with query: '{query}'")
    
    # Test Myntra first (since it's working well)
    myntra_scraper = MyntraScraper()
    test_scraper_detailed(myntra_scraper, query, "Myntra")

if __name__ == "__main__":
    main()
