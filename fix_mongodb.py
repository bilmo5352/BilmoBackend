#!/usr/bin/env python3
"""
Fix MongoDB Connection Issues
This script helps diagnose and fix MongoDB Atlas connection problems
"""

from pymongo import MongoClient
import urllib.parse
import sys

def test_connection(uri, description):
    """Test a MongoDB connection URI"""
    print(f"\n🔗 Testing: {description}")
    print(f"URI: {uri}")
    
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        # Test connection
        client.admin.command('ping')
        print("✅ Connection successful!")
        
        # List databases
        dbs = client.list_database_names()
        print(f"Available databases: {dbs}")
        
        # Test creating a collection
        db = client['scraper_db']
        collection = db['test_collection']
        
        # Insert a test document
        test_doc = {"test": "connection", "timestamp": "2024-01-01"}
        result = collection.insert_one(test_doc)
        print(f"✅ Test document inserted with ID: {result.inserted_id}")
        
        # Delete the test document
        collection.delete_one({"_id": result.inserted_id})
        print("✅ Test document deleted")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def main():
    print("🔧 MongoDB Atlas Connection Fixer")
    print("=" * 50)
    
    # Your credentials
    username = "hrithick"
    password = "hrimee@0514"
    
    # URL encode the password properly
    encoded_password = urllib.parse.quote_plus(password)
    
    print(f"Username: {username}")
    print(f"Password: {password}")
    print(f"Encoded password: {encoded_password}")
    
    # Different connection strings to try
    connection_strings = [
        # Original format
        (f"mongodb+srv://{username}:{encoded_password}@bilmo.jmeclfh.mongodb.net/?retryWrites=true&w=majority&appName=bilmo", 
         "Original format with appName"),
        
        # Without appName
        (f"mongodb+srv://{username}:{encoded_password}@bilmo.jmeclfh.mongodb.net/?retryWrites=true&w=majority", 
         "Without appName"),
        
        # With database specified
        (f"mongodb+srv://{username}:{encoded_password}@bilmo.jmeclfh.mongodb.net/scraper_db?retryWrites=true&w=majority", 
         "With database specified"),
        
        # Minimal format
        (f"mongodb+srv://{username}:{encoded_password}@bilmo.jmeclfh.mongodb.net/", 
         "Minimal format"),
        
        # With different options
        (f"mongodb+srv://{username}:{encoded_password}@bilmo.jmeclfh.mongodb.net/?retryWrites=true&w=majority&authSource=admin", 
         "With authSource=admin"),
    ]
    
    print("\n🧪 Testing different connection formats...")
    
    success = False
    working_uri = None
    
    for uri, description in connection_strings:
        if test_connection(uri, description):
            success = True
            working_uri = uri
            break
    
    if success:
        print(f"\n🎉 SUCCESS! Working connection string:")
        print(f"{working_uri}")
        
        # Update the mongodb_manager.py file
        print(f"\n📝 Updating mongodb_manager.py with working URI...")
        try:
            with open('mongodb_manager.py', 'r') as f:
                content = f.read()
            
            # Replace the URI
            old_uri = 'MONGODB_URI = "mongodb+srv://hrithick:hrithick@bilmo.jmeclfh.mongodb.net/?retryWrites=true&w=majority&appName=bilmo"'
            new_uri = f'MONGODB_URI = "{working_uri}"'
            
            content = content.replace(old_uri, new_uri)
            
            with open('mongodb_manager.py', 'w') as f:
                f.write(content)
            
            print("✅ Updated mongodb_manager.py")
            
        except Exception as e:
            print(f"⚠️ Could not update mongodb_manager.py: {e}")
        
        print(f"\n🚀 Now you can run: python mongodb_manager.py")
        
    else:
        print(f"\n❌ All connection attempts failed!")
        print(f"\n🔍 Troubleshooting steps:")
        print(f"1. Check MongoDB Atlas Dashboard:")
        print(f"   - Go to https://cloud.mongodb.com/")
        print(f"   - Verify your cluster is running")
        print(f"   - Check Database Access - make sure user 'hrithick' exists")
        print(f"   - Check Network Access - make sure your IP is whitelisted")
        
        print(f"\n2. Verify credentials:")
        print(f"   - Username: {username}")
        print(f"   - Password: {password}")
        print(f"   - Make sure these match exactly in MongoDB Atlas")
        
        print(f"\n3. Check cluster connection string:")
        print(f"   - In MongoDB Atlas, click 'Connect' on your cluster")
        print(f"   - Choose 'Connect your application'")
        print(f"   - Copy the connection string and compare with:")
        print(f"   - goat.kgtnygx.mongodb.net")
        
        print(f"\n4. Create a new database user:")
        print(f"   - Go to Database Access in MongoDB Atlas")
        print(f"   - Delete the existing user if needed")
        print(f"   - Create a new user with a simple password (no special characters)")
        print(f"   - Give it 'Read and write to any database' permissions")

if __name__ == "__main__":
    main()