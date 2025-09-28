#!/usr/bin/env python3
"""
Updated MongoDB Manager for Unified Search Results
Handles MongoDB operations for storing search results in the new unified format
"""

import json
import os
from datetime import datetime
from pymongo import MongoClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB Configuration
MONGODB_URI = "mongodb+srv://hrithick:hrithick@bilmo.jmeclfh.mongodb.net/?retryWrites=true&w=majority&appName=bilmo"
DB_NAME = "scraper_db"
COLLECTION_NAME = "unified_search_results"

class UnifiedMongoDBManager:
    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
        
    def connect(self):
        """Connect to MongoDB Atlas"""
        try:
            self.client = MongoClient(MONGODB_URI)
            self.db = self.client[DB_NAME]
            self.collection = self.db[COLLECTION_NAME]
            
            # Test connection
            self.client.admin.command('ping')
            logger.info("✅ Successfully connected to MongoDB Atlas")
            return True
        except Exception as e:
            logger.error(f"❌ MongoDB connection error: {e}")
            return False
    
    def save_unified_search_result(self, search_data):
        """
        Save unified search result in the new format
        
        Expected format:
        {
            "success": true,
            "query": "phones",
            "total_results": 6,
            "results": [
                {
                    "site": "Amazon",
                    "query": "phones",
                    "total_products": 2,
                    "products": [...]
                },
                ...
            ]
        }
        """
        if self.collection is None:
            if not self.connect():
                return False
        
        try:
            # Create a copy to avoid modifying the original data
            data_to_save = search_data.copy()
            data_to_save["search_timestamp"] = datetime.now()
            
            # Insert the document
            result = self.collection.insert_one(data_to_save)
            
            logger.info(f"✅ Saved unified search result for query '{search_data.get('query', 'unknown')}' with ID: {result.inserted_id}")
            return result.inserted_id
            
        except Exception as e:
            logger.error(f"❌ Failed to save unified search result: {e}")
            return False
    
    def get_search_results(self, query=None, limit=10):
        """Retrieve search results from MongoDB"""
        if self.collection is None:
            if not self.connect():
                return []
        
        try:
            # Build query filter
            filter_query = {}
            if query:
                filter_query["query"] = {"$regex": query, "$options": "i"}
            
            cursor = self.collection.find(filter_query).sort("search_timestamp", -1).limit(limit)
            
            results = []
            for doc in cursor:
                # Convert ObjectId to string for JSON serialization
                doc['_id'] = str(doc['_id'])
                results.append(doc)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve search results: {e}")
            return []
    
    def get_search_result_by_id(self, result_id):
        """Get a specific search result by ID"""
        if self.collection is None:
            if not self.connect():
                return None
        
        try:
            from bson import ObjectId
            result_doc = self.collection.find_one({"_id": ObjectId(result_id)})
            
            if result_doc:
                result_doc['_id'] = str(result_doc['_id'])
                return result_doc
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve search result {result_id}: {e}")
            return None
    
    def get_database_stats(self):
        """Get database statistics"""
        if self.db is None:
            if not self.connect():
                return None
        
        try:
            stats = self.client.admin.command("dbstats")
            collections = self.db.list_collection_names()
            
            # Get collection stats
            collection_stats = {}
            for collection_name in collections:
                collection = self.db[collection_name]
                count = collection.count_documents({})
                collection_stats[collection_name] = count
            
            return {
                "database": DB_NAME,
                "collections": collections,
                "collection_stats": collection_stats,
                "db_size": stats.get("dataSize", 0),
                "collections_count": len(collections)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get database stats: {e}")
            return None
    
    def delete_all_results(self):
        """Delete all search results from the collection"""
        if self.collection is None:
            if not self.connect():
                return False
        
        try:
            result = self.collection.delete_many({})
            logger.info(f"✅ Deleted {result.deleted_count} search results")
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"❌ Failed to delete search results: {e}")
            return False
    
    def get_recent_searches(self, limit=5):
        """Get recent search queries"""
        if self.collection is None:
            if not self.connect():
                return []
        
        try:
            pipeline = [
                {"$group": {
                    "_id": "$query",
                    "last_search": {"$max": "$search_timestamp"},
                    "count": {"$sum": 1}
                }},
                {"$sort": {"last_search": -1}},
                {"$limit": limit}
            ]
            
            results = list(self.collection.aggregate(pipeline))
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to get recent searches: {e}")
            return []
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("✅ MongoDB connection closed")

def main():
    """Main function to demonstrate MongoDB operations"""
    manager = UnifiedMongoDBManager()
    
    print("🔗 Testing MongoDB connection...")
    if manager.connect():
        print("✅ Connected successfully!")
        
        print("\n📊 Database Statistics:")
        stats = manager.get_database_stats()
        if stats:
            print(f"Database: {stats['database']}")
            print(f"Collections: {stats['collections']}")
            print(f"Collection Stats: {stats['collection_stats']}")
            print(f"Database Size: {stats['db_size']} bytes")
        
        print("\n🔍 Recent Search Results:")
        results = manager.get_search_results(limit=3)
        for i, result in enumerate(results, 1):
            print(f"{i}. Query: '{result['query']}' - {result['total_results']} results - {result['search_timestamp']}")
        
        print("\n📋 Recent Search Queries:")
        recent_searches = manager.get_recent_searches(5)
        for i, search in enumerate(recent_searches, 1):
            print(f"{i}. '{search['_id']}' - {search['count']} searches - Last: {search['last_search']}")
        
        manager.close()
    else:
        print("❌ Failed to connect to MongoDB")

if __name__ == "__main__":
    main()
