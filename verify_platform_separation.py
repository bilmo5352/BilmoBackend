#!/usr/bin/env python3
"""
Unified Platform Collection Verification Script
Checks if all platforms are properly stored with correct platform identifiers
"""

from pymongo import MongoClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB Configuration
MONGODB_URI = "mongodb+srv://hrithick:hrithick@bilmo.jmeclfh.mongodb.net/?retryWrites=true&w=majority&appName=bilmo"
DB_NAME = "scraper_db"

def verify_platform_separation():
    """Verify that platforms are properly stored with correct identifiers"""
    
    try:
        # Connect to MongoDB
        client = MongoClient(MONGODB_URI)
        db = client[DB_NAME]
        
        print("\n" + "="*70)
        print("🔍 UNIFIED COLLECTION VERIFICATION")
        print("="*70)
        
        # Check Unified Collection (amazon_homepage_deals - now stores ALL platforms)
        print("\n📦 UNIFIED COLLECTION (amazon_homepage_deals)")
        print("-" * 70)
        unified_coll = db['amazon_homepage_deals']
        
        total_docs = unified_coll.count_documents({})
        amazon_docs = unified_coll.count_documents({'platform': 'Amazon'})
        myntra_docs = unified_coll.count_documents({'platform': 'Myntra'})
        flipkart_docs = unified_coll.count_documents({'platform': 'Flipkart'})
        other_docs = total_docs - amazon_docs - myntra_docs - flipkart_docs
        
        print(f"Total documents: {total_docs}")
        print(f"Amazon docs: {amazon_docs} ✅")
        print(f"Myntra docs: {myntra_docs} ✅")
        print(f"Flipkart docs: {flipkart_docs} ✅")
        print(f"Other/untagged docs: {other_docs} {'⚠️ WARNING!' if other_docs > 0 else '✅'}")
        
        # Check for platform consistency in items
        print("\n🔗 Checking Platform Consistency in Items...")
        
        # Check Amazon items
        amazon_sample = unified_coll.find({'platform': 'Amazon'}).limit(5)
        amazon_url_issues = []
        for doc in amazon_sample:
            for section in doc.get('sections', []):
                for item in section.get('items', []):
                    link = item.get('link', '')
                    item_platform = item.get('platform', 'MISSING')
                    if link and 'amazon' not in link.lower():
                        amazon_url_issues.append(link)
                    if item_platform != 'Amazon':
                        amazon_url_issues.append(f"Wrong platform: {item_platform}")
        
        # Check Myntra items
        myntra_sample = unified_coll.find({'platform': 'Myntra'}).limit(5)
        myntra_issues = []
        for doc in myntra_sample:
            for section in doc.get('sections', []):
                for item in section.get('items', []):
                    item_platform = item.get('platform', 'MISSING')
                    if item_platform != 'Myntra':
                        myntra_issues.append(f"Wrong platform: {item_platform}")
        
        # Check Flipkart items
        flipkart_sample = unified_coll.find({'platform': 'Flipkart'}).limit(5)
        flipkart_issues = []
        for doc in flipkart_sample:
            for section in doc.get('sections', []):
                for item in section.get('items', []):
                    item_platform = item.get('platform', 'MISSING')
                    if item_platform != 'Flipkart':
                        flipkart_issues.append(f"Wrong platform: {item_platform}")
        
        if amazon_url_issues:
            print(f"⚠️ Amazon: Found {len(amazon_url_issues)} issues")
        else:
            print(f"✅ Amazon: All items properly tagged")
            
        if myntra_issues:
            print(f"⚠️ Myntra: Found {len(myntra_issues)} issues")
        else:
            print(f"✅ Myntra: All items properly tagged")
            
        if flipkart_issues:
            print(f"⚠️ Flipkart: Found {len(flipkart_issues)} issues")
        else:
            print(f"✅ Flipkart: All items properly tagged")
        
        # Check Old Unified Collection (should be empty or migrated)
        print("\n📦 OLD UNIFIED COLLECTION (unified_search_results)")
        print("-" * 70)
        old_unified_coll = db['unified_search_results']
        
        old_total_docs = old_unified_coll.count_documents({})
        old_myntra_docs = old_unified_coll.count_documents({'platform': 'Myntra'})
        old_flipkart_docs = old_unified_coll.count_documents({'platform': 'Flipkart'})
        old_amazon_docs = old_unified_coll.count_documents({'platform': 'Amazon'})
        
        print(f"Total documents: {old_total_docs} {'⚠️ Should be migrated to amazon_homepage_deals' if old_total_docs > 0 else '✅ Empty as expected'}")
        if old_total_docs > 0:
            print(f"  Myntra docs: {old_myntra_docs}")
            print(f"  Flipkart docs: {old_flipkart_docs}")
            print(f"  Amazon docs: {old_amazon_docs}")
        
        # Summary
        print("\n" + "="*70)
        print("📊 VERIFICATION SUMMARY")
        print("="*70)
        
        issues_found = []
        
        if other_docs > 0:
            issues_found.append(f"❌ {other_docs} documents without proper platform tag")
        
        if amazon_url_issues:
            issues_found.append(f"❌ {len(amazon_url_issues)} Amazon item issues found")
        
        if myntra_issues:
            issues_found.append(f"❌ {len(myntra_issues)} Myntra item issues found")
            
        if flipkart_issues:
            issues_found.append(f"❌ {len(flipkart_issues)} Flipkart item issues found")
        
        if issues_found:
            print("\n⚠️ ISSUES FOUND:")
            for issue in issues_found:
                print(f"   {issue}")
            print("\n💡 Recommendation: Check platform tagging in scrapers")
        else:
            print("\n✅ ALL CHECKS PASSED!")
            print("   - All platforms properly stored in unified collection")
            print("   - Amazon deals properly tagged with 'Amazon'")
            print("   - Myntra deals properly tagged with 'Myntra'")
            print("   - Flipkart deals properly tagged with 'Flipkart'")
            print("   - All items have correct platform tags")
        
        # Show platform distribution
        print("\n📈 PLATFORM DISTRIBUTION (Unified Collection)")
        print("-" * 70)
        print(f"Amazon documents:     {amazon_docs}")
        print(f"Myntra documents:     {myntra_docs}")
        print(f"Flipkart documents:   {flipkart_docs}")
        print(f"Other/untagged:       {other_docs}")
        print(f"─" * 70)
        print(f"Total in collection:  {total_docs}")
        
        print("\n" + "="*70)
        
        client.close()
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        print(f"\n❌ Error: {e}")

