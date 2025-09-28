#!/usr/bin/env python3
"""
MongoDB JSON File Uploader
Upload your JSON files to MongoDB Atlas once connection is fixed
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

class MongoDBJSONUploader:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.client = None
        self.db = None
        self.collection = None
        
    def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client['scraper_db']
            self.collection = self.db['json_files']
            
            # Test connection
            self.client.admin.command('ping')
            logger.info("✅ Successfully connected to MongoDB")
            return True
        except Exception as e:
            logger.error(f"❌ MongoDB connection error: {e}")
            return False
    
    def upload_json_file(self, file_path):
        """Upload a single JSON file to MongoDB"""
        try:
            # Read JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Get file info
            file_stats = os.stat(file_path)
            
            # Create document
            document = {
                "file_name": os.path.basename(file_path),
                "file_path": file_path,
                "file_size": file_stats.st_size,
                "upload_timestamp": datetime.now(),
                "file_modified": datetime.fromtimestamp(file_stats.st_mtime),
                "json_content": json_data,
                "content_type": "json",
                "source": "scraper_output"
            }
            
            # Check if file already exists
            existing = self.collection.find_one({
                "file_name": document["file_name"],
                "file_modified": document["file_modified"]
            })
            
            if existing:
                logger.info(f"⚠️ File '{document['file_name']}' already exists in MongoDB")
                return str(existing["_id"])
            
            # Insert document
            result = self.collection.insert_one(document)
            logger.info(f"✅ Uploaded '{document['file_name']}' to MongoDB with ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"❌ Failed to upload {file_path}: {e}")
            return None
    
    def upload_all_json_files(self):
        """Upload all JSON files from current directory"""
        json_patterns = [
            "unified_search_*.json",
            "*_search_*.json", 
            "*_detailed_*.json"
        ]
        
        uploaded_files = []
        failed_files = []
        skipped_files = []
        
        for pattern in json_patterns:
            json_files = glob.glob(pattern)
            for file_path in json_files:
                try:
                    result = self.upload_json_file(file_path)
                    if result:
                        if len(result) == 24:  # ObjectId length
                            uploaded_files.append(file_path)
                        else:
                            skipped_files.append(file_path)
                    else:
                        failed_files.append(file_path)
                except Exception as e:
                    logger.error(f"❌ Error uploading {file_path}: {e}")
                    failed_files.append(file_path)
        
        return {
            "uploaded_count": len(uploaded_files),
            "skipped_count": len(skipped_files),
            "failed_count": len(failed_files),
            "uploaded_files": uploaded_files,
            "skipped_files": skipped_files,
            "failed_files": failed_files
        }
    
    def list_uploaded_files(self, limit=10):
        """List uploaded files from MongoDB"""
        try:
            cursor = self.collection.find().sort("upload_timestamp", -1).limit(limit)
            
            files = []
            for doc in cursor:
                doc['_id'] = str(doc['_id'])
                files.append(doc)
            
            return files
        except Exception as e:
            logger.error(f"❌ Failed to list files: {e}")
            return []
    
    def get_database_stats(self):
        """Get database statistics"""
        try:
            stats = self.client.admin.command("dbstats")
            collections = self.db.list_collection_names()
            
            collection_stats = {}
            for collection_name in collections:
                collection = self.db[collection_name]
                count = collection.count_documents({})
                collection_stats[collection_name] = count
            
            return {
                "database": "scraper_db",
                "collections": collections,
                "collection_stats": collection_stats,
                "db_size": stats.get("dataSize", 0),
                "collections_count": len(collections)
            }
        except Exception as e:
            logger.error(f"❌ Failed to get stats: {e}")
            return None
    
    def close(self):
        """Close connection"""
        if self.client:
            self.client.close()
            logger.info("✅ MongoDB connection closed")

def main():
    print("📤 MongoDB JSON File Uploader")
    print("=" * 40)
    
    # You need to update this connection string once you fix MongoDB Atlas
    print("⚠️ IMPORTANT: Update the connection string below with your working MongoDB Atlas URI")
    print("Current connection string is a placeholder - it won't work!")
    
    # PLACEHOLDER - Replace with your working connection string
    connection_string = "mongodb+srv://hrithick:hrithick@bilmo.jmeclfh.mongodb.net/?retryWrites=true&w=majority&appName=bilmo"
    
    print(f"\nConnection string: {connection_string}")
    print("\n🔧 To fix the connection:")
    print("1. Go to https://cloud.mongodb.com/")
    print("2. Create/verify database user 'hrithick' with password 'hrimee@0514'")
    print("3. Add your IP to Network Access (or allow 0.0.0.0/0)")
    print("4. Get the correct connection string from 'Connect' button")
    print("5. Update the connection_string variable above")
    
    # Ask user if they want to proceed
    proceed = input("\nHave you updated the connection string? (y/n): ").lower().strip()
    if proceed != 'y':
        print("Please update the connection string first!")
        return
    
    # Initialize uploader
    uploader = MongoDBJSONUploader(connection_string)
    
    # Test connection
    if not uploader.connect():
        print("❌ Failed to connect to MongoDB. Please check your connection string.")
        return
    
    # Get current stats
    print("\n📊 Current database stats:")
    stats = uploader.get_database_stats()
    if stats:
        print(f"Database: {stats['database']}")
        print(f"Collections: {stats['collections']}")
        print(f"Collection stats: {stats['collection_stats']}")
    
    # Upload all JSON files
    print("\n📤 Uploading JSON files...")
    result = uploader.upload_all_json_files()
    
    print(f"\n✅ Upload Results:")
    print(f"Uploaded: {result['uploaded_count']} files")
    print(f"Skipped: {result['skipped_count']} files (already exist)")
    print(f"Failed: {result['failed_count']} files")
    
    if result['uploaded_files']:
        print(f"\nUploaded files:")
        for file in result['uploaded_files']:
            print(f"  - {file}")
    
    if result['failed_files']:
        print(f"\nFailed files:")
        for file in result['failed_files']:
            print(f"  - {file}")
    
    # List recent files
    print(f"\n📋 Recent files in MongoDB:")
    files = uploader.list_uploaded_files(5)
    for i, file in enumerate(files, 1):
        print(f"{i}. {file['file_name']} (ID: {file['_id']}) - {file['upload_timestamp']}")
    
    uploader.close()
    print(f"\n🎉 Done! Your JSON files are now stored in MongoDB Atlas.")

if __name__ == "__main__":
    main()