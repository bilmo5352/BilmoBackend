#!/usr/bin/env python3
"""
Test script to debug Meesho and Myntra scrapers
"""

import sys
import time
from app import MeeshoScraper, MyntraScraper

def test_scraper(scraper, query, name):
    """Test a specific scraper"""
    print(f"\n{'='*60}")
    print(f"Testing {name} scraper with query: '{query}'")
    print(f"{'='*60}")
    
    try:
        result = scraper.search(query, max_results=3)
        
        if result.get('error'):
            print(f"❌ {name} Error: {result['error']}")
        else:
            print(f"✅ {name} Success!")
            print(f"   Found {result.get('total_products', 0)} products")
            
            for i, product in enumerate(result.get('products', []), 1):
                print(f"\n   Product {i}:")
                print(f"     Title: {product.get('title', 'N/A')}")
                print(f"     Price: {product.get('price', 'N/A')}")
                print(f"     Brand: {product.get('brand', 'N/A')}")
                print(f"     Link: {product.get('link', 'N/A')[:50]}...")
                
    except Exception as e:
        print(f"❌ {name} Exception: {e}")

def main():
    """Main test function"""
    if len(sys.argv) < 2:
        query = "shoes"
    else:
        query = " ".join(sys.argv[1:])
    
    print(f"Testing scrapers with query: '{query}'")
    
    # Test Meesho
    meesho_scraper = MeeshoScraper()
    test_scraper(meesho_scraper, query, "Meesho")
    
    # Wait a bit between tests
    time.sleep(2)
    
    # Test Myntra
    myntra_scraper = MyntraScraper()
    test_scraper(myntra_scraper, query, "Myntra")
    
    print(f"\n{'='*60}")
    print("Test completed!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()


