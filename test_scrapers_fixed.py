#!/usr/bin/env python3
"""
Test the updated scrapers to verify they return structured data
"""

import sys
from amazon_search import search_amazon
from flipkart_search import search_flipkart  
from meesho_search import search_meesho
from myntra_search import search_myntra

def test_scraper(scraper_func, platform_name, query="phones"):
    """Test a single scraper"""
    print(f"\n🔍 Testing {platform_name} scraper with query: '{query}'")
    print("=" * 60)
    
    try:
        if platform_name in ["Amazon", "Flipkart", "Myntra"]:
            result = scraper_func(query, headless=True, max_results=3)
        else:  # Meesho
            result = scraper_func(query, headless=True)
        
        if result:
            print(f"✅ {platform_name} scraper returned data:")
            print(f"   Site: {result.get('site', 'Unknown')}")
            print(f"   Query: {result.get('query', 'Unknown')}")
            print(f"   Total Products: {result.get('total_products', 0)}")
            
            # Handle different structures
            products = result.get('products', [])
            basic_products = result.get('basic_products', [])
            
            if products:
                print(f"   Products found: {len(products)}")
                if products:
                    first_product = products[0]
                    print(f"   First product: {first_product.get('name', 'No name')[:50]}...")
            elif basic_products:
                print(f"   Basic products found: {len(basic_products)}")
                if basic_products:
                    first_product = basic_products[0]
                    print(f"   First product: {first_product.get('title', first_product.get('name', 'No name'))[:50]}...")
            else:
                print(f"   No products found")
            
            if result.get('error'):
                print(f"   Error: {result['error']}")
            
            return True
        else:
            print(f"❌ {platform_name} scraper returned None")
            return False
            
    except Exception as e:
        print(f"❌ {platform_name} scraper failed: {e}")
        return False

def main():
    """Test all scrapers"""
    print("🧪 Testing Updated Scrapers")
    print("=" * 80)
    
    query = "phones"  # Simple test query
    
    scrapers = [
        (search_amazon, "Amazon"),
        (search_flipkart, "Flipkart"), 
        (search_meesho, "Meesho"),
        (search_myntra, "Myntra")
    ]
    
    results = {}
    
    for scraper_func, platform_name in scrapers:
        success = test_scraper(scraper_func, platform_name, query)
        results[platform_name] = success
    
    print("\n" + "=" * 80)
    print("🏁 FINAL RESULTS")
    print("=" * 80)
    
    for platform, success in results.items():
        status = "✅ WORKING" if success else "❌ FAILED"
        print(f"{platform:15} | {status}")
    
    working_count = sum(results.values())
    total_count = len(results)
    
    print(f"\nSummary: {working_count}/{total_count} scrapers working properly")
    
    if working_count == total_count:
        print("🎉 All scrapers are working! The intelligent search system should work now.")
    elif working_count > 0:
        print(f"⚠️ {working_count} scrapers working. The system will work with limited platforms.")
    else:
        print("❌ No scrapers working. There may be issues with the scraper implementations.")

if __name__ == "__main__":
    main()
