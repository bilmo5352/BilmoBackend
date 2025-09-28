#!/usr/bin/env python3
"""
Test the HTML frontend and API connection
"""

import webbrowser
import time
import requests
import json

def test_api_connection():
    """Test if the Flask API is responding"""
    try:
        response = requests.get("http://localhost:5000/", timeout=5)
        if response.status_code == 200:
            print("✅ Flask API is running and responding")
            return True
        else:
            print(f"❌ Flask API returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask API. Make sure it's running on port 5000")
        return False
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

def open_frontend():
    """Open the HTML frontend in browser"""
    try:
        # Open the HTML file directly
        webbrowser.open("file://" + __file__.replace("test_frontend.py", "index.html"))
        print("🌐 Opening HTML frontend in browser...")
        return True
    except Exception as e:
        print(f"❌ Error opening frontend: {e}")
        return False

def main():
    print("🚀 Testing E-commerce Scraper Frontend")
    print("=" * 50)
    
    # Test API connection
    print("\n📡 Testing Flask API connection...")
    api_ok = test_api_connection()
    
    if api_ok:
        print("\n✅ Flask API is ready!")
        print("📋 API Endpoints available:")
        print("   - GET /search?query=socks (search all platforms)")
        print("   - GET /search/amazon?query=socks (search Amazon only)")
        print("   - GET /search/flipkart?query=socks (search Flipkart only)")
        print("   - GET /search/meesho?query=socks (search Meesho only)")
        print("   - GET /search/myntra?query=socks (search Myntra only)")
        print("   - GET /api/results (get results from MongoDB)")
    else:
        print("\n❌ Flask API is not responding")
        print("Please make sure to run: python app.py")
        return
    
    # Open frontend
    print("\n🌐 Opening HTML frontend...")
    if open_frontend():
        print("✅ Frontend opened in browser")
        print("\n📋 How to use:")
        print("1. Enter a search term (e.g., 'socks', 'shoes', 'laptop')")
        print("2. Select a platform or search all platforms")
        print("3. Click 'Search' to search and store results in MongoDB")
        print("4. View results in the product grid")
        print("\n💡 Note: First search may take 30-60 seconds due to web scraping")
    else:
        print("❌ Could not open frontend automatically")
        print("Please manually open 'index.html' in your browser")

if __name__ == "__main__":
    main()


