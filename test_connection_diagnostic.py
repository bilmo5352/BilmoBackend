#!/usr/bin/env python3
"""
MongoDB Connection Diagnostic Tool
Tests the new connection string and provides detailed error information
"""

from pymongo import MongoClient
import urllib.parse

def test_connection():
    print("🔍 MongoDB Connection Diagnostic")
    print("=" * 50)
    
    # Test the new connection string
    connection_string = "mongodb+srv://hrithick:hrithick@bilmo.jmeclfh.mongodb.net/?retryWrites=true&w=majority&appName=bilmo"
    
    print(f"Connection String: {connection_string}")
    print("\n🔗 Testing connection...")
    
    try:
        # Test with a longer timeout
        client = MongoClient(connection_string, serverSelectionTimeoutMS=10000)
        
        # Test connection
        client.admin.command('ping')
        print("✅ Connection successful!")
        
        # List databases
        dbs = client.list_database_names()
        print(f"📊 Available databases: {dbs}")
        
        # Test specific database access
        db = client["scraper_db"]
        collections = db.list_collection_names()
        print(f"📁 Collections in scraper_db: {collections}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Provide specific troubleshooting steps
        print("\n🔧 Troubleshooting Steps:")
        print("1. Verify the username 'hrithick' exists in MongoDB Atlas")
        print("2. Verify the password 'hrithick' is correct")
        print("3. Check if your IP address is whitelisted in Network Access")
        print("4. Ensure the cluster 'bilmo' is running and accessible")
        print("5. Verify the connection string format is correct")
        
        return False

def test_alternative_credentials():
    """Test with different credential combinations"""
    print("\n🔄 Testing alternative credentials...")
    
    # Test different password variations
    passwords_to_try = [
        "hrithick",
        "hrimee@0514", 
        "hrimee0514",
        "Hrithick",
        "HRITHICK"
    ]
    
    for password in passwords_to_try:
        encoded_password = urllib.parse.quote_plus(password)
        connection_string = f"mongodb+srv://hrithick:{encoded_password}@bilmo.jmeclfh.mongodb.net/?retryWrites=true&w=majority&appName=bilmo"
        
        print(f"\nTesting password: {password}")
        try:
            client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            client.admin.command('ping')
            print(f"✅ SUCCESS with password: {password}")
            client.close()
            return True
        except Exception as e:
            print(f"❌ Failed with password: {password}")
            continue
    
    return False

if __name__ == "__main__":
    success = test_connection()
    
    if not success:
        test_alternative_credentials()
    
    print("\n" + "=" * 50)
    print("Diagnostic complete!")

