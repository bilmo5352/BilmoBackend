#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Amazon Deals Button Functionality
Tests the new deals button and collection endpoints
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

# API Configuration
API_BASE_URL = "http://localhost:5000"

def test_deals_endpoints():
    """Test all Amazon deals related endpoints"""
    print(f"\n{'='*60}")
    print(f"🛒 TESTING AMAZON DEALS BUTTON FUNCTIONALITY")
    print(f"{'='*60}")
    
    endpoints = [
        {
            "name": "Get Amazon Deals",
            "url": f"{API_BASE_URL}/amazon/deals",
            "description": "Main endpoint for deals button"
        },
        {
            "name": "View Collection",
            "url": f"{API_BASE_URL}/amazon/deals/view",
            "description": "HTML viewer for collection"
        },
        {
            "name": "Get Collection Data",
            "url": f"{API_BASE_URL}/amazon/deals/collection",
            "description": "JSON data for collection"
        },
        {
            "name": "Get Sections Only",
            "url": f"{API_BASE_URL}/amazon/deals/sections",
            "description": "Only section documents"
        }
    ]
    
    results = {}
    
    for endpoint in endpoints:
        print(f"\n🔍 Testing: {endpoint['name']}")
        print(f"   URL: {endpoint['url']}")
        print(f"   Description: {endpoint['description']}")
        
        try:
            start_time = time.time()
            response = requests.get(endpoint['url'], timeout=30)
            end_time = time.time()
            
            response_time = round(end_time - start_time, 2)
            
            if response.status_code == 200:
                print(f"   ✅ Status: {response.status_code}")
                print(f"   ⏱️ Response Time: {response_time}s")
                
                if endpoint['name'] == "View Collection":
                    # HTML response
                    content_length = len(response.text)
                    print(f"   📄 Content Length: {content_length} characters")
                    print(f"   🌐 Content Type: HTML")
                else:
                    # JSON response
                    try:
                        data = response.json()
                        print(f"   📊 Success: {data.get('success', 'Unknown')}")
                        
                        if 'data' in data:
                            sections = data['data'].get('sections', [])
                            total_items = data['data'].get('total_items', 0)
                            print(f"   📦 Sections: {len(sections)}")
                            print(f"   🛍️ Total Items: {total_items}")
                        
                        if 'documents' in data:
                            print(f"   📄 Documents: {len(data['documents'])}")
                        
                        if 'sections' in data:
                            print(f"   📂 Sections: {len(data['sections'])}")
                            
                    except json.JSONDecodeError:
                        print(f"   ⚠️ Response is not valid JSON")
                
                results[endpoint['name']] = {
                    "status": "success",
                    "response_time": response_time,
                    "status_code": response.status_code
                }
                
            else:
                print(f"   ❌ Status: {response.status_code}")
                print(f"   ⚠️ Error: {response.text[:100]}...")
                
                results[endpoint['name']] = {
                    "status": "error",
                    "status_code": response.status_code,
                    "error": response.text[:100]
                }
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout after 30 seconds")
            results[endpoint['name']] = {"status": "timeout"}
            
        except requests.exceptions.ConnectionError:
            print(f"   🔌 Connection Error - Is the API running?")
            results[endpoint['name']] = {"status": "connection_error"}
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            results[endpoint['name']] = {"status": "error", "error": str(e)}
    
    return results

def test_frontend_integration():
    """Test frontend integration points"""
    print(f"\n{'='*60}")
    print(f"🌐 FRONTEND INTEGRATION TEST")
    print(f"{'='*60}")
    
    print(f"\n📁 Frontend Files:")
    
    files_to_check = [
        "frontend/index.html",
        "frontend/style.css", 
        "frontend/script.js"
    ]
    
    for file_path in files_to_check:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if file_path.endswith('.html'):
                if 'dealsButton' in content and 'deals-section' in content:
                    print(f"   ✅ {file_path}: Deals button HTML found")
                else:
                    print(f"   ❌ {file_path}: Deals button HTML missing")
                    
            elif file_path.endswith('.css'):
                if 'deals-button' in content and 'deals-section' in content:
                    print(f"   ✅ {file_path}: Deals button styles found")
                else:
                    print(f"   ❌ {file_path}: Deals button styles missing")
                    
            elif file_path.endswith('.js'):
                if 'loadAmazonDeals' in content and 'dealsButton' in content:
                    print(f"   ✅ {file_path}: Deals button JavaScript found")
                else:
                    print(f"   ❌ {file_path}: Deals button JavaScript missing")
                    
        except FileNotFoundError:
            print(f"   ❌ {file_path}: File not found")
        except Exception as e:
            print(f"   ⚠️ {file_path}: Error reading file - {e}")

def show_usage_instructions():
    """Show how to use the deals button"""
    print(f"\n{'='*60}")
    print(f"📖 HOW TO USE THE DEALS BUTTON")
    print(f"{'='*60}")
    
    print(f"\n🚀 Steps to Test:")
    print(f"   1. Start the API:")
    print(f"      python smart_api.py")
    print(f"")
    print(f"   2. Open the frontend:")
    print(f"      Open frontend/index.html in your browser")
    print(f"")
    print(f"   3. Click the Deals Button:")
    print(f"      Look for the orange 'View Amazon Deals' button")
    print(f"      Click it to scrape Amazon homepage")
    print(f"")
    print(f"   4. View Results:")
    print(f"      Results will show grouped by sections")
    print(f"      Each section shows products with prices")
    print(f"")
    print(f"   5. View Collection:")
    print(f"      Visit: http://localhost:5000/amazon/deals/view")
    print(f"      Browse MongoDB Atlas: https://cloud.mongodb.com/")
    
    print(f"\n🎯 Expected Behavior:")
    print(f"   • Button shows loading animation")
    print(f"   • Scrapes entire Amazon homepage")
    print(f"   • Groups products by sections")
    print(f"   • Shows 20-30 sections with 200-400 products")
    print(f"   • Saves data to MongoDB collection")
    print(f"   • Displays success message")

def main():
    """Main test function"""
    print(f"🛒 Amazon Deals Button Test Suite")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Test API endpoints
    api_results = test_deals_endpoints()
    
    # Test frontend integration
    test_frontend_integration()
    
    # Show usage instructions
    show_usage_instructions()
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    successful_tests = sum(1 for result in api_results.values() if result.get('status') == 'success')
    total_tests = len(api_results)
    
    print(f"\nAPI Endpoints: {successful_tests}/{total_tests} successful")
    
    if successful_tests == total_tests:
        print(f"🎉 All tests passed! Deals button is ready to use.")
    else:
        print(f"⚠️ Some tests failed. Check API status and try again.")
    
    print(f"\n🔗 Quick Links:")
    print(f"   Frontend: file:///E:/bilmo-main/frontend/index.html")
    print(f"   API Deals: http://localhost:5000/amazon/deals")
    print(f"   Collection View: http://localhost:5000/amazon/deals/view")
    print(f"   MongoDB Atlas: https://cloud.mongodb.com/")

if __name__ == "__main__":
    main()
