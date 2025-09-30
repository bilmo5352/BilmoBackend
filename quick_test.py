#!/usr/bin/env python3
"""
Quick Verification Script - Tests scrapers with one query each
"""

def test_flipkart():
    print("🔍 Testing Flipkart scraper...")
    try:
        import subprocess
        result = subprocess.run(['python', 'flipkart_search.py', 'test', '--headless'], 
                              capture_output=True, text=True, timeout=120)
        if result.returncode == 0 and 'Found' in result.stdout:
            print("✅ Flipkart: WORKING")
            return True
        else:
            print("❌ Flipkart: FAILED")
            return False
    except Exception as e:
        print(f"❌ Flipkart: ERROR - {e}")
        return False

def test_meesho():
    print("🔍 Testing Meesho scraper...")
    try:
        import subprocess
        result = subprocess.run(['python', 'meesho_search.py', 'test', '--headless'], 
                              capture_output=True, text=True, timeout=120)
        if result.returncode == 0 and 'Found' in result.stdout:
            print("✅ Meesho: WORKING")
            return True
        else:
            print("❌ Meesho: FAILED")
            return False
    except Exception as e:
        print(f"❌ Meesho: ERROR - {e}")
        return False

if __name__ == "__main__":
    print("🚀 QUICK SCRAPER VERIFICATION")
    print("=" * 40)
    
    flipkart_ok = test_flipkart()
    meesho_ok = test_meesho()
    
    print("\n" + "=" * 40)
    if flipkart_ok and meesho_ok:
        print("🎉 ALL SCRAPERS ARE WORKING PERFECTLY!")
    else:
        print("⚠️ Some scrapers need attention")
    
    print("=" * 40)
