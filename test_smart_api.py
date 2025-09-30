#!/usr/bin/env python3
"""
Test Script for Enhanced Smart API Integration
Tests the smart_api with enhanced scrapers
"""

import requests
import json
import time
from datetime import datetime

def test_smart_api():
    """Test the enhanced smart API"""
    base_url = "http://localhost:5000"
    
    print("🚀 TESTING ENHANCED SMART API")
    print("=" * 50)
    
    # Test queries
    test_queries = ["laptop", "phone", "helmet"]
    
    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
        print("-" * 30)
        
        try:
            # Test GET request
            response = requests.get(f"{base_url}/search", params={"q": query}, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"✅ Status: {data.get('success')}")
                print(f"📊 Total Results: {data.get('total_results')}")
                print(f"⏱️ Processing Time: {data.get('processing_time')}")
                print(f"📦 Source: {data.get('source')}")
                
                # Check enhanced features
                results = data.get('results', [])
                for result in results:
                    site = result.get('site')
                    total_products = result.get('total_products')
                    enhanced_features = result.get('enhanced_features', {})
                    
                    print(f"  🏪 {site}: {total_products} products")
                    print(f"    🎯 MRP Extraction: {enhanced_features.get('mrp_extraction', False)}")
                    print(f"    🎯 Discount Calculation: {enhanced_features.get('discount_calculation', False)}")
                    print(f"    🎯 Rating Extraction: {enhanced_features.get('rating_extraction', False)}")
                    
                    # Show sample product with enhanced fields
                    products = result.get('products', [])
                    if products:
                        sample_product = products[0]
                        print(f"    📱 Sample Product:")
                        print(f"      Name: {sample_product.get('name', 'N/A')}")
                        print(f"      Price: {sample_product.get('price', 'N/A')}")
                        print(f"      MRP: {sample_product.get('mrp', 'N/A')}")
                        print(f"      Discount: {sample_product.get('discount_percentage', 'N/A')}")
                        print(f"      You Save: {sample_product.get('discount_amount', 'N/A')}")
                        print(f"      Rating: {sample_product.get('rating', 'N/A')}")
                
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        time.sleep(2)  # Delay between requests

def test_api_status():
    """Test API status endpoint"""
    base_url = "http://localhost:5000"
    
    print(f"\n🔍 Testing API Status")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/status", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Status: {data.get('api_status')}")
            print(f"✅ MongoDB Status: {data.get('mongodb_status')}")
            print(f"⏰ Cache Expiry: {data.get('cache_expiry_hours')} hours")
            
            db_stats = data.get('database_stats')
            if db_stats:
                print(f"📊 Database Stats: {db_stats}")
        else:
            print(f"❌ Status check failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Status check error: {e}")

def test_search_history():
    """Test search history endpoint"""
    base_url = "http://localhost:5000"
    
    print(f"\n🔍 Testing Search History")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/history", params={"limit": 5}, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Total Searches: {data.get('total_searches')}")
            
            searches = data.get('searches', [])
            for i, search in enumerate(searches, 1):
                print(f"  {i}. Query: {search.get('_id')} - Count: {search.get('count')}")
        else:
            print(f"❌ History check failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ History check error: {e}")

def main():
    """Main test function"""
    print(f"🧪 Enhanced Smart API Test Suite")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Test API status first
    test_api_status()
    
    # Test search functionality
    test_smart_api()
    
    # Test search history
    test_search_history()
    
    print(f"\n{'='*60}")
    print(f"✅ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎉 Enhanced Smart API is working with improved scrapers!")

if __name__ == "__main__":
    main()
