#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Amazon Homepage Deals feature
"""

import sys
import io
import requests
import json
import time
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

API_URL = "http://localhost:5000"

def test_amazon_deals_endpoint():
    """Test the /amazon/deals endpoint"""
    print("\n" + "="*60)
    print("🧪 Testing Amazon Deals Endpoint")
    print("="*60)
    
    try:
        print("\n1️⃣ Making request to /amazon/deals...")
        start_time = time.time()
        
        response = requests.get(f"{API_URL}/amazon/deals")
        elapsed_time = time.time() - start_time
        
        print(f"   ⏱️  Response time: {elapsed_time:.2f}s")
        print(f"   📊 Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n2️⃣ Response structure:")
            print(f"   ✅ Success: {data.get('success', False)}")
            
            if data.get('success'):
                deals_data = data.get('data', {})
                print(f"\n3️⃣ Deals data:")
                print(f"   📦 Total deals: {deals_data.get('total_deals', 0)}")
                print(f"   🕐 Timestamp: {deals_data.get('timestamp', 'N/A')}")
                print(f"   📍 Source: {deals_data.get('source', 'N/A')}")
                
                deals = deals_data.get('deals', [])
                if deals:
                    print(f"\n4️⃣ Sample deals (first 3):")
                    for i, deal in enumerate(deals[:3], 1):
                        print(f"\n   Deal {i}:")
                        print(f"      Title: {deal.get('title', 'N/A')[:60]}...")
                        print(f"      Price: {deal.get('price', 'N/A')}")
                        print(f"      Discount: {deal.get('discount', 'N/A')}")
                        print(f"      Deal Type: {deal.get('deal_type', 'N/A')}")
                        print(f"      Link: {deal.get('link', 'N/A')[:50]}...")
                    
                    print(f"\n✅ Test PASSED: Successfully fetched {len(deals)} deals")
                else:
                    print(f"\n⚠️  No deals found in response")
            else:
                print(f"\n❌ API returned success=False")
                print(f"   Error: {data.get('error', 'Unknown error')}")
        else:
            print(f"\n❌ Test FAILED: Status code {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Test FAILED: Cannot connect to {API_URL}")
        print(f"   💡 Make sure the API is running: python smart_api.py")
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")

def test_api_status():
    """Test the API status endpoint"""
    print("\n" + "="*60)
    print("🧪 Testing API Status")
    print("="*60)
    
    try:
        response = requests.get(f"{API_URL}/status")
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ API Status: {data.get('api_status', 'unknown')}")
            print(f"   MongoDB: {data.get('mongodb_status', 'unknown')}")
            print(f"   Cache Expiry: {data.get('cache_expiry_hours', 'N/A')} hours")
        else:
            print(f"\n⚠️  Status endpoint returned: {response.status_code}")
    except Exception as e:
        print(f"\n❌ Status check failed: {e}")

def test_frontend_integration():
    """Test instructions for frontend"""
    print("\n" + "="*60)
    print("🖥️  Frontend Integration Test")
    print("="*60)
    
    print("\n📋 To test the frontend:")
    print("   1. Make sure smart_api.py is running:")
    print("      python smart_api.py")
    print("\n   2. Open the frontend:")
    print("      Open frontend/index.html in your browser")
    print("\n   3. Click the 'Amazon' platform button")
    print("      (without entering any search query)")
    print("\n   4. You should see Amazon homepage deals displayed")
    print("\n   5. Verify:")
    print("      ✓ Deals are displayed with images")
    print("      ✓ Prices and discounts are shown")
    print("      ✓ Links work correctly")
    print("      ✓ Cache status is displayed")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 AMAZON HOMEPAGE DEALS - TEST SUITE")
    print("="*60)
    
    # Test API status first
    test_api_status()
    
    # Test Amazon deals endpoint
    test_amazon_deals_endpoint()
    
    # Show frontend test instructions
    test_frontend_integration()
    
    print("\n" + "="*60)
    print("✅ Test Suite Complete")
    print("="*60 + "\n")
