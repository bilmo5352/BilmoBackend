#!/usr/bin/env python3
"""
MongoDB Setup Guide for E-commerce Scraper
This script helps you set up MongoDB Atlas connection
"""

import urllib.parse

def main():
    print("🔧 MongoDB Atlas Setup Guide")
    print("=" * 50)
    
    print("\n📋 Steps to set up MongoDB Atlas:")
    print("1. Go to https://cloud.mongodb.com/")
    print("2. Sign in or create a free account")
    print("3. Create a new cluster (free tier is fine)")
    print("4. Create a database user:")
    print("   - Go to Database Access")
    print("   - Click 'Add New Database User'")
    print("   - Choose 'Password' authentication")
    print("   - Username: hrithick")
    print("   - Password: hrimee@0514")
    print("   - Database User Privileges: 'Read and write to any database'")
    print("5. Set up network access:")
    print("   - Go to Network Access")
    print("   - Click 'Add IP Address'")
    print("   - Choose 'Allow access from anywhere' (0.0.0.0/0)")
    print("   - Or add your current IP address")
    print("6. Get connection string:")
    print("   - Go to Clusters")
    print("   - Click 'Connect' on your cluster")
    print("   - Choose 'Connect your application'")
    print("   - Copy the connection string")
    
    print("\n🔗 Your current connection details:")
    username = "hrithick"
    password = "hrimee@0514"
    encoded_password = urllib.parse.quote_plus(password)
    
    print(f"Username: {username}")
    print(f"Password: {password}")
    print(f"URL-encoded password: {encoded_password}")
    
    print(f"\n📝 Expected connection string format:")
    print(f"mongodb+srv://{username}:{encoded_password}@<cluster-name>.mongodb.net/?retryWrites=true&w=majority")
    
    print(f"\n🔍 Current connection string in your code:")
    print(f"mongodb+srv://{username}:{encoded_password}@goat.kgtnygx.mongodb.net/?retryWrites=true&w=majority&appName=goat")
    
    print("\n⚠️ Common issues and solutions:")
    print("1. Authentication failed:")
    print("   - Verify username and password in MongoDB Atlas")
    print("   - Make sure the user has proper permissions")
    print("   - Check if the user is created for the correct database")
    
    print("2. Network/IP issues:")
    print("   - Add your IP address to the whitelist")
    print("   - Or allow access from anywhere (0.0.0.0/0)")
    
    print("3. Cluster name issues:")
    print("   - Verify the cluster connection string")
    print("   - Make sure 'goat.kgtnygx.mongodb.net' is correct")
    
    print("\n🧪 Test connection manually:")
    print("1. Install MongoDB Compass (GUI tool)")
    print("2. Use the connection string to connect")
    print("3. If it works in Compass, it should work in Python")
    
    print("\n📞 Next steps:")
    print("1. Verify your MongoDB Atlas setup")
    print("2. Update the connection string if needed")
    print("3. Run the test script again")
    
    print("\n💡 Alternative: Use MongoDB locally")
    print("If Atlas doesn't work, you can:")
    print("1. Install MongoDB locally")
    print("2. Use connection string: mongodb://localhost:27017/")
    print("3. No authentication needed for local development")

if __name__ == "__main__":
    main()