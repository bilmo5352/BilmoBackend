#!/usr/bin/env python3
"""
MongoDB Atlas User Setup Script
This script will help you create the user and test the connection
"""

import urllib.parse
from pymongo import MongoClient
import time

def create_user_instructions():
    print("🔧 MongoDB Atlas User Setup")
    print("=" * 50)
    print()
    print("Since we can't programmatically create users in MongoDB Atlas,")
    print("you need to do this manually. Here are the exact steps:")
    print()
    print("1. Go to: https://cloud.mongodb.com/")
    print("2. Sign in to your account")
    print("3. Click on your 'bilmo' cluster")
    print("4. Go to 'Database Access' in the left sidebar")
    print("5. Click 'Add New Database User'")
    print("6. Fill in the form:")
    print("   - Authentication Method: Password")
    print("   - Username: hrithick")
    print("   - Password: hrithick")
    print("   - Database User Privileges: Read and write to any database")
    print("7. Click 'Add User'")
    print("8. Go to 'Network Access' in the left sidebar")
    print("9. Click 'Add IP Address'")
    print("10. Choose 'Allow access from anywhere' (0.0.0.0/0)")
    print("11. Click 'Confirm'")
    print()
    print("⏳ Wait 2-3 minutes for the changes to propagate...")
    print()

def test_connection_with_retry():
    """Test connection with multiple retries"""
    connection_string = "mongodb+srv://hrithick:hrithick@bilmo.jmeclfh.mongodb.net/?retryWrites=true&w=majority&appName=bilmo"
    
    print("🔗 Testing connection with retries...")
    print(f"Connection String: {connection_string}")
    print()
    
    max_retries = 5
    for attempt in range(1, max_retries + 1):
        print(f"Attempt {attempt}/{max_retries}...")
        
        try:
            client = MongoClient(connection_string, serverSelectionTimeoutMS=10000)
            client.admin.command('ping')
            print("✅ Connection successful!")
            
            # List databases
            dbs = client.list_database_names()
            print(f"📊 Available databases: {dbs}")
            
            # Test specific database
            db = client["scraper_db"]
            collections = db.list_collection_names()
            print(f"📁 Collections in scraper_db: {collections}")
            
            # Test inserting a document
            test_doc = {"test": "connection", "timestamp": "2025-01-27", "status": "working"}
            result = db["search_results"].insert_one(test_doc)
            print(f"✅ Test document inserted with ID: {result.inserted_id}")
            
            # Clean up test document
            db["search_results"].delete_one({"_id": result.inserted_id})
            print("✅ Test document cleaned up")
            
            client.close()
            return True
            
        except Exception as e:
            print(f"❌ Attempt {attempt} failed: {e}")
            
            if attempt < max_retries:
                print(f"⏳ Waiting 30 seconds before retry...")
                time.sleep(30)
            else:
                print(f"❌ All {max_retries} attempts failed")
                return False
    
    return False

def update_all_files_with_working_connection():
    """Update all files with the working connection string"""
    connection_string = "mongodb+srv://hrithick:hrithick@bilmo.jmeclfh.mongodb.net/?retryWrites=true&w=majority&appName=bilmo"
    
    print("🔄 Updating all files with working connection string...")
    
    files_to_update = [
        "app.py",
        "mongodb_manager.py", 
        "search_products.py",
        "real_search_products.py",
        "mongodb_json_uploader.py"
    ]
    
    for file_path in files_to_update:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find and replace MongoDB URI
            lines = content.split('\n')
            updated = False
            
            for i, line in enumerate(lines):
                if 'MONGODB_URI' in line and 'mongodb+srv://' in line:
                    lines[i] = f'MONGODB_URI = "{connection_string}"'
                    updated = True
                elif 'connection_string' in line and 'mongodb+srv://' in line:
                    lines[i] = f'    connection_string = "{connection_string}"'
                    updated = True
            
            if updated:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                print(f"✅ Updated {file_path}")
            else:
                print(f"⚠️ No MongoDB URI found in {file_path}")
                
        except Exception as e:
            print(f"❌ Error updating {file_path}: {e}")

def main():
    print("🚀 MongoDB Atlas Setup & Test")
    print("=" * 50)
    print()
    
    # Show setup instructions
    create_user_instructions()
    
    # Ask if user wants to proceed
    proceed = input("Have you completed the user setup steps above? (y/n): ").lower().strip()
    
    if proceed == 'y':
        print("\n🔗 Testing connection...")
        success = test_connection_with_retry()
        
        if success:
            print("\n🎉 SUCCESS! Your MongoDB connection is working!")
            update_all_files_with_working_connection()
            print("\n✅ All files have been updated with the working connection string.")
            print("Your MongoDB connection is now ready to use!")
        else:
            print("\n❌ Connection still failing. Please check:")
            print("1. User 'hrithick' with password 'hrithick' exists in Database Access")
            print("2. IP address is whitelisted in Network Access")
            print("3. Cluster 'bilmo' is running")
            print("4. Wait a few more minutes for changes to propagate")
    else:
        print("\nPlease complete the setup steps first, then run this script again.")

if __name__ == "__main__":
    main()

