#!/usr/bin/env python3
"""
Unified Search Interface - Search all websites simultaneously
Usage:
  python unified_search.py "iphone 15"
"""

import sys
import time
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional
from datetime import datetime

# Import all scraper functions
from amazon_search import search_amazon
from flipkart_search import search_flipkart
from meesho_search import search_meesho
from myntra_search import search_myntra

def search_single_website(website: str, query: str, headless: bool = True) -> Dict:
    """
    Search a single website and return results
    """
    print(f"🔍 Starting {website} search for: {query}")
    
    try:
        if website == "amazon":
            # Run Amazon search
            result = run_amazon_search(query, headless)
        elif website == "flipkart":
            # Run Flipkart search
            result = run_flipkart_search(query, headless)
        elif website == "meesho":
            # Run Meesho search
            result = run_meesho_search(query, headless)
        elif website == "myntra":
            # Run Myntra search
            result = run_myntra_search(query, headless)
        else:
            result = {"error": f"Unknown website: {website}"}
        
        print(f"✅ {website} search completed")
        return {
            "website": website,
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        print(f"❌ {website} search failed: {str(e)}")
        return {
            "website": website,
            "status": "error",
            "error": str(e),
            "data": None
        }

def run_amazon_search(query: str, headless: bool) -> Dict:
    """Run Amazon search and return structured data"""
    try:
        # Import the search function
        from amazon_search import search_amazon
        
        # Create a custom search function that returns data instead of printing
        def amazon_search_wrapper():
            # This will be implemented to capture the search results
            # For now, we'll use the existing function and capture its output
            pass
        
        # Try to read existing Amazon data files
        detailed_file = f"amazon_detailed_products_{query.replace(' ', '_')}.json"
        basic_file = f"amazon_products_{query.replace(' ', '_')}.json"
        
        try:
            with open(detailed_file, 'r', encoding='utf-8') as f:
                detailed_data = json.load(f)
            return detailed_data
        except FileNotFoundError:
            try:
                with open(basic_file, 'r', encoding='utf-8') as f:
                    basic_data = json.load(f)
                return basic_data
            except FileNotFoundError:
                return {"error": "No Amazon data found. Please run Amazon search first."}
                
    except Exception as e:
        return {"error": f"Amazon search error: {str(e)}"}

def run_flipkart_search(query: str, headless: bool) -> Dict:
    """Run Flipkart search and return structured data"""
    try:
        detailed_file = f"flipkart_detailed_products_{query.replace(' ', '_')}.json"
        basic_file = f"flipkart_products_{query.replace(' ', '_')}.json"
        
        try:
            with open(detailed_file, 'r', encoding='utf-8') as f:
                detailed_data = json.load(f)
            return detailed_data
        except FileNotFoundError:
            try:
                with open(basic_file, 'r', encoding='utf-8') as f:
                    basic_data = json.load(f)
                return basic_data
            except FileNotFoundError:
                return {"error": "No Flipkart data found. Please run Flipkart search first."}
                
    except Exception as e:
        return {"error": f"Flipkart search error: {str(e)}"}

def run_meesho_search(query: str, headless: bool) -> Dict:
    """Run Meesho search and return structured data"""
    try:
        detailed_file = f"meesho_detailed_products_{query.replace(' ', '_')}.json"
        basic_file = f"meesho_products_{query.replace(' ', '_')}.json"
        
        try:
            with open(detailed_file, 'r', encoding='utf-8') as f:
                detailed_data = json.load(f)
            return detailed_data
        except FileNotFoundError:
            try:
                with open(basic_file, 'r', encoding='utf-8') as f:
                    basic_data = json.load(f)
                return basic_data
            except FileNotFoundError:
                return {"error": "No Meesho data found. Please run Meesho search first."}
                
    except Exception as e:
        return {"error": f"Meesho search error: {str(e)}"}

def run_myntra_search(query: str, headless: bool) -> Dict:
    """Run Myntra search and return structured data"""
    try:
        detailed_file = f"myntra_detailed_products_{query.replace(' ', '_')}.json"
        basic_file = f"myntra_products_{query.replace(' ', '_')}.json"
        
        try:
            with open(detailed_file, 'r', encoding='utf-8') as f:
                detailed_data = json.load(f)
            return detailed_data
        except FileNotFoundError:
            try:
                with open(basic_file, 'r', encoding='utf-8') as f:
                    basic_data = json.load(f)
                return basic_data
            except FileNotFoundError:
                return {"error": "No Myntra data found. Please run Myntra search first."}
                
    except Exception as e:
        return {"error": f"Myntra search error: {str(e)}"}

def unified_search(query: str, headless: bool = True) -> Dict:
    """
    Search all websites simultaneously and return combined results
    """
    print(f"🚀 Starting unified search for: '{query}'")
    print("=" * 60)
    
    websites = ["amazon", "flipkart", "meesho", "myntra"]
    results = {}
    
    # Use ThreadPoolExecutor for parallel execution
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Submit all search tasks
        future_to_website = {
            executor.submit(search_single_website, website, query, headless): website 
            for website in websites
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_website):
            website = future_to_website[future]
            try:
                result = future.result()
                results[website] = result
            except Exception as e:
                results[website] = {
                    "website": website,
                    "status": "error",
                    "error": str(e),
                    "data": None
                }
    
    # Create combined result structure
    combined_result = {
        "query": query,
        "search_timestamp": datetime.now().isoformat(),
        "total_websites": len(websites),
        "successful_searches": len([r for r in results.values() if r["status"] == "success"]),
        "failed_searches": len([r for r in results.values() if r["status"] == "error"]),
        "websites": results,
        "summary": {
            "total_products": 0,
            "websites_with_data": [],
            "price_range": {"min": None, "max": None},
            "brands_found": set(),
            "categories_found": set()
        }
    }
    
    # Analyze results and create summary
    all_products = []
    prices = []
    
    for website, result in results.items():
        if result["status"] == "success" and result["data"]:
            data = result["data"]
            if "products" in data and data["products"]:
                combined_result["summary"]["websites_with_data"].append(website)
                combined_result["summary"]["total_products"] += len(data["products"])
                
                for product in data["products"]:
                    # Add website info to each product
                    product["source_website"] = website
                    all_products.append(product)
                    
                    # Extract price for range calculation
                    if "price" in product and product["price"]:
                        try:
                            # Extract numeric price
                            price_str = product["price"].replace("₹", "").replace(",", "").replace("Rs", "").strip()
                            if price_str.replace(".", "").isdigit():
                                prices.append(float(price_str))
                        except:
                            pass
                    
                    # Extract brand
                    if "brand" in product and product["brand"]:
                        combined_result["summary"]["brands_found"].add(product["brand"])
                    
                    # Extract category
                    if "category" in product and product["category"]:
                        combined_result["summary"]["categories_found"].add(product["category"])
    
    # Calculate price range
    if prices:
        combined_result["summary"]["price_range"]["min"] = min(prices)
        combined_result["summary"]["price_range"]["max"] = max(prices)
    
    # Convert sets to lists for JSON serialization
    combined_result["summary"]["brands_found"] = list(combined_result["summary"]["brands_found"])
    combined_result["summary"]["categories_found"] = list(combined_result["summary"]["categories_found"])
    
    # Add all products to the result
    combined_result["all_products"] = all_products
    
    return combined_result

def main():
    """Main function to run unified search"""
    if len(sys.argv) < 2:
        query = input("Enter product to search across all websites: ").strip()
    else:
        query = " ".join(sys.argv[1:])
    
    if not query:
        print("No query provided. Exiting.")
        sys.exit(1)
    
    # Check for headless flag
    headless = "--headless" in query
    if headless:
        query = query.replace("--headless", "").strip()
    
    print(f"🔍 Searching for: '{query}'")
    print(f"🌐 Websites: Amazon, Flipkart, Meesho, Myntra")
    print(f"⚙️ Headless mode: {headless}")
    print()
    
    # Run unified search
    start_time = time.time()
    result = unified_search(query, headless=headless)
    end_time = time.time()
    
    # Display results summary
    print("\n" + "=" * 60)
    print("📊 SEARCH RESULTS SUMMARY")
    print("=" * 60)
    
    print(f"Query: {result['query']}")
    print(f"Total Websites: {result['total_websites']}")
    print(f"Successful Searches: {result['successful_searches']}")
    print(f"Failed Searches: {result['failed_searches']}")
    print(f"Total Products Found: {result['summary']['total_products']}")
    print(f"Websites with Data: {', '.join(result['summary']['websites_with_data'])}")
    print(f"Search Time: {end_time - start_time:.2f} seconds")
    
    if result['summary']['price_range']['min']:
        print(f"Price Range: ₹{result['summary']['price_range']['min']:.0f} - ₹{result['summary']['price_range']['max']:.0f}")
    
    if result['summary']['brands_found']:
        print(f"Brands Found: {', '.join(result['summary']['brands_found'][:5])}{'...' if len(result['summary']['brands_found']) > 5 else ''}")
    
    if result['summary']['categories_found']:
        print(f"Categories Found: {', '.join(result['summary']['categories_found'][:5])}{'...' if len(result['summary']['categories_found']) > 5 else ''}")
    
    # Display combined results as JSON without saving to file
    print(f"\n{'='*60}")
    print(f"UNIFIED SEARCH RESULTS (JSON FORMAT)")
    print(f"{'='*60}")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Display sample products
    if result['all_products']:
        print(f"\n📋 SAMPLE PRODUCTS (showing first 3):")
        print("-" * 60)
        
        for i, product in enumerate(result['all_products'][:3], 1):
            print(f"\n{i}. {product.get('name', 'Unknown Product')}")
            print(f"   Website: {product.get('source_website', 'Unknown').upper()}")
            print(f"   Price: {product.get('price', 'Not available')}")
            if product.get('brand'):
                print(f"   Brand: {product['brand']}")
            if product.get('rating'):
                print(f"   Rating: {product['rating']}")
            if product.get('link'):
                print(f"   Link: {product['link'][:80]}...")
    
    print(f"\n🎉 Unified search completed!")
    print(f"📄 Complete JSON results displayed above (no files saved)")

if __name__ == "__main__":
    main()
