#!/usr/bin/env python3
"""
Quick MongoDB Setup Instructions
Follow these steps to get MongoDB Atlas working
"""

def main():
    print("🚀 Quick MongoDB Atlas Setup Guide")
    print("=" * 50)
    
    print("\n📋 Step-by-step instructions:")
    
    print("\n1️⃣ Go to MongoDB Atlas:")
    print("   https://cloud.mongodb.com/")
    
    print("\n2️⃣ Sign in or create account")
    
    print("\n3️⃣ Create a cluster (if you don't have one):")
    print("   - Choose 'Build a Database'")
    print("   - Select 'M0 Sandbox' (Free)")
    print("   - Choose a cloud provider and region")
    print("   - Name your cluster (e.g., 'goat')")
    
    print("\n4️⃣ Create a database user:")
    print("   - Go to 'Database Access' in left menu")
    print("   - Click 'Add New Database User'")
    print("   - Authentication Method: Password")
    print("   - Username: hrithick")
    print("   - Password: hrimee@0514")
    print("   - Database User Privileges: 'Read and write to any database'")
    print("   - Click 'Add User'")
    
    print("\n5️⃣ Set up network access:")
    print("   - Go to 'Network Access' in left menu")
    print("   - Click 'Add IP Address'")
    print("   - Choose 'Allow access from anywhere' (0.0.0.0/0)")
    print("   - Or click 'Add Current IP Address'")
    print("   - Click 'Confirm'")
    
    print("\n6️⃣ Get connection string:")
    print("   - Go to 'Clusters' in left menu")
    print("   - Click 'Connect' button on your cluster")
    print("   - Choose 'Connect your application'")
    print("   - Select 'Python' and version '3.6 or later'")
    print("   - Copy the connection string")
    print("   - It should look like:")
    print("   mongodb+srv://hrithick:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority")
    
    print("\n7️⃣ Test the connection:")
    print("   - Replace <password> with: hrimee%400514")
    print("   - Update mongodb_json_uploader.py with your connection string")
    print("   - Run: python mongodb_json_uploader.py")
    
    print("\n🔧 Common issues and fixes:")
    print("   ❌ Authentication failed:")
    print("      - Double-check username and password")
    print("      - Make sure user has correct permissions")
    print("      - Wait a few minutes after creating user")
    
    print("   ❌ Network timeout:")
    print("      - Check Network Access settings")
    print("      - Add your IP address or allow all (0.0.0.0/0)")
    
    print("   ❌ Connection string issues:")
    print("      - Make sure cluster name is correct")
    print("      - URL-encode special characters in password")
    print("      - @ symbol becomes %40")
    
    print("\n💡 Alternative approach:")
    print("   If you're still having issues:")
    print("   1. Create a new user with a simple password (no special characters)")
    print("   2. Use a password like 'password123' for testing")
    print("   3. Once it works, you can change to a more secure password")
    
    print("\n📞 Need help?")
    print("   - MongoDB Atlas documentation: https://docs.atlas.mongodb.com/")
    print("   - MongoDB community forums: https://community.mongodb.com/")
    
    print("\n✅ Once connected, your JSON files will be automatically uploaded to MongoDB!")

if __name__ == "__main__":
    main()