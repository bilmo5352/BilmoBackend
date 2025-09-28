#!/usr/bin/env python3
"""
Fix MongoDB Connection - Complete Setup
This script will help you set up MongoDB Atlas properly
"""

import urllib.parse
from pymongo import MongoClient

def print_setup_instructions():
    print("🔧 MongoDB Atlas Setup Instructions")
    print("=" * 60)
    print()
    print("1. Go to https://cloud.mongodb.com/ and sign in")
    print("2. Create a new cluster (if you don't have one)")
    print("3. Set up Database Access:")
    print("   - Go to 'Database Access' in the left sidebar")
    print("   - Click 'Add New Database User'")
    print("   - Choose 'Password' authentication")
    print("   - Username: hrithick")
    print("   - Password: hrithick")
    print("   - Database User Privileges: 'Read and write to any database'")
    print("   - Click 'Add User'")
    print()
    print("4. Set up Network Access:")
    print("   - Go to 'Network Access' in the left sidebar")
    print("   - Click 'Add IP Address'")
    print("   - Choose 'Allow access from anywhere' (0.0.0.0/0)")
    print("   - Click 'Confirm'")
    print()
    print("5. Get your connection string:")
    print("   - Go to 'Clusters' in the left sidebar")
    print("   - Click 'Connect' on your cluster")
    print("   - Choose 'Connect your application'")
    print("   - Copy the connection string")
    print("   - Replace <password> with 'hrithick'")
    print("   - Replace <dbname> with 'scraper_db'")
    print()
    print("6. Your connection string should look like:")
    print("   mongodb+srv://hrithick:hrithick@<cluster-name>.mongodb.net/scraper_db?retryWrites=true&w=majority")
    print()

def test_connection_with_user_input():
    print("🔗 Test Your Connection String")
    print("=" * 40)
    
    # Get connection string from user
    print("Enter your MongoDB connection string:")
    print("(It should look like: mongodb+srv://hrithick:hrithick@cluster0.xxxxx.mongodb.net/scraper_db?retryWrites=true&w=majority)")
    
    connection_string = input("Connection string: ").strip()
    
    if not connection_string:
        print("❌ No connection string provided")
        return False
    
    print(f"\nTesting: {connection_string}")
    
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
        
        client.close()
        
        # Update all files with the working connection string
        update_all_files(connection_string)
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def update_all_files(connection_string):
    """Update all Python files with the working connection string"""
    print("\n🔄 Updating all files with working connection string...")
    
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
    print("🚀 MongoDB Connection Fixer")
    print("=" * 50)
    print()
    
    # Show setup instructions
    print_setup_instructions()
    
    # Ask if user wants to test connection
    proceed = input("Have you completed the setup steps above? (y/n): ").lower().strip()
    
    if proceed == 'y':
        success = test_connection_with_user_input()
        
        if success:
            print("\n🎉 SUCCESS! Your MongoDB connection is now working!")
            print("All files have been updated with the working connection string.")
        else:
            print("\n❌ Connection still failing. Please check:")
            print("1. Username and password are correct")
            print("2. IP address is whitelisted")
            print("3. Cluster is running")
            print("4. Connection string format is correct")
    else:
        print("\nPlease complete the setup steps first, then run this script again.")

if __name__ == "__main__":
    main()