def migrate_old_data():
    """Migrate data from old unified_search_results to amazon_homepage_deals"""
    
    try:
        client = MongoClient(MONGODB_URI)
        db = client[DB_NAME]
        
        print("\n🔄 MIGRATING OLD DATA...")
        print("="*70)
        
        old_coll = db['unified_search_results']
        new_coll = db['amazon_homepage_deals']
        
        # Count documents to migrate
        myntra_count = old_coll.count_documents({'platform': 'Myntra'})
        flipkart_count = old_coll.count_documents({'platform': 'Flipkart'})
        
        print(f"Found {myntra_count} Myntra docs to migrate")
        print(f"Found {flipkart_count} Flipkart docs to migrate")
        
        if myntra_count > 0 or flipkart_count > 0:
            # Migrate Myntra docs
            myntra_docs = list(old_coll.find({'platform': 'Myntra'}))
            if myntra_docs:
                new_coll.insert_many(myntra_docs)
                print(f"✅ Migrated {len(myntra_docs)} Myntra documents")
            
            # Migrate Flipkart docs
            flipkart_docs = list(old_coll.find({'platform': 'Flipkart'}))
            if flipkart_docs:
                new_coll.insert_many(flipkart_docs)
                print(f"✅ Migrated {len(flipkart_docs)} Flipkart documents")
            
            print("\n💡 Old documents still in unified_search_results")
            print("   Run cleanup if you want to remove them")
        else:
            print("✅ No documents to migrate")
        
        client.close()
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    print("\n🔍 Starting unified collection verification...")
    verify_platform_separation()
    
    # Uncomment to run migration if old data exists
    # print("\n" + "="*70)
    # response = input("\n⚠️ Do you want to migrate old data to unified collection? (yes/no): ")
    # if response.lower() == 'yes':
    #     migrate_old_data()
    #     print("\n✅ Running verification again after migration...")
    #     verify_platform_separation()

