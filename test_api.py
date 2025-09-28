#!/usr/bin/env python3
"""
Test script to verify the Flask API is working
"""
import requests
import json
import time

def test_api():
    """Test the Flask API endpoints"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Flask API...")
    
    # Test 1: Basic connectivity
    try:
        response = requests.get(f"{base_url}/test", timeout=10)
        print(f"✅ Test endpoint: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Test endpoint failed: {e}")
        return False
    
    # Test 2: Search endpoint
    try:
        print("\n🔍 Testing search endpoint...")
        response = requests.get(f"{base_url}/search?query=test", timeout=30)
        print(f"✅ Search endpoint: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('success')}")
            print(f"   Query: {data.get('query')}")
            print(f"   Source: {data.get('source')}")
            print(f"   Total results: {data.get('total_results')}")
            print(f"   Message: {data.get('message')}")
            
            if data.get('results'):
                print(f"   Results count: {len(data.get('results', []))}")
                for i, result in enumerate(data.get('results', [])[:2]):  # Show first 2
                    print(f"     {i+1}. {result.get('site')}: {len(result.get('products', []))} products")
        else:
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Search endpoint failed: {e}")
        return False
    
    # Test 3: MongoDB results endpoint
    try:
        print("\n📋 Testing MongoDB results endpoint...")
        response = requests.get(f"{base_url}/api/results", timeout=10)
        print(f"✅ Results endpoint: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Total stored results: {len(data.get('results', []))}")
        else:
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Results endpoint failed: {e}")
    
    print("\n🎉 API testing completed!")
    return True

if __name__ == "__main__":
    test_api()