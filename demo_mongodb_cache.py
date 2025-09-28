#!/usr/bin/env python3
"""
Demo script to show MongoDB cache functionality
"""

import requests
import json
import time

def demo_cache_functionality():
    """Demonstrate MongoDB cache functionality"""
    print("🎯 MongoDB Cache Demo")
    print("=" * 50)
    
    base_url = "http://localhost:5001"
    
    # Test 1: First search (should create mock data)
    print("1️⃣ First search for 'socks' (should create mock data):")
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/search?query=socks", timeout=10)
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {data.get('success')}")
            print(f"   📊 Source: {data.get('source')}")
            print(f"   💬 Message: {data.get('message')}")
            print(f"   🔢 Total results: {data.get('total_results', 0)}")
            print(f"   ⏰ Response time: {end_time - start_time:.2f}s")
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "="*50)
    
    # Test 2: Second search (should get from cache)
    print("2️⃣ Second search for 'socks' (should get from MongoDB cache):")
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/search?query=socks", timeout=10)
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {data.get('success')}")
            print(f"   📊 Source: {data.get('source')}")
            print(f"   💬 Message: {data.get('message')}")
            print(f"   🔢 Total results: {data.get('total_results', 0)}")
            print(f"   ⏰ Response time: {end_time - start_time:.2f}s")
            print(f"   💾 Cached at: {data.get('cached_at')}")
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "="*50)
    
    # Test 3: Different query (should create new mock data)
    print("3️⃣ Search for 'shoes' (should create new mock data):")
    try:
        start_time = time.time()
        response = requests.get(f"{base_url}/search?query=shoes", timeout=10)
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {data.get('success')}")
            print(f"   📊 Source: {data.get('source')}")
            print(f"   💬 Message: {data.get('message')}")
            print(f"   🔢 Total results: {data.get('total_results', 0)}")
            print(f"   ⏰ Response time: {end_time - start_time:.2f}s")
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "="*50)
    
    # Test 4: Check MongoDB results
    print("4️⃣ Check all results in MongoDB:")
    try:
        response = requests.get(f"{base_url}/api/results", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   📊 Total cached searches: {data.get('count', 0)}")
            for i, result in enumerate(data.get('results', [])[:3], 1):
                print(f"   {i}. Query: '{result.get('query')}' - {result.get('total_results', 0)} results")
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "="*50)
    print("🎉 Demo completed!")
    print("\n📋 Summary:")
    print("✅ First search creates mock data and stores in MongoDB")
    print("✅ Second search retrieves from MongoDB cache (faster)")
    print("✅ Different query creates new mock data")
    print("✅ All results are stored in MongoDB for future use")
    print("\n💡 Benefits:")
    print("🚀 Faster responses for cached queries")
    print("💾 Persistent storage in MongoDB")
    print("🔄 Automatic caching of search results")
    print("📊 Clear indication of data source")

if __name__ == "__main__":
    demo_cache_functionality()


