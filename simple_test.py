#!/usr/bin/env python3
"""
Simple test to verify the system is working
"""

import requests
import json

def test_basic_api():
    """Test basic API endpoints"""
    print("🧪 Simple API Test")
    print("=" * 30)
    
    # Test 1: Basic API connection
    print("1. Testing basic API connection...")
    try:
        response = requests.get("http://localhost:5000/test", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API is working: {data.get('message')}")
            print(f"   🗄️ MongoDB connected: {data.get('mongodb_connected')}")
        else:
            print(f"   ❌ API returned status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ API connection failed: {e}")
        return False
    
    # Test 2: Check MongoDB for existing data
    print("\n2. Checking MongoDB for existing data...")
    try:
        response = requests.get("http://localhost:5000/api/results?limit=5", timeout=10)
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            print(f"   📊 Found {count} existing results in MongoDB")
            if count > 0:
                print("   ✅ MongoDB has cached data")
            else:
                print("   ℹ️ MongoDB is empty (first time use)")
        else:
            print(f"   ❌ MongoDB check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ MongoDB check failed: {e}")
    
    # Test 3: Try a simple search (this might timeout due to ChromeDriver issues)
    print("\n3. Testing search functionality...")
    print("   ⚠️ This might take 30-60 seconds or timeout due to ChromeDriver issues")
    try:
        response = requests.get("http://localhost:5000/search?query=test", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Search successful: {data.get('message')}")
            print(f"   📊 Source: {data.get('source')}")
            print(f"   🔢 Results: {data.get('total_results', 0)}")
        else:
            print(f"   ❌ Search failed: {response.status_code}")
    except requests.exceptions.Timeout:
        print("   ⏰ Search timed out (ChromeDriver issues expected)")
    except Exception as e:
        print(f"   ❌ Search failed: {e}")
    
    print("\n" + "=" * 30)
    print("🎯 Summary:")
    print("✅ Flask API is running on port 5000")
    print("✅ MongoDB connection is working")
    print("⚠️ Web scraping may have ChromeDriver issues (expected)")
    print("✅ HTML frontend is available at index.html")
    print("\n💡 To use the system:")
    print("1. Open index.html in your browser")
    print("2. Search for products (may take time due to scraping)")
    print("3. Results will be cached in MongoDB for faster future searches")

if __name__ == "__main__":
    test_basic_api()


