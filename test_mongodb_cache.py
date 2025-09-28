#!/usr/bin/env python3
"""
Test MongoDB cache functionality
"""

import requests
import json
import time

def test_search_with_cache():
    """Test search functionality with MongoDB caching"""
    print("🧪 Testing MongoDB Cache Functionality")
    print("=" * 50)
    
    query = "socks"
    url = f"http://localhost:5000/search?query={query}"
    
    print(f"🔍 Testing search for: {query}")
    print(f"URL: {url}")
    print()
    
    # First search - should scrape from web
    print("📡 First search (should scrape from web):")
    try:
        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {data.get('success')}")
            print(f"📊 Source: {data.get('source')}")
            print(f"💬 Message: {data.get('message')}")
            print(f"🔢 Total results: {data.get('total_results', 0)}")
            print(f"⏰ Response time: {response.elapsed.total_seconds():.2f}s")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    print("\n" + "="*50)
    
    # Second search - should get from MongoDB cache
    print("📡 Second search (should get from MongoDB cache):")
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {data.get('success')}")
            print(f"📊 Source: {data.get('source')}")
            print(f"💬 Message: {data.get('message')}")
            print(f"🔢 Total results: {data.get('total_results', 0)}")
            print(f"⏰ Response time: {response.elapsed.total_seconds():.2f}s")
            
            if data.get('cached_at'):
                print(f"💾 Cached at: {data.get('cached_at')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "="*50)
    
    # Test different query - should scrape from web
    print("📡 Testing different query (should scrape from web):")
    query2 = "shoes"
    url2 = f"http://localhost:5000/search?query={query2}"
    
    try:
        response = requests.get(url2, timeout=60)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {data.get('success')}")
            print(f"📊 Source: {data.get('source')}")
            print(f"💬 Message: {data.get('message')}")
            print(f"🔢 Total results: {data.get('total_results', 0)}")
            print(f"⏰ Response time: {response.elapsed.total_seconds():.2f}s")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_api_connection():
    """Test basic API connection"""
    print("🔌 Testing API Connection")
    print("=" * 30)
    
    try:
        response = requests.get("http://localhost:5000/test", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Status: {data.get('success')}")
            print(f"💬 Message: {data.get('message')}")
            print(f"🗄️ MongoDB Connected: {data.get('mongodb_connected')}")
            return True
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False

def main():
    print("🚀 MongoDB Cache Test Suite")
    print("=" * 60)
    
    # Test API connection first
    if not test_api_connection():
        print("\n❌ API connection failed. Please make sure Flask API is running.")
        return
    
    print("\n" + "="*60)
    
    # Test search with caching
    test_search_with_cache()
    
    print("\n🎉 Test completed!")
    print("\n📋 Summary:")
    print("1. First search should show 'web_scraping' source")
    print("2. Second search should show 'mongodb_cache' source")
    print("3. Different query should show 'web_scraping' source again")
    print("4. Cached results should be much faster")

if __name__ == "__main__":
    main()


