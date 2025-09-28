#!/usr/bin/env python3
"""
Simple Flask app for testing MongoDB cache functionality
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from datetime import datetime
from pymongo import MongoClient

# MongoDB Configuration
MONGODB_URI = "mongodb+srv://hrithick:hrithick@bilmo.jmeclfh.mongodb.net/?retryWrites=true&w=majority&appName=bilmo"
DB_NAME = "scraper_db"
COLLECTION_NAME = "search_results"

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000", "file://"])

# MongoDB connection
mongodb_client = None
mongodb_db = None
mongodb_collection = None

def connect_mongodb():
    """Connect to MongoDB Atlas"""
    global mongodb_client, mongodb_db, mongodb_collection
    try:
        mongodb_client = MongoClient(MONGODB_URI)
        mongodb_db = mongodb_client[DB_NAME]
        mongodb_collection = mongodb_db[COLLECTION_NAME]
        # Test connection
        mongodb_client.admin.command('ping')
        print("✅ Successfully connected to MongoDB Atlas")
        return True
    except Exception as e:
        print(f"❌ MongoDB connection error: {e}")
        return False

def save_to_mongodb(data, search_type, query):
    """Save search results to MongoDB"""
    global mongodb_collection
    if mongodb_collection is None:
        if not connect_mongodb():
            return False
    
    try:
        document = {
            "search_type": search_type,
            "query": query,
            "timestamp": datetime.now(),
            "data": data,
            "total_results": len(data.get("results", []))
        }
        
        result = mongodb_collection.insert_one(document)
        print(f"✅ Saved {search_type} search for '{query}' to MongoDB with ID: {result.inserted_id}")
        return True
    except Exception as e:
        print(f"❌ Failed to save to MongoDB: {e}")
        return False

@app.route('/')
def home():
    """API info page"""
    return jsonify({
        "message": "Simple E-commerce Scraper API",
        "description": "MongoDB cache functionality test",
        "status": "running",
        "cors_enabled": True,
        "endpoints": {
            "test": "GET /test",
            "search": "GET /search?query=test",
            "results": "GET /api/results"
        }
    })

@app.route('/test')
def test_endpoint():
    """Simple test endpoint"""
    return jsonify({
        "success": True,
        "message": "Simple API is working!",
        "timestamp": datetime.now().isoformat(),
        "mongodb_connected": mongodb_collection is not None
    })

@app.route('/search')
def search():
    """Search endpoint with MongoDB cache"""
    query = request.args.get('query')
    
    if not query:
        return jsonify({
            "success": False,
            "error": "Query parameter is required"
        }), 400
    
    try:
        # Check MongoDB first
        if mongodb_collection is None:
            if not connect_mongodb():
                return jsonify({"error": "MongoDB connection failed"}), 500
        
        # Look for existing results in MongoDB
        existing_result = mongodb_collection.find_one({
            "query": query,
            "search_type": "unified_search"
        }, sort=[("timestamp", -1)])
        
        if existing_result:
            print(f"📋 Found existing results in MongoDB for query: {query}")
            # Convert ObjectId to string for JSON serialization
            existing_result["_id"] = str(existing_result["_id"])
            if "timestamp" in existing_result:
                existing_result["timestamp"] = existing_result["timestamp"].isoformat()
            
            return jsonify({
                "success": True,
                "query": query,
                "source": "mongodb_cache",
                "message": "Results retrieved from MongoDB cache",
                "cached_at": existing_result.get("timestamp"),
                "total_results": existing_result.get("total_results", 0),
                "results": existing_result.get("data", {}).get("results", [])
            })
        
        # No existing results found, create mock data
        print(f"🔍 No cached results found, creating mock data for query: {query}")
        
        # Create mock search results
        mock_results = [
            {
                "site": "amazon",
                "products": [
                    {"name": f"{query} Product 1", "price": "299", "rating": "4.5", "link": "https://amazon.com"},
                    {"name": f"{query} Product 2", "price": "399", "rating": "4.2", "link": "https://amazon.com"}
                ]
            },
            {
                "site": "flipkart", 
                "products": [
                    {"name": f"{query} Product 3", "price": "199", "rating": "4.0", "link": "https://flipkart.com"},
                    {"name": f"{query} Product 4", "price": "499", "rating": "4.7", "link": "https://flipkart.com"}
                ]
            }
        ]
        
        # Prepare response data
        response_data = {
            "success": True,
            "query": query,
            "source": "mock_data",
            "message": "Mock results created and stored in MongoDB",
            "total_results": sum(len(result.get('products', [])) for result in mock_results),
            "results": mock_results
        }
        
        # Save to MongoDB
        save_to_mongodb(response_data, "unified_search", query)
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Search error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/results')
def get_results():
    """Get search results from MongoDB"""
    try:
        query = request.args.get('query')
        limit = int(request.args.get('limit', 50))
        
        if mongodb_collection is None:
            if not connect_mongodb():
                return jsonify({"error": "MongoDB connection failed"}), 500
        
        # Build query filter
        filter_query = {}
        if query:
            filter_query["query"] = {"$regex": query, "$options": "i"}
        
        # Get results from MongoDB
        results = list(mongodb_collection.find(filter_query).sort("timestamp", -1).limit(limit))
        
        # Convert ObjectId to string for JSON serialization
        for result in results:
            result["_id"] = str(result["_id"])
            if "timestamp" in result:
                result["timestamp"] = result["timestamp"].isoformat()
        
        return jsonify({
            "success": True,
            "count": len(results),
            "results": results
        })
        
    except Exception as e:
        print(f"❌ Get results error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 Starting Simple Flask API server...")
    print("💡 This version uses mock data instead of web scraping")
    
    # Connect to MongoDB
    connect_mongodb()
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)
