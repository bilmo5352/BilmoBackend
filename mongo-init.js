// MongoDB initialization script for Docker
db = db.getSiblingDB('bilmo_cache');

// Create collections
db.createCollection('search_cache');
db.createCollection('product_cache');

// Create indexes for better performance
db.search_cache.createIndex({ "query": 1, "timestamp": 1 });
db.search_cache.createIndex({ "timestamp": 1 }, { expireAfterSeconds: 86400 }); // 24 hours TTL

db.product_cache.createIndex({ "product_id": 1 });
db.product_cache.createIndex({ "platform": 1, "query": 1 });
db.product_cache.createIndex({ "timestamp": 1 }, { expireAfterSeconds: 86400 }); // 24 hours TTL

// Create a user for the application
db.createUser({
  user: "bilmo_user",
  pwd: "bilmo_password",
  roles: [
    {
      role: "readWrite",
      db: "bilmo_cache"
    }
  ]
});

print("MongoDB initialization completed successfully!");










