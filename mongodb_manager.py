#!/usr/bin/env python3
"""
MongoDB Manager for E-commerce Scraper
Handles MongoDB operations for storing and retrieving JSON files
"""

import json
import os
import glob
from datetime import datetime
from pymongo import MongoClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB Configuration
MONGODB_URI = "mongodb+srv://hrithick:hrimee%400514@goat.kgtnygx.mongodb.net/?retryWrites=true&w=majority&appName=goat"
DB_NAME = "scraper_db"
COLLECTION_NAME = "search_results"
JSON_FILES_COLLECTION = "json_files"

class MongoDBManager:
    def __init__(self):
        self.client = None
        self.db = None
        self.search_collection = None
        self.json_files_collection = None
        
    def connect(self):
        """Connect to MongoDB Atlas"""
        try:
            self.client = MongoClient(MONGODB_URI)
            self.db = self.client[DB_NAME]
            self.search_collection = self.db[COLLECTION_NAME]
            self.json_files_collection = self.db[JSON_FILES_COLLECTION]
            
            # Test connection
            self.client.admin.command('ping')
            logger.info("✅ Successfully connected to MongoDB Atlas")
            return True
        except Exception as e:
            logger.error(f"❌ MongoDB connection error: {e}")
            return False
    
    def save_json_file(self, file_path, file_name=None):
        """Save JSON file contents to MongoDB"""
        if not self.db:
            if not self.connect():
                return False
        
        try:
            # Read JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Get file info
            file_stats = os.stat(file_path)
            file_size = file_stats.st_size
            
            # Prepare document
            document = {
                "file_name": file_name or os.path.basename(file_path),
                "file_path": file_path,
                "file_size": file_size,
                "upload_timestamp": datetime.now(),
                "file_modified": datetime.fromtimestamp(file_stats.st_mtime),
                "json_content": json_data,
                "content_type": "json",
                "source": "scraper_output"
            }
            
            # Check if file already exists
            existing = self.json_files_collection.find_one({
                "file_name": document["file_name"],
                "file_modified": document["file_modified"]
            })
            
            if existing:
                logger.info(f"⚠️ File '{document['file_name']}' already exists in MongoDB")
                return existing["_id"]
            
            # Save to JSON files collection
            result = self.json_files_collection.insert_one(document)
            
            logger.info(f"✅ Saved JSON file '{document['file_name']}' to MongoDB with ID: {result.inserted_id}")
            return result.inserted_id
            
        except Exception as e:
            logger.error(f"❌ Failed to save JSON file to MongoDB: {e}")
            return False
    
    def save_all_json_files(self):
        """Save all existing JSON files in the directory to MongoDB"""
        # Find all JSON files
        json_patterns = [
            "unified_search_*.json",
            "*_search_*.json", 
            "*_detailed_*.json"
        ]
        
        saved_files = []
        failed_files = []
        skipped_files = []
        
        for pattern in json_patterns:
            json_files = glob.glob(pattern)
            for file_path in json_files:
                try:
                    result = self.save_json_file(file_path)
                    if result:
                        if isinstance(result, str):  # ObjectId converted to string
                            saved_files.append(file_path)
                        else:
                            skipped_files.append(file_path)
                    else:
                        failed_files.append(file_path)
                except Exception as e:
                    logger.error(f"❌ Error saving {file_path}: {e}")
                    failed_files.append(file_path)
        
        logger.info(f"✅ Successfully saved {len(saved_files)} JSON files to MongoDB")
        if skipped_files:
            logger.info(f"⚠️ Skipped {len(skipped_files)} files (already exist): {skipped_files}")
        if failed_files:
            logger.warning(f"⚠️ Failed to save {len(failed_files)} files: {failed_files}")
        
        return {
            "saved_count": len(saved_files),
            "skipped_count": len(skipped_files),
            "failed_count": len(failed_files),
            "saved_files": saved_files,
            "skipped_files": skipped_files,
            "failed_files": failed_files
        }
    
    def get_json_files(self, limit=10):
        """Retrieve JSON files from MongoDB"""
        if not self.db:
            if not self.connect():
                return []
        
        try:
            cursor = self.json_files_collection.find().sort("upload_timestamp", -1).limit(limit)
            
            files = []
            for doc in cursor:
                # Convert ObjectId to string for JSON serialization
                doc['_id'] = str(doc['_id'])
                files.append(doc)
            
            return files
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve JSON files from MongoDB: {e}")
            return []
    
    def get_json_file_by_id(self, file_id):
        """Get a specific JSON file by ID from MongoDB"""
        if not self.db:
            if not self.connect():
                return None
        
        try:
            from bson import ObjectId
            file_doc = self.json_files_collection.find_one({"_id": ObjectId(file_id)})
            
            if file_doc:
                file_doc['_id'] = str(file_doc['_id'])
                return file_doc
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve JSON file {file_id}: {e}")
            return None
    
    def get_database_stats(self):
        """Get database statistics"""
        if not self.db:
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
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("✅ MongoDB connection closed")

def main():
    """Main function to demonstrate MongoDB operations"""
    manager = MongoDBManager()
    
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
        
        print("\n📁 Uploading JSON files...")
        result = manager.save_all_json_files()
        print(f"✅ Upload complete: {result}")
        
        print("\n📋 Recent JSON files:")
        files = manager.get_json_files(5)
        for i, file in enumerate(files, 1):
            print(f"{i}. {file['file_name']} (ID: {file['_id']}) - {file['upload_timestamp']}")
        
        manager.close()
    else:
        print("❌ Failed to connect to MongoDB")

if __name__ == "__main__":
    main()