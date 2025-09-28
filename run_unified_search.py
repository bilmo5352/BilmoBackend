#!/usr/bin/env python3
"""
Run Unified Search Across All 4 Platforms and Store in MongoDB
This script will search Amazon, Flipkart, Meesho, and Myntra simultaneously
"""

import sys
import json
import time
from datetime import datetime
from pymongo import MongoClient

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
            "search_type": "unified_search"
        }
        
        result = collection.insert_one(document)
        print(f"✅ Saved unified search results to MongoDB with ID: {result.inserted_id}")
        return True
    except Exception as e:
        print(f"❌ Failed to save to MongoDB: {e}")
        return False

def run_unified_search(query):
    """Run unified search across all platforms"""
    print(f"🚀 Starting unified search for: '{query}'")
    print("=" * 60)
    
    # Import the unified search function
    try:
        from unified_search import unified_search
        result = unified_search(query, headless=True)
        
        print(f"✅ Unified search completed!")
        print(f"📊 Total websites searched: {result.get('total_websites', 0)}")
        print(f"✅ Successful searches: {result.get('successful_searches', 0)}")
        print(f"❌ Failed searches: {result.get('failed_searches', 0)}")
        
        return result
        
    except ImportError:
        print("❌ Could not import unified_search. Trying alternative method...")
        return run_alternative_search(query)

def run_alternative_search(query):
    """Alternative search method using individual scrapers"""
    print("🔄 Running alternative search method...")
    
    results = {}
    websites = ["amazon", "flipkart", "meesho", "myntra"]
    
    for website in websites:
        try:
            print(f"🔍 Searching {website}...")
            
            if website == "amazon":
                from amazon_search import search_amazon
                result = search_amazon(query, max_results=8)
            elif website == "flipkart":
                from flipkart_search import search_flipkart
                result = search_flipkart(query, max_results=8)
            elif website == "meesho":
                from meesho_search import search_meesho
                result = search_meesho(query, max_results=8)
            elif website == "myntra":
                from myntra_search import search_myntra
                result = search_myntra(query, max_results=8)
            
            results[website] = result
            print(f"✅ {website} search completed")
            time.sleep(2)  # Add delay between searches
            
        except Exception as e:
            print(f"❌ {website} search failed: {e}")
            results[website] = {"error": str(e)}
    
    # Create combined result
    combined_result = {
        "query": query,
        "search_timestamp": datetime.now().isoformat(),
        "total_websites": len(websites),
        "successful_searches": len([r for r in results.values() if "error" not in r]),
        "failed_searches": len([r for r in results.values() if "error" in r]),
        "websites": results,
        "summary": {
            "total_products": sum(len(r.get("products", [])) for r in results.values() if "error" not in r),
            "websites_with_data": [w for w, r in results.items() if "error" not in r and "products" in r]
        }
    }
    
    return combined_result

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_unified_search.py <search_query>")
        print("Example: python run_unified_search.py 'iphone 15'")
        return
    
    query = " ".join(sys.argv[1:])
    
    print("🔍 Unified E-commerce Search")
    print("=" * 50)
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
        result = run_unified_search(query)
        
        # Save to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = query.replace(' ', '_').replace('/', '_').replace('\\', '_')
        filename = f"unified_search_{safe_query}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"💾 Results saved to: {filename}")
        
        # Save to MongoDB
        save_to_mongodb(collection, result, query)
        
        # Print summary
        print("\n📊 Search Summary:")
        print(f"Query: {query}")
        print(f"Total websites: {result.get('total_websites', 0)}")
        print(f"Successful: {result.get('successful_searches', 0)}")
        print(f"Failed: {result.get('failed_searches', 0)}")
        
        if 'summary' in result:
            print(f"Total products found: {result['summary'].get('total_products', 0)}")
            print(f"Websites with data: {', '.join(result['summary'].get('websites_with_data', []))}")
        
        print("\n🎉 Unified search completed and stored in MongoDB!")
        
    except Exception as e:
        print(f"❌ Error during search: {e}")
    
    finally:
        if client:
            client.close()
            print("🔌 MongoDB connection closed")

if __name__ == "__main__":
    main()
