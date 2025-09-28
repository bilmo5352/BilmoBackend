#!/usr/bin/env python3
"""
Test MongoDB connection with different URI formats
"""

from pymongo import MongoClient
import urllib.parse

# Your credentials
username = "hrithick"
password = "hrithick"

# URL encode the password
encoded_password = urllib.parse.quote_plus(password)
print(f"Original password: {password}")
print(f"URL encoded password: {encoded_password}")

# Different URI formats to try
uris = [
    f"mongodb+srv://{username}:{encoded_password}@bilmo.jmeclfh.mongodb.net/?retryWrites=true&w=majority&appName=bilmo",
    f"mongodb+srv://{username}:{password}@bilmo.jmeclfh.mongodb.net/?retryWrites=true&w=majority&appName=bilmo",
    f"mongodb+srv://{username}:{encoded_password}@bilmo.jmeclfh.mongodb.net/scraper_db?retryWrites=true&w=majority",
]

for i, uri in enumerate(uris, 1):
    print(f"\n🔗 Testing URI {i}:")
    print(f"URI: {uri}")
    
    try:
        client = MongoClient(uri)
        # Test connection
        client.admin.command('ping')
        print("✅ Connection successful!")
        
        # List databases
        dbs = client.list_database_names()
        print(f"Available databases: {dbs}")
        
        client.close()
        break
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        continue
else:
    print("\n❌ All connection attempts failed")