#!/usr/bin/env python3
"""
Test all scrapers with detailed output
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
            
            # Show only the products array for cleaner output
            products = result.get('products', [])
            if products:
                print("\n📋 Products:")
                for i, product in enumerate(products, 1):
                    print(f"\n   Product {i}:")
                    print(f"     Name: {product.get('name', 'N/A')}")
                    print(f"     Price: {product.get('price', 'N/A')}")
                    print(f"     Brand: {product.get('brand', 'N/A')}")
                    print(f"     Category: {product.get('category', 'N/A')}")
                    print(f"     Rating: {product.get('rating', 'N/A')}")
                    print(f"     Link: {product.get('link', 'N/A')[:80]}...")
            else:
                print("   No products found")
                
    except Exception as e:
        print(f"❌ {name} Exception: {e}")

def main():
    """Main test function"""
    query = "mobile phones"
    
    print(f"Testing all improved scrapers with query: '{query}'")
    
    # Test Amazon
    amazon_scraper = AmazonScraper()
    test_scraper_detailed(amazon_scraper, query, "Amazon")
    
    # Test Flipkart
    flipkart_scraper = FlipkartScraper()
    test_scraper_detailed(flipkart_scraper, query, "Flipkart")
    
    # Test Meesho
    meesho_scraper = MeeshoScraper()
    test_scraper_detailed(meesho_scraper, query, "Meesho")
    
    # Test Myntra
    myntra_scraper = MyntraScraper()
    test_scraper_detailed(myntra_scraper, query, "Myntra")

if __name__ == "__main__":
    main()
