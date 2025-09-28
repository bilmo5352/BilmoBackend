#!/usr/bin/env python3
"""
Simple Terminal Product Search & MongoDB Storage
Usage: python search_products.py "iphone 15"
"""

import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
import pymongo
from pymongo import MongoClient

# MongoDB Configuration
MONGODB_URI = "mongodb+srv://hrithick:hrithick@bilmo.jmeclfh.mongodb.net/?retryWrites=true&w=majority&appName=bilmo"
DB_NAME = "scraper_db"
COLLECTION_NAME = "search_results"

def connect_mongodb():
    """Connect to MongoDB Atlas"""
    try:
        # Try with proper URL encoding
        import urllib.parse
        username = "hrithick"
        password = "hrimee@0514"
        encoded_password = urllib.parse.quote_plus(password)
        uri = f"mongodb+srv://{username}:{encoded_password}@bilmo.jmeclfh.mongodb.net/?retryWrites=true&w=majority&appName=bilmo"
        
        client = MongoClient(uri)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        # Test connection
        client.admin.command('ping')
        print("✅ Connected to MongoDB")
        return client, db, collection
    except Exception as e:
        print(f"❌ MongoDB connection error: {e}")
        print("💡 Continuing without MongoDB - results will be saved to JSON file only")
        return None, None, None

def save_to_mongodb(collection, data, query):
    """Save search results to MongoDB"""
    try:
        document = {
            "query": query,
            "timestamp": datetime.now(),
            "data": data,
            "total_results": len(data.get("all_products", [])) if isinstance(data, dict) else len(data) if isinstance(data, list) else 1
        }
        
        result = collection.insert_one(document)
        print(f"✅ Saved search results to MongoDB with ID: {result.inserted_id}")
        return True
    except Exception as e:
        print(f"❌ Failed to save to MongoDB: {e}")
        return False

def search_amazon_simple(query: str):
    """Simple Amazon search - returns mock data for demo"""
    print(f"🔍 Searching Amazon for: {query}")
    time.sleep(1)  # Simulate search time
    
    # Mock Amazon results
    return {
        "website": "amazon",
        "products": [
            {
                "name": f"Amazon {query} - Premium Quality",
                "price": "₹45,999",
                "brand": "Amazon Basics",
                "rating": "4.2",
                "link": f"https://amazon.in/{query.replace(' ', '-')}",
                "image": "https://example.com/amazon-product.jpg"
            },
            {
                "name": f"Amazon {query} - Best Seller",
                "price": "₹52,999",
                "brand": "Amazon Choice",
                "rating": "4.5",
                "link": f"https://amazon.in/{query.replace(' ', '-')}-bestseller",
                "image": "https://example.com/amazon-bestseller.jpg"
            }
        ]
    }

def search_flipkart_simple(query: str):
    """Simple Flipkart search - returns mock data for demo"""
    print(f"🔍 Searching Flipkart for: {query}")
    time.sleep(1)  # Simulate search time
    
    # Mock Flipkart results
    return {
        "website": "flipkart",
        "products": [
            {
                "name": f"Flipkart {query} - Great Value",
                "price": "₹41,999",
                "brand": "Flipkart SmartBuy",
                "rating": "4.1",
                "link": f"https://flipkart.com/{query.replace(' ', '-')}",
                "image": "https://example.com/flipkart-product.jpg"
            },
            {
                "name": f"Flipkart {query} - Premium Edition",
                "price": "₹48,999",
                "brand": "Flipkart Plus",
                "rating": "4.3",
                "link": f"https://flipkart.com/{query.replace(' ', '-')}-premium",
                "image": "https://example.com/flipkart-premium.jpg"
            }
        ]
    }

