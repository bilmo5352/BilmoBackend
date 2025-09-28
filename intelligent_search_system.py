#!/usr/bin/env python3
"""
Intelligent Search System with MongoDB Caching
Workflow: Search for product → Check MongoDB → Not found → Web scraping → Save to MongoDB
"""

import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from unified_mongodb_manager import UnifiedMongoDBManager
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntelligentSearchSystem:
    def __init__(self, cache_expiry_hours=24):
        """
        Initialize the intelligent search system
        
        Args:
            cache_expiry_hours: How many hours before cached results expire
        """
        self.mongodb_manager = UnifiedMongoDBManager()
        self.cache_expiry_hours = cache_expiry_hours
        
        # Import scrapers
        try:
            from amazon_search import search_amazon
            from flipkart_search import search_flipkart
            from meesho_search import search_meesho  
            from myntra_search import search_myntra
            
            self.scrapers = {
                'Amazon': search_amazon,
                'Flipkart': search_flipkart,
                'Meesho': search_meesho,
                'Myntra': search_myntra
            }
            logger.info("✅ Successfully imported all scrapers")
        except ImportError as e:
            logger.error(f"❌ Failed to import scrapers: {e}")
            self.scrapers = {}
    
    def search_in_mongodb(self, query: str) -> Optional[Dict]:
        """
        Search for cached results in MongoDB
        
        Args:
            query: Search query
            
        Returns:
            Cached results if found and not expired, None otherwise
        """
        try:
            if not self.mongodb_manager.connect():
                logger.error("❌ Failed to connect to MongoDB")
                return None
            
            # Search for recent results
            results = self.mongodb_manager.get_search_results(query=query, limit=1)
            
            if not results:
                logger.info(f"🔍 No cached results found for query: '{query}'")
                return None
            
            latest_result = results[0]
            
            # Check if result is still fresh
            search_time = latest_result.get('search_timestamp')
            if search_time:
                time_diff = datetime.now() - search_time
                if time_diff < timedelta(hours=self.cache_expiry_hours):
                    logger.info(f"✅ Found fresh cached results for query: '{query}' (cached {time_diff} ago)")
                    # Remove MongoDB-specific fields that can't be JSON serialized
                    if '_id' in latest_result:
                        del latest_result['_id']
                    return latest_result
                else:
                    logger.info(f"⏰ Cached results for query: '{query}' are expired (cached {time_diff} ago)")
                    return None
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error searching MongoDB: {e}")
            return None
    
    def scrape_all_platforms(self, query: str) -> Dict:
        """
        Scrape all platforms for the given query
        
        Args:
            query: Search query
            
        Returns:
            Unified search results in the required format
        """
        logger.info(f"🕷️ Starting web scraping for query: '{query}'")
        
        results = []
        total_products = 0
        
        def scrape_platform(platform_name, scraper_func):
            """Helper function to scrape a single platform"""
            try:
                logger.info(f"🔍 Scraping {platform_name} for: '{query}'")
                
                # Call scraper with appropriate parameters
                if platform_name == "Myntra":
                    products = scraper_func(query, headless=True)
                elif platform_name in ["Amazon", "Flipkart"]:
                    products = scraper_func(query, headless=True, max_results=8)
                else:  # Meesho
                    products = scraper_func(query, headless=True)
                
                logger.info(f"🔍 {platform_name} returned: {type(products)} - {str(products)[:200]}...")
                
                if products and isinstance(products, dict):
                    # Handle different return formats
                    if 'basic_products' in products:
                        # Handle Meesho's structure with basic_products and detailed_products
                        platform_result = {
                            "site": platform_name,
                            "query": query,
                            "total_products": len(products.get('basic_products', [])),
                            "basic_products": products.get('basic_products', []),
                            "detailed_products": products.get('detailed_products', [])
                        }
                    elif 'products' in products:
                        # Standard format with products key
                        platform_result = {
                            "site": platform_name,
                            "query": query,
                            "total_products": len(products.get('products', [])),
                            "products": products.get('products', [])
                        }
                    else:
                        # Direct product list
                        platform_result = {
                            "site": platform_name,
                            "query": query,
                            "total_products": len(products) if isinstance(products, list) else 0,
                            "products": products if isinstance(products, list) else []
                        }
                elif isinstance(products, list):
                    # Direct list of products
                    platform_result = {
                        "site": platform_name,
                        "query": query,
                        "total_products": len(products),
                        "products": products
                    }
                else:
                    logger.warning(f"⚠️ {platform_name}: Unexpected return format")
                    return None
                
                logger.info(f"✅ {platform_name}: Found {platform_result['total_products']} products")
                return platform_result
                    
            except Exception as e:
                logger.error(f"❌ Error scraping {platform_name}: {e}")
                return None
        
        # Run Myntra first to avoid browser conflicts
        myntra_result = None
        remaining_scrapers = {}
        
        for platform, scraper in self.scrapers.items():
            if platform == "Myntra":
                logger.info(f"🔍 Running {platform} first to avoid browser conflicts...")
                try:
                    myntra_result = scrape_platform(platform, scraper)
                    if myntra_result:
                        results.append(myntra_result)
                        total_products += myntra_result['total_products']
                        logger.info(f"✅ {platform}: Found {myntra_result['total_products']} products")
                    else:
                        logger.warning(f"⚠️ {platform}: No results returned")
                except Exception as e:
                    logger.error(f"❌ {platform} failed: {e}")
            else:
                remaining_scrapers[platform] = scraper
        
        # Use threading to scrape remaining platforms in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_to_platform = {
                executor.submit(scrape_platform, platform, scraper): platform 
                for platform, scraper in remaining_scrapers.items()
            }
            
            for future in as_completed(future_to_platform):
                platform = future_to_platform[future]
                try:
                    result = future.result(timeout=300)  # 5 minute timeout per platform
                    if result:
                        results.append(result)
                        total_products += result['total_products']
                except TimeoutError:
                    logger.warning(f"⏰ {platform}: Timeout after 5 minutes")
                except Exception as e:
                    logger.error(f"❌ {platform} scraping failed: {e}")
        
        # Create unified response
        unified_response = {
            "success": True,
            "query": query,
            "total_results": total_products,
            "results": results
        }
        
        logger.info(f"✅ Web scraping completed. Found {total_products} total products from {len(results)} platforms")
        return unified_response
    
    def save_to_mongodb(self, search_data: Dict) -> bool:
        """
        Save search results to MongoDB
        
        Args:
            search_data: Unified search results
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            result_id = self.mongodb_manager.save_unified_search_result(search_data)
            if result_id:
                logger.info(f"✅ Saved search results to MongoDB with ID: {result_id}")
                return True
            else:
                logger.error("❌ Failed to save to MongoDB")
                return False
        except Exception as e:
            logger.error(f"❌ Error saving to MongoDB: {e}")
            return False
    
    def intelligent_search(self, query: str, force_refresh: bool = False) -> Dict:
        """
        Main intelligent search function
        Implements the workflow: Check MongoDB → If not found → Web scraping → Save to MongoDB
        
        Args:
            query: Search query
            force_refresh: If True, skip cache and force web scraping
            
        Returns:
            Search results in unified format
        """
        logger.info(f"🧠 Starting intelligent search for: '{query}'")
        
        # Step 1: Check MongoDB cache (unless force refresh is requested)
        if not force_refresh:
            cached_results = self.search_in_mongodb(query)
            if cached_results:
                logger.info(f"📦 Returning cached results for: '{query}'")
                return cached_results
        else:
            logger.info(f"🔄 Force refresh requested, skipping cache for: '{query}'")
        
        # Step 2: No cached results found or force refresh - scrape web
        logger.info(f"🌐 No fresh cached results found. Starting web scraping for: '{query}'")
        search_results = self.scrape_all_platforms(query)
        
        # Step 3: Save results to MongoDB
        if search_results.get('success') and search_results.get('total_results', 0) > 0:
            logger.info(f"💾 Saving new search results to MongoDB for: '{query}'")
            self.save_to_mongodb(search_results)
        else:
            logger.warning(f"⚠️ No results found to save for: '{query}'")
            search_results = {
                "success": False,
                "query": query,
                "total_results": 0,
                "results": [],
                "message": "No products found on any platform"
            }
        
        return search_results
    
    def get_search_history(self, limit: int = 10) -> List[Dict]:
        """Get recent search history"""
        return self.mongodb_manager.get_recent_searches(limit)
    
    def get_cached_result_by_id(self, result_id: str) -> Optional[Dict]:
        """Get a specific cached result by ID"""
        return self.mongodb_manager.get_search_result_by_id(result_id)
    
    def close(self):
        """Close connections"""
        self.mongodb_manager.close()

def main():
    """Demo function to test the intelligent search system"""
    search_system = IntelligentSearchSystem(cache_expiry_hours=24)
    
    print("🧠 Intelligent Search System Demo")
    print("=" * 50)
    
    # Test search
    test_query = "smartphones"
    print(f"\n🔍 Testing search for: '{test_query}'")
    
    # First search (will scrape web)
    print("\n1️⃣ First search (should scrape web):")
    results1 = search_system.intelligent_search(test_query)
    print(f"Success: {results1.get('success')}")
    print(f"Total Results: {results1.get('total_results')}")
    print(f"Platforms: {[r['site'] for r in results1.get('results', [])]}")
    
    # Second search (should use cache)
    print("\n2️⃣ Second search (should use cache):")
    results2 = search_system.intelligent_search(test_query)
    print(f"Success: {results2.get('success')}")
    print(f"Total Results: {results2.get('total_results')}")
    print(f"Platforms: {[r['site'] for r in results2.get('results', [])]}")
    
    # Force refresh
    print("\n3️⃣ Force refresh search (should scrape web again):")
    results3 = search_system.intelligent_search(test_query, force_refresh=True)
    print(f"Success: {results3.get('success')}")
    print(f"Total Results: {results3.get('total_results')}")
    print(f"Platforms: {[r['site'] for r in results3.get('results', [])]}")
    
    # Show search history
    print("\n📋 Recent Search History:")
    history = search_system.get_search_history(5)
    for i, search in enumerate(history, 1):
        print(f"{i}. '{search['_id']}' - {search['count']} searches - Last: {search['last_search']}")
    
    search_system.close()
    print("\n✅ Demo completed!")

if __name__ == "__main__":
    main()
