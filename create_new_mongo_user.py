#!/usr/bin/env python3
"""
Create New MongoDB User Test
Test with different user credentials to isolate the issue
"""

from pymongo import MongoClient
import urllib.parse

def test_with_simple_credentials():
    """Test with simple credentials (no special characters)"""
    print("🧪 Testing with simple credentials...")
    
    # Simple test credentials
    username = "testuser"
    password = "testpass123"
    encoded_password = urllib.parse.quote_plus(password)
    
    uri = f"mongodb+srv://{username}:{encoded_password}@goat.kgtnygx.mongodb.net/?retryWrites=true&w=majority"
    
    print(f"Username: {username}")
    print(f"Password: {password}")
    print(f"URI: {uri}")
    
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("✅ Simple credentials work!")
        client.close()
        return True
    except Exception as e:
        print(f"❌ Simple credentials failed: {e}")
        return False

def test_cluster_connectivity():
    """Test if the cluster itself is reachable"""
    print("\n🌐 Testing cluster connectivity...")
    
    # Test without authentication
    try:
        # This will fail auth but should reach the cluster
        client = MongoClient("mongodb+srv://goat.kgtnygx.mongodb.net/", serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
    except Exception as e:
        error_msg = str(e)
        if "authentication failed" in error_msg.lower() or "bad auth" in error_msg.lower():
            print("✅ Cluster is reachable (authentication issue only)")
            return True
        elif "timeout" in error_msg.lower() or "network" in error_msg.lower():
            print(f"❌ Network/cluster issue: {e}")
            return False
        else:
            print(f"✅ Cluster reachable, auth issue: {e}")
            return True

def main():
    print("🔍 MongoDB Connection Diagnostics")
    print("=" * 40)
    
    # Test cluster connectivity
    cluster_ok = test_cluster_connectivity()
    
    if not cluster_ok:
        print("\n❌ Cluster connectivity issue!")
        print("The cluster 'goat.kgtnygx.mongodb.net' might not exist or be accessible.")
        print("\nPlease check:")
        print("1. Go to https://cloud.mongodb.com/")
        print("2. Verify your cluster name and connection string")
        print("3. Make sure the cluster is running")
        return
    
    print("\n✅ Cluster is reachable - this is an authentication issue.")
    
    # Test with simple credentials
    simple_works = test_with_simple_credentials()
    
    print("\n📋 Diagnosis:")
    if simple_works:
        print("✅ Simple credentials work - issue is with your current password")
        print("The special characters in 'hrimee@0514' might be causing issues")
    else:
        print("❌ Even simple credentials fail - user setup issue")
    
    print("\n🔧 Recommended fixes:")
    print("1. Go to MongoDB Atlas Dashboard")
    print("2. Database Access → Delete existing user 'hrithick'")
    print("3. Create new user:")
    print("   - Username: hrithick")
    print("   - Password: simplepass123 (no special characters)")
    print("   - Privileges: Read and write to any database")
    print("4. Network Access → Add IP 0.0.0.0/0 (allow all)")
    print("5. Wait 2-3 minutes for changes to propagate")
    print("6. Test again")
    
    print("\n💡 Alternative:")
    print("Create a completely new cluster if issues persist:")
    print("1. Create new cluster with different name")
    print("2. Use simple credentials from the start")
    print("3. Update connection string in your code")

if __name__ == "__main__":
    main()