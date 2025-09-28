#!/usr/bin/env python3
"""
Unified Search All Platforms - Search Amazon, Flipkart, Meesho, and Myntra
Uses the scrapers from app.py and stores results in MongoDB
"""

import sys
import json
import time
from datetime import datetime
from pymongo import MongoClient
from concurrent.futures import ThreadPoolExecutor, as_completed

# MongoDB Configuration
MONGODB_URI = "mongodb+srv://hrithick:hrithick@bilmo.jmeclfh.mongodb.net/?retryWrites=true&w=majority&appName=bilmo"
DB_NAME = "scraper_db"
COLLECTION_NAME = "search_results"

def connect_mongodb():
    """Connect to MongoDB Atlas"""
    try:
        client = MongoClient(MONGODB_URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        # Test connection
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB Atlas")
        return client, db, collection
    except Exception as e:
        print(f"❌ MongoDB connection error: {e}")
        return None, None, None

def save_to_mongodb(collection, data, query):
    """Save search results to MongoDB"""
    try:
        document = {
            "query": query,
            "timestamp": datetime.now(),
            "data": data,
            "total_results": len(data.get("all_products", [])) if isinstance(data, dict) else len(data) if isinstance(data, list) else 1,
            "search_type": "unified_search_all_platforms"
        }
        
        result = collection.insert_one(document)
        print(f"✅ Saved unified search results to MongoDB with ID: {result.inserted_id}")
        return True
    except Exception as e:
        print(f"❌ Failed to save to MongoDB: {e}")
        return False

def search_amazon(query: str, max_results: int = 8):
    """Search Amazon using the scraper from app.py"""
    try:
        # Import the Amazon scraper from app.py
        from app import AmazonScraper
        scraper = AmazonScraper()
        result = scraper.search(query, max_results)
        return result
    except Exception as e:
        print(f"❌ Amazon search error: {e}")
        return {"error": str(e), "products": []}

def search_flipkart(query: str, max_results: int = 8):
    """Search Flipkart using the scraper from app.py"""
    try:
        # Import the Flipkart scraper from app.py
        from app import FlipkartScraper
        scraper = FlipkartScraper()
        result = scraper.search(query, max_results)
        return result
    except Exception as e:
        print(f"❌ Flipkart search error: {e}")
        return {"error": str(e), "products": []}

def search_meesho(query: str, max_results: int = 8):
    """Search Meesho using the scraper from app.py"""
    try:
        # Import the Meesho scraper from app.py
        from app import MeeshoScraper
        scraper = MeeshoScraper()
        result = scraper.search(query, max_results)
        return result
    except Exception as e:
        print(f"❌ Meesho search error: {e}")
        return {"error": str(e), "products": []}

def search_myntra(query: str, max_results: int = 8):
    """Search Myntra using the scraper from app.py"""
    try:
        # Import the Myntra scraper from app.py
        from app import MyntraScraper
        scraper = MyntraScraper()
        result = scraper.search(query, max_results)
        return result
    except Exception as e:
        print(f"❌ Myntra search error: {e}")
        return {"error": str(e), "products": []}

def search_single_platform(platform: str, query: str, max_results: int = 8):
    """Search a single platform and return results"""
    print(f"🔍 Starting {platform} search for: {query}")
    start_time = time.time()
    
    try:
        if platform == "amazon":
            result = search_amazon(query, max_results)
        elif platform == "flipkart":
            result = search_flipkart(query, max_results)
        elif platform == "meesho":
            result = search_meesho(query, max_results)
        elif platform == "myntra":
            result = search_myntra(query, max_results)
        else:
            result = {"error": f"Unknown platform: {platform}"}
        
        end_time = time.time()
        search_time = end_time - start_time
        
        # Add source platform to each product
        if "products" in result and result["products"]:
            for product in result["products"]:
                product["source_platform"] = platform
        
        print(f"✅ {platform} search completed in {search_time:.2f}s")
        return {
            "platform": platform,
            "status": "success",
            "search_time": search_time,
            "data": result
        }
        
    except Exception as e:
        end_time = time.time()
        search_time = end_time - start_time
        print(f"❌ {platform} search failed: {str(e)}")
        return {
            "platform": platform,
            "status": "error",
            "search_time": search_time,
            "error": str(e),
            "data": None
        }

def unified_search_all_platforms(query: str, max_results: int = 8):
    """Search all platforms simultaneously and return combined results"""
    print(f"🚀 Starting unified search for: '{query}'")
    print("=" * 60)
    
    platforms = ["amazon", "flipkart", "meesho", "myntra"]
    results = {}
    all_products = []
    
    # Use ThreadPoolExecutor for parallel execution
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Submit all search tasks
        future_to_platform = {
            executor.submit(search_single_platform, platform, query, max_results): platform 
            for platform in platforms
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_platform):
            platform = future_to_platform[future]
            try:
                result = future.result()
                results[platform] = result
                
                # Extract products from successful searches
                if result["status"] == "success" and "data" in result and "products" in result["data"]:
                    products = result["data"]["products"]
                    all_products.extend(products)
                    
            except Exception as e:
                results[platform] = {
                    "platform": platform,
                    "status": "error",
                    "error": str(e),
                    "data": None
                }
    
    # Calculate summary statistics
    successful_searches = len([r for r in results.values() if r["status"] == "success"])
    failed_searches = len([r for r in results.values() if r["status"] == "error"])
    
    # Calculate price range
    prices = []
    brands = set()
    categories = set()
    
    for product in all_products:
        if "price" in product and product["price"]:
            try:
                # Clean price string and convert to float
                price_str = str(product["price"]).replace("₹", "").replace(",", "").replace(" ", "")
                if price_str.isdigit():
                    prices.append(float(price_str))
            except:
                pass
        
        if "brand" in product and product["brand"]:
            brands.add(product["brand"])
        
        if "category" in product and product["category"]:
            categories.add(product["category"])
    
    # Create combined result
    combined_result = {
        "query": query,
        "search_timestamp": datetime.now().isoformat(),
        "total_platforms": len(platforms),
        "successful_searches": successful_searches,
        "failed_searches": failed_searches,
        "platforms": results,
        "all_products": all_products,
        "summary": {
            "total_products": len(all_products),
            "platforms_with_data": [p for p, r in results.items() if r["status"] == "success" and "data" in r and "products" in r["data"]],
            "price_range": {
                "min": min(prices) if prices else None,
                "max": max(prices) if prices else None
            },
            "brands_found": list(brands),
            "categories_found": list(categories)
        }
    }
    
    return combined_result

def main():
    if len(sys.argv) < 2:
        print("Usage: python unified_search_all_platforms.py <search_query>")
        print("Example: python unified_search_all_platforms.py 'iphone 15'")
        return
    
    query = " ".join(sys.argv[1:])
    
    print("🔍 Unified E-commerce Search - All Platforms")
    print("=" * 60)
    print(f"Search Query: {query}")
    print(f"Platforms: Amazon, Flipkart, Meesho, Myntra")
    print()
    
    # Connect to MongoDB
    client, db, collection = connect_mongodb()
    if collection is None:
        print("❌ Cannot proceed without MongoDB connection")
        return
    
    try:
        # Run unified search
        result = unified_search_all_platforms(query)
        
        # Save to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = query.replace(' ', '_').replace('/', '_').replace('\\', '_')
        filename = f"unified_search_all_{safe_query}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"💾 Results saved to: {filename}")
        
        # Save to MongoDB
        save_to_mongodb(collection, result, query)
        
        # Print summary
        print("\n📊 Search Summary:")
        print(f"Query: {query}")
        print(f"Total platforms: {result.get('total_platforms', 0)}")
        print(f"Successful: {result.get('successful_searches', 0)}")
        print(f"Failed: {result.get('failed_searches', 0)}")
        print(f"Total products found: {result['summary'].get('total_products', 0)}")
        print(f"Platforms with data: {', '.join(result['summary'].get('platforms_with_data', []))}")
        
        if result['summary'].get('price_range', {}).get('min'):
            print(f"Price range: ₹{result['summary']['price_range']['min']:.0f} - ₹{result['summary']['price_range']['max']:.0f}")
        
        print("\n🎉 Unified search completed and stored in MongoDB!")
        
    except Exception as e:
        print(f"❌ Error during search: {e}")
    
    finally:
        if client:
            client.close()
            print("🔌 MongoDB connection closed")

if __name__ == "__main__":
    main()