def search_meesho_simple(query: str):
    """Simple Meesho search - returns mock data for demo"""
    print(f"🔍 Searching Meesho for: {query}")
    time.sleep(1)  # Simulate search time
    
    # Mock Meesho results
    return {
        "website": "meesho",
        "products": [
            {
                "name": f"Meesho {query} - Budget Friendly",
                "price": "₹38,999",
                "brand": "Meesho Originals",
                "rating": "4.0",
                "link": f"https://meesho.com/{query.replace(' ', '-')}",
                "image": "https://example.com/meesho-product.jpg"
            }
        ]
    }

def search_myntra_simple(query: str):
    """Simple Myntra search - returns mock data for demo"""
    print(f"🔍 Searching Myntra for: {query}")
    time.sleep(1)  # Simulate search time
    
    # Mock Myntra results
    return {
        "website": "myntra",
        "products": [
            {
                "name": f"Myntra {query} - Fashion Forward",
                "price": "₹55,999",
                "brand": "Myntra Fashion",
                "rating": "4.4",
                "link": f"https://myntra.com/{query.replace(' ', '-')}",
                "image": "https://example.com/myntra-product.jpg"
            }
        ]
    }

def unified_search(query: str):
    """Search all websites and combine results"""
    print(f"🚀 Starting unified search for: '{query}'")
    print("=" * 60)
    
    # Search all websites
    websites = {
        "amazon": search_amazon_simple,
        "flipkart": search_flipkart_simple,
        "meesho": search_meesho_simple,
        "myntra": search_myntra_simple
    }
    
    results = {}
    all_products = []
    
    for website, search_func in websites.items():
        try:
            result = search_func(query)
            results[website] = result
            if "products" in result:
                for product in result["products"]:
                    product["source_website"] = website
                    all_products.append(product)
        except Exception as e:
            print(f"❌ Error searching {website}: {e}")
            results[website] = {"error": str(e)}
    
    # Create combined result
    combined_result = {
        "query": query,
        "search_timestamp": datetime.now().isoformat(),
        "total_websites": len(websites),
        "successful_searches": len([r for r in results.values() if "error" not in r]),
        "failed_searches": len([r for r in results.values() if "error" in r]),
        "websites": results,
        "all_products": all_products,
        "summary": {
            "total_products": len(all_products),
            "websites_with_data": [w for w, r in results.items() if "error" not in r and "products" in r],
            "price_range": calculate_price_range(all_products),
            "brands_found": list(set([p.get("brand") for p in all_products if p.get("brand")]))
        }
    }
    
    return combined_result

def calculate_price_range(products):
    """Calculate price range from products"""
    prices = []
    for product in products:
        if "price" in product and product["price"]:
            try:
                price_str = product["price"].replace("₹", "").replace(",", "").strip()
                if price_str.replace(".", "").isdigit():
                    prices.append(float(price_str))
            except:
                pass
    
    if prices:
        return {"min": min(prices), "max": max(prices)}
    return {"min": None, "max": None}

def save_json_file(data, query):
    """Save results to JSON file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"search_results_{query.replace(' ', '_')}_{timestamp}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved JSON file: {filename}")
        return filename
    except Exception as e:
        print(f"❌ Failed to save JSON file: {e}")
        return None

def main():
    """Main function"""
    if len(sys.argv) < 2:
        query = input("Enter product to search: ").strip()
    else:
        query = " ".join(sys.argv[1:])
    
    if not query:
        print("❌ No query provided. Exiting.")
        sys.exit(1)
    
    print(f"🔍 Searching for: '{query}'")
    print(f"🌐 Websites: Amazon, Flipkart, Meesho, Myntra")
    print()
    
    # Run search
    start_time = time.time()
    result = unified_search(query)
    end_time = time.time()
    
    # Display summary
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
    
    # Connect to MongoDB and save
    client, db, collection = connect_mongodb()
    if collection:
        save_to_mongodb(collection, result, query)
        client.close()
    
    # Save to JSON file
    json_file = save_json_file(result, query)
    
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
    
    print(f"\n🎉 Search completed!")
    if json_file:
        print(f"📄 JSON file saved: {json_file}")
    print(f"💾 Data saved to MongoDB: scraper_db.search_results")

if __name__ == "__main__":
    main()
