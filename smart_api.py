#!/usr/bin/env python3
"""
Smart E-commerce API with Intelligent Caching
Implements: Search → Check MongoDB → Not found → Web scraping → Save to MongoDB
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json
import time
from datetime import datetime
from intelligent_search_system import IntelligentSearchSystem
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"], methods=["GET", "POST", "OPTIONS"])

# Initialize intelligent search system
search_system = IntelligentSearchSystem(cache_expiry_hours=24)

@app.route('/')
def home():
    """Home page with API documentation"""
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Smart E-commerce Search API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .endpoint { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .method { color: #007acc; font-weight: bold; }
            .success { color: #28a745; }
            .warning { color: #ffc107; }
            .error { color: #dc3545; }
            pre { background: #f8f9fa; padding: 10px; border-radius: 3px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <h1>🧠 Smart E-commerce Search API</h1>
        <p><strong>Intelligent workflow:</strong> Search → Check MongoDB Cache → Not found → Web Scraping → Save to MongoDB</p>
        
        <h2>📍 API Endpoints</h2>
        
        <div class="endpoint">
            <h3><span class="method">GET</span> /search</h3>
            <p>Intelligent product search with caching</p>
            <p><strong>Parameters:</strong></p>
            <ul>
                <li><code>q</code> - Search query (required)</li>
                <li><code>force_refresh</code> - Skip cache and force web scraping (optional, default: false)</li>
            </ul>
            <p><strong>Example:</strong> <code>/search?q=smartphones&force_refresh=true</code></p>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">POST</span> /search</h3>
            <p>Intelligent product search via JSON</p>
            <p><strong>Body:</strong> <code>{"query": "phones", "force_refresh": false}</code></p>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">GET</span> /history</h3>
            <p>Get recent search history</p>
            <p><strong>Parameters:</strong></p>
            <ul>
                <li><code>limit</code> - Number of recent searches (optional, default: 10)</li>
            </ul>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">GET</span> /cached/{result_id}</h3>
            <p>Get specific cached result by ID</p>
        </div>
        
        <div class="endpoint">
            <h3><span class="method">GET</span> /status</h3>
            <p>Check API and database status</p>
        </div>
        
        <h2>📊 Response Format</h2>
        <pre>{
  "success": true,
  "query": "phones",
  "total_results": 6,
  "source": "cache" | "web_scraping",
  "cache_age": "2 hours ago",
  "results": [
    {
      "site": "Amazon",
      "query": "phones",
      "total_products": 2,
      "products": [...]
    },
    {
      "site": "Flipkart", 
      "query": "phones",
      "total_products": 2,
      "products": [...]
    }
  ]
}</pre>
        
        <h2>🚀 Quick Test</h2>
        <p>Try these endpoints:</p>
        <ul>
            <li><a href="/search?q=phones">/search?q=phones</a></li>
            <li><a href="/history">/history</a></li>
            <li><a href="/status">/status</a></li>
        </ul>
        
        <div style="margin-top: 30px; padding: 15px; background: #e7f3ff; border-radius: 5px;">
            <h3>💡 Smart Features</h3>
            <ul>
                <li><strong>Automatic Caching:</strong> Results are cached for 24 hours to improve speed</li>
                <li><strong>Multi-platform:</strong> Searches Amazon, Flipkart, Meesho, and Myntra simultaneously</li>
                <li><strong>Force Refresh:</strong> Use force_refresh=true to get fresh results</li>
                <li><strong>Unified Format:</strong> All results in consistent JSON format</li>
            </ul>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html)

@app.route('/search', methods=['GET', 'POST'])
def search_products():
    """
    Intelligent product search endpoint
    Implements: Check cache → If not found → Web scraping → Save to cache
    """
    try:
        start_time = time.time()
        
        # Get search parameters
        if request.method == 'POST':
            data = request.get_json()
            if not data:
                return jsonify({"error": "Invalid JSON"}), 400
            query = data.get('query', '').strip()
            force_refresh = data.get('force_refresh', False)
        else:
            query = request.args.get('q', '').strip()
            force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
        
        if not query:
            return jsonify({"error": "Query parameter 'q' is required"}), 400
        
        logger.info(f"🔍 Search request: query='{query}', force_refresh={force_refresh}")
        
        # Perform intelligent search
        results = search_system.intelligent_search(query, force_refresh=force_refresh)
        
        # Add metadata
        end_time = time.time()
        processing_time = round(end_time - start_time, 2)
        
        # Determine if results came from cache or web scraping
        if not force_refresh:
            # Check if we have a recent cache entry
            cached_result = search_system.search_in_mongodb(query)
            if cached_result:
                cache_time = cached_result.get('search_timestamp')
                if cache_time:
                    cache_age = datetime.now() - cache_time
                    results['source'] = 'cache'
                    results['cache_age'] = str(cache_age).split('.')[0] + ' ago'
                else:
                    results['source'] = 'web_scraping'
            else:
                results['source'] = 'web_scraping'
        else:
            results['source'] = 'web_scraping'
        
        results['processing_time'] = f"{processing_time}s"
        results['timestamp'] = datetime.now().isoformat()
        
        logger.info(f"✅ Search completed in {processing_time}s: {results.get('total_results', 0)} results")
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"❌ Search error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/history')
def search_history():
    """Get recent search history"""
    try:
        limit = request.args.get('limit', 10, type=int)
        limit = max(1, min(limit, 50))  # Limit between 1 and 50
        
        history = search_system.get_search_history(limit)
        
        return jsonify({
            "success": True,
            "total_searches": len(history),
            "searches": history,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ History error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/cached/<result_id>')
def get_cached_result(result_id):
    """Get specific cached result by ID"""
    try:
        result = search_system.get_cached_result_by_id(result_id)
        
        if result:
            return jsonify({
                "success": True,
                "result": result,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "error": "Result not found",
                "timestamp": datetime.now().isoformat()
            }), 404
            
    except Exception as e:
        logger.error(f"❌ Cached result error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/status')
def api_status():
    """Check API and database status"""
    try:
        # Test MongoDB connection
        mongodb_status = search_system.mongodb_manager.connect()
        
        # Get database stats
        db_stats = search_system.mongodb_manager.get_database_stats()
        
        status = {
            "success": True,
            "api_status": "online",
            "mongodb_status": "connected" if mongodb_status else "disconnected",
            "timestamp": datetime.now().isoformat(),
            "cache_expiry_hours": search_system.cache_expiry_hours
        }
        
        if db_stats:
            status["database_stats"] = db_stats
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"❌ Status check error: {e}")
        return jsonify({
            "success": False,
            "api_status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "available_endpoints": [
            "/search?q=<query>",
            "/history",
            "/cached/<id>", 
            "/status"
        ],
        "timestamp": datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "timestamp": datetime.now().isoformat()
    }), 500

# Graceful shutdown
import atexit

def cleanup():
    """Cleanup function"""
    logger.info("🧹 Cleaning up resources...")
    search_system.close()

atexit.register(cleanup)

if __name__ == '__main__':
    logger.info("🚀 Starting Smart E-commerce Search API...")
    logger.info("📍 Endpoints:")
    logger.info("   GET  /search?q=<query>&force_refresh=<bool>")
    logger.info("   POST /search (JSON body)")
    logger.info("   GET  /history?limit=<int>")
    logger.info("   GET  /cached/<id>")
    logger.info("   GET  /status")
    
    # Start the Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)
