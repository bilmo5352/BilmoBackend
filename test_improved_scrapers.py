#!/usr/bin/env python3
"""
Test script to verify all scrapers work like Amazon
"""

import subprocess
import json
import time
import os

def test_scraper(scraper_name, query, expected_fields):
    """Test a single scraper and verify it extracts expected fields"""
    print(f"\n{'='*60}")
    print(f"TESTING {scraper_name.upper()} SCRAPER")
    print(f"{'='*60}")
    
    try:
        # Run the scraper
        cmd = f"python {scraper_name}_search.py \"{query}\" --headless"
        print(f"Running: {cmd}")
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"❌ {scraper_name} failed with error:")
            print(result.stderr)
            return False
        
        print(f"✅ {scraper_name} completed successfully")
        
        # Check for detailed products JSON file
        detailed_file = f"{scraper_name}_detailed_products_{query.replace(' ', '_')}.json"
        if os.path.exists(detailed_file):
            with open(detailed_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"📊 Found {data.get('total_products', 0)} detailed products")
            
            if data.get('products'):
                product = data['products'][0]  # Check first product
                
                print(f"\n📋 EXTRACTED DATA QUALITY CHECK:")
                print(f"{'='*40}")
                
                missing_fields = []
                for field in expected_fields:
                    if field in product and product[field]:
                        print(f"✅ {field}: {str(product[field])[:50]}...")
                    else:
                        print(f"❌ {field}: Missing or empty")
                        missing_fields.append(field)
                
                # Check image quality
                images = product.get('images', [])
                if images:
                    print(f"✅ Images: {len(images)} images found")
                    if images[0].get('url'):
                        print(f"✅ First image URL: {images[0]['url'][:50]}...")
                    else:
                        print(f"❌ Images: No valid image URLs")
                        missing_fields.append('images')
                else:
                    print(f"❌ Images: No images found")
                    missing_fields.append('images')
                
                # Check specifications
                specs = product.get('specifications', {})
                if specs:
                    print(f"✅ Specifications: {len(specs)} specs found")
                else:
                    print(f"❌ Specifications: No specifications found")
                    missing_fields.append('specifications')
                
                success_rate = ((len(expected_fields) - len(missing_fields)) / len(expected_fields)) * 100
                print(f"\n📈 SUCCESS RATE: {success_rate:.1f}%")
                
                if success_rate >= 80:
                    print(f"🎉 {scraper_name} is working well!")
                    return True
                else:
                    print(f"⚠️ {scraper_name} needs improvement")
                    return False
            else:
                print(f"❌ No products found in detailed data")
                return False
        else:
            print(f"❌ Detailed products file not found: {detailed_file}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"❌ {scraper_name} timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ {scraper_name} failed with exception: {e}")
        return False

def main():
    """Test all scrapers"""
    print("🚀 TESTING ALL IMPROVED SCRAPERS")
    print("=" * 60)
    
    # Define expected fields that should be extracted (like Amazon)
    expected_fields = [
        'name',
        'price', 
        'brand',
        'category',
        'rating',
        'reviews_count',
        'availability',
        'link',
        'images',
        'specifications'
    ]
    
    # Test queries for each platform
    test_cases = [
        ("amazon", "iphone 15", expected_fields),
        ("flipkart", "iphone 14", expected_fields),
        ("meesho", "mobile phones", expected_fields),
        ("myntra", "nike shoes", expected_fields)
    ]
    
    results = {}
    
    for scraper, query, fields in test_cases:
        print(f"\n⏳ Testing {scraper} with query: '{query}'")
        success = test_scraper(scraper, query, fields)
        results[scraper] = success
        time.sleep(2)  # Brief pause between tests
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 FINAL RESULTS SUMMARY")
    print(f"{'='*60}")
    
    passed = 0
    total = len(results)
    
    for scraper, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{scraper.upper():<12}: {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 OVERALL SUCCESS RATE: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL SCRAPERS ARE NOW WORKING LIKE AMAZON!")
    elif passed >= total * 0.75:
        print("👍 MOST SCRAPERS ARE WORKING WELL!")
    else:
        print("⚠️ SOME SCRAPERS STILL NEED IMPROVEMENT")

if __name__ == "__main__":
    main()
