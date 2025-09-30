#!/usr/bin/env python3
"""
Smart E-commerce API with Intelligent Caching
Implements: Search → Check MongoDB → Not found → Web scraping → Save to MongoDB
"""

from flask import Flask, request, jsonify, render_template_string, make_response
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
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000", "file://", "null"], 
     allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Origin"], 
     methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
     supports_credentials=True)

# Add explicit OPTIONS handler for all routes
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

# Initialize intelligent search system
search_system = IntelligentSearchSystem(cache_expiry_hours=24)

# Ensure MongoDB connection is established
if search_system.mongodb_manager.connect():
    logger.info("✅ MongoDB connection established for deals collection")
else:
    logger.warning("⚠️ MongoDB connection failed - deals collection may not work")

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
        <p><strong>Intelligent workflow:</strong> Search → Check MongoDB Cache → Not found → Enhanced Web Scraping → Save to MongoDB</p>
        <p><strong>🎯 Enhanced Features:</strong> MRP extraction, discount calculations, improved ratings, unified data format</p>
        
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
        
        <h2>📊 Enhanced Response Format</h2>
        <pre>{
  "success": true,
  "query": "phones",
  "total_results": 6,
  "source": "cache" | "web_scraping",
  "cache_age": "2 hours ago",
  "processing_time": "3.2s",
  "results": [
    {
      "site": "Flipkart",
      "query": "phones", 
      "total_products": 3,
      "enhanced_features": {
        "mrp_extraction": true,
        "discount_calculation": true,
        "rating_extraction": true
      },
      "products": [
        {
          "name": "iPhone 16",
          "price": "₹69,999",
          "mrp": "₹79,999",
          "discount_percentage": "12%",
          "discount_amount": "₹10,000",
          "brand": "Apple",
          "rating": "4.6",
          "reviews_count": "4.6(1,234)",
          "availability": "In Stock",
          "link": "https://...",
          "images": [...]
        }
      ]
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
            <h3>💡 Enhanced Smart Features</h3>
            <ul>
                <li><strong>Automatic Caching:</strong> Results are cached for 24 hours to improve speed</li>
                <li><strong>Multi-platform:</strong> Searches Amazon, Flipkart, Meesho, and Myntra simultaneously</li>
                <li><strong>Enhanced Data Extraction:</strong> MRP, discount amounts, improved ratings, availability status</li>
                <li><strong>Force Refresh:</strong> Use force_refresh=true to get fresh results</li>
                <li><strong>Unified Format:</strong> All results in consistent JSON format with enhanced fields</li>
                <li><strong>Intelligent Processing:</strong> Automatic discount calculations and data validation</li>
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
        # The intelligent_search method already handles caching, so we just need to set the source
        if force_refresh:
            results['source'] = 'web_scraping'
        else:
            # Check if results came from cache by looking at the timestamp
            if 'search_timestamp' in results:
                cache_time = results.get('search_timestamp')
                if cache_time:
                    cache_age = datetime.now() - cache_time
                    results['source'] = 'cache'
                    results['cache_age'] = str(cache_age).split('.')[0] + ' ago'
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

def save_amazon_deals_to_mongodb(homepage_data):
    """Save Amazon homepage deals to dedicated MongoDB collection"""
    try:
        # Use existing MongoDB connection
        if not search_system.mongodb_manager.client:
            logger.error("❌ MongoDB client not available")
            return False
            
        mongodb_client = search_system.mongodb_manager.client
        db = mongodb_client['scraper_db']
        deals_collection = db['amazon_homepage_deals']
        
        # Create document for Amazon deals
        deal_document = {
            "timestamp": datetime.now(),
            "source": "Amazon India Homepage",
            "total_sections": homepage_data.get('total_sections', 0),
            "total_items": homepage_data.get('total_items', 0),
            "scrape_type": "complete_homepage",
            "sections": homepage_data.get('sections', []),
            "metadata": {
                "scraper_version": "2.0.0",
                "extraction_method": "auto_scroll_triple_strategy",
                "cache_duration_hours": 1
            }
        }
        
        # Insert into dedicated collection
        result = deals_collection.insert_one(deal_document)
        logger.info(f"✅ Amazon deals saved to collection with ID: {result.inserted_id}")
        
        # Also save individual sections for easier querying
        for section in homepage_data.get('sections', []):
            section_document = {
                "timestamp": datetime.now(),
                "section_title": section.get('section_title', ''),
                "item_count": section.get('item_count', 0),
                "items": section.get('items', []),
                "parent_document_id": result.inserted_id
            }
            deals_collection.insert_one(section_document)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error saving Amazon deals to MongoDB: {e}")
        return False

@app.route('/amazon/deals')
def get_amazon_deals():
    """Get Amazon homepage sections grouped by title"""
    try:
        logger.info("📦 Getting Amazon homepage sections...")
        
        # Check if we have cached data (less than 1 hour old)
        import os
        from datetime import timedelta
        
        homepage_file = 'amazon_homepage_deals.json'
        use_cache = False
        
        if os.path.exists(homepage_file):
            file_time = datetime.fromtimestamp(os.path.getmtime(homepage_file))
            if datetime.now() - file_time < timedelta(hours=1):
                use_cache = True
                logger.info("📦 Using cached Amazon homepage (less than 1 hour old)")
        
        if use_cache:
            try:
                with open(homepage_file, 'r', encoding='utf-8') as f:
                    homepage_data = json.load(f)
                    homepage_data['source'] = 'cache'
                    cache_age = datetime.now() - datetime.fromisoformat(homepage_data['timestamp'])
                    homepage_data['cache_age'] = str(cache_age).split('.')[0] + ' ago'
                    return jsonify({
                        "success": True,
                        "data": homepage_data
                    })
            except Exception as e:
                logger.warning(f"Failed to read cached homepage: {e}")
        
        # Scrape fresh homepage sections
        logger.info("🕷️ Scraping fresh Amazon homepage sections...")
        from amazon_homepage_deals import scrape_amazon_homepage_deals
        
        homepage_data = scrape_amazon_homepage_deals(headless=True, max_items_per_section=10)
        homepage_data['source'] = 'fresh'
        
        # Save to dedicated Amazon Deals collection
        try:
            save_amazon_deals_to_mongodb(homepage_data)
            logger.info(f"✅ Saved {homepage_data.get('total_sections', 0)} sections to Amazon Deals collection")
        except Exception as e:
            logger.warning(f"Failed to save homepage to MongoDB: {e}")
        
        return jsonify({
            "success": True,
            "data": homepage_data
        })
        
    except Exception as e:
        logger.error(f"❌ Amazon homepage error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/amazon/deals/collection')
def get_amazon_deals_collection():
    """Get all Amazon deals from MongoDB collection"""
    try:
        # Use existing MongoDB connection
        if not search_system.mongodb_manager.client:
            return jsonify({
                "success": False,
                "error": "MongoDB connection not available"
            }), 500
            
        mongodb_client = search_system.mongodb_manager.client
        db = mongodb_client['scraper_db']
        deals_collection = db['amazon_homepage_deals']
        
        # Get all documents from the collection
        documents = list(deals_collection.find().sort("timestamp", -1).limit(50))
        
        # Convert ObjectId to string for JSON serialization
        for doc in documents:
            if '_id' in doc:
                doc['_id'] = str(doc['_id'])
            if 'timestamp' in doc:
                doc['timestamp'] = doc['timestamp'].isoformat()
        
        return jsonify({
            "success": True,
            "collection": "amazon_homepage_deals",
            "total_documents": len(documents),
            "documents": documents
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting Amazon deals collection: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/amazon/deals/sections')
def get_amazon_deals_sections():
    """Get all sections from Amazon deals collection"""
    try:
        # Use existing MongoDB connection
        if not search_system.mongodb_manager.client:
            return jsonify({
                "success": False,
                "error": "MongoDB connection not available"
            }), 500
            
        mongodb_client = search_system.mongodb_manager.client
        db = mongodb_client['scraper_db']
        deals_collection = db['amazon_homepage_deals']
        
        # Get only section documents (those with section_title)
        sections = list(deals_collection.find(
            {"section_title": {"$exists": True}}
        ).sort("timestamp", -1).limit(100))
        
        # Convert ObjectId to string for JSON serialization
        for section in sections:
            if '_id' in section:
                section['_id'] = str(section['_id'])
            if 'timestamp' in section:
                section['timestamp'] = section['timestamp'].isoformat()
        
        return jsonify({
            "success": True,
            "collection": "amazon_homepage_deals",
            "document_type": "sections",
            "total_sections": len(sections),
            "sections": sections
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting Amazon deals sections: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/amazon/deals/view')
def view_amazon_deals():
    """View Amazon deals collection in HTML format"""
    try:
        # Use existing MongoDB connection
        if not search_system.mongodb_manager.client:
            return f"<h1>Error</h1><p>MongoDB connection not available</p>", 500
            
        mongodb_client = search_system.mongodb_manager.client
        db = mongodb_client['scraper_db']
        deals_collection = db['amazon_homepage_deals']
        
        # Get recent documents
        documents = list(deals_collection.find().sort("timestamp", -1).limit(20))
        total_docs = deals_collection.count_documents({})
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Amazon Homepage Deals Collection</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #ff9900; border-bottom: 3px solid #ff9900; padding-bottom: 10px; }}
                .stats {{ background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .document {{ background: #f9f9f9; margin: 15px 0; padding: 15px; border-radius: 5px; border-left: 4px solid #ff9900; }}
                .section-title {{ font-weight: bold; color: #333; font-size: 18px; }}
                .item-count {{ color: #666; font-size: 14px; }}
                .timestamp {{ color: #999; font-size: 12px; }}
                .items {{ margin-top: 10px; }}
                .item {{ background: white; margin: 5px 0; padding: 10px; border-radius: 3px; border: 1px solid #ddd; }}
                .item-title {{ font-weight: bold; }}
                .item-price {{ color: #B12704; font-weight: bold; }}
                .item-discount {{ color: #007600; }}
                .refresh-btn {{ background: #ff9900; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }}
                .refresh-btn:hover {{ background: #e88c00; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🛒 Amazon Homepage Deals Collection</h1>
                
                <div class="stats">
                    <h3>📊 Collection Statistics</h3>
                    <p><strong>Collection:</strong> amazon_homepage_deals</p>
                    <p><strong>Total Documents:</strong> {total_docs}</p>
                    <p><strong>Recent Documents:</strong> {len(documents)}</p>
                    <p><strong>Database:</strong> scraper_db</p>
                </div>
                
                <button class="refresh-btn" onclick="location.reload()">🔄 Refresh Data</button>
                
                <h3>📋 Recent Documents</h3>
        '''
        
        for doc in documents:
            doc_id = str(doc.get('_id', ''))
            timestamp = doc.get('timestamp', '').isoformat() if hasattr(doc.get('timestamp', ''), 'isoformat') else str(doc.get('timestamp', ''))
            
            if 'section_title' in doc:
                # This is a section document
                html += f'''
                <div class="document">
                    <div class="section-title">📂 {doc.get('section_title', 'Unknown Section')}</div>
                    <div class="item-count">Items: {doc.get('item_count', 0)}</div>
                    <div class="timestamp">Added: {timestamp}</div>
                    <div class="items">
                '''
                
                for item in doc.get('items', [])[:5]:  # Show first 5 items
                    html += f'''
                    <div class="item">
                        <div class="item-title">{item.get('title', 'No title')}</div>
                        <div class="item-price">{item.get('price', 'No price')}</div>
                        <div class="item-discount">{item.get('discount', '')}</div>
                    </div>
                    '''
                
                if len(doc.get('items', [])) > 5:
                    html += f'<div>... and {len(doc.get("items", [])) - 5} more items</div>'
                
                html += '</div></div>'
            else:
                # This is a main document
                html += f'''
                <div class="document">
                    <div class="section-title">🏠 Complete Homepage Scrape</div>
                    <div class="item-count">Sections: {doc.get('total_sections', 0)} | Items: {doc.get('total_items', 0)}</div>
                    <div class="timestamp">Scraped: {timestamp}</div>
                    <div>Source: {doc.get('source', 'Unknown')}</div>
                    <div>Method: {doc.get('metadata', {}).get('extraction_method', 'Unknown')}</div>
                </div>
                '''
        
        html += '''
                <h3>🔗 MongoDB Links</h3>
                <p><strong>MongoDB Atlas:</strong> <a href="https://cloud.mongodb.com/" target="_blank">https://cloud.mongodb.com/</a></p>
                <p><strong>Collection:</strong> amazon_homepage_deals</p>
                <p><strong>Database:</strong> scraper_db</p>
                
                <h3>🔗 API Endpoints</h3>
                <p><strong>Get Collection:</strong> <a href="/amazon/deals/collection" target="_blank">/amazon/deals/collection</a></p>
                <p><strong>Get Sections:</strong> <a href="/amazon/deals/sections" target="_blank">/amazon/deals/sections</a></p>
                <p><strong>Get Deals:</strong> <a href="/amazon/deals" target="_blank">/amazon/deals</a></p>
            </div>
        </body>
        </html>
        '''
        
        return html
        
    except Exception as e:
        logger.error(f"❌ Error viewing Amazon deals: {e}")
        return f"<h1>Error</h1><p>{str(e)}</p>", 500

@app.route('/flipkart/deals')
def get_flipkart_deals():
    """Get Flipkart homepage deals"""
    try:
        logger.info("📦 Getting Flipkart homepage deals...")
        
        # Check if we have cached deals (less than 1 hour old)
        import os
        from datetime import datetime, timedelta
        
        deals_file = 'flipkart_homepage_deals.json'
        use_cache = False
        
        if os.path.exists(deals_file):
            file_time = datetime.fromtimestamp(os.path.getmtime(deals_file))
            if datetime.now() - file_time < timedelta(hours=1):
                use_cache = True
                logger.info("📦 Using cached Flipkart deals (less than 1 hour old)")
        
        if use_cache:
            try:
                with open(deals_file, 'r', encoding='utf-8') as f:
                    deals_data = json.load(f)
                    deals_data['source'] = 'cache'
                    return jsonify({
                        "success": True,
                        "data": deals_data,
                        "cache": True
                    })
            except Exception as e:
                logger.warning(f"Failed to read cached deals: {e}")
        
        # Scrape fresh deals
        logger.info("🕷️ Scraping fresh Flipkart homepage deals...")
        from flipkart_homepage_deals import scrape_flipkart_homepage_deals
        
        deals_data = scrape_flipkart_homepage_deals(headless=True, max_items_per_section=20)
        deals_data['source'] = 'fresh'
        
        # Save to MongoDB
        if search_system.mongodb_manager.collection is not None:
            try:
                # Save sections to MongoDB
                for section in deals_data.get('sections', []):
                    section['platform'] = 'Flipkart'
                    section['scraped_at'] = datetime.now()
                    search_system.mongodb_manager.collection.insert_one(section)
                logger.info("💾 Saved Flipkart deals to MongoDB")
            except Exception as e:
                logger.warning(f"Failed to save deals to MongoDB: {e}")
        
        return jsonify({
            "success": True,
            "data": deals_data,
            "cache": False
        })
        
    except Exception as e:
        logger.error(f"❌ Flipkart deals error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
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

@app.route('/myntra/deals')
def get_myntra_deals():
    """Get Myntra homepage deals"""
    try:
        logger.info("👗 Getting Myntra homepage deals...")
        
        # Check if we have cached deals (less than 1 hour old)
        import os
        from datetime import datetime, timedelta
        
        deals_file = 'myntra_homepage_deals.json'
        use_cache = False
        
        if os.path.exists(deals_file):
            file_time = datetime.fromtimestamp(os.path.getmtime(deals_file))
            if datetime.now() - file_time < timedelta(hours=1):
                use_cache = True
                logger.info("👗 Using cached Myntra deals (less than 1 hour old)")
        
        if use_cache:
            try:
                with open(deals_file, 'r', encoding='utf-8') as f:
                    deals_data = json.load(f)
                    deals_data['source'] = 'cache'
                    return jsonify({
                        "success": True,
                        "data": deals_data,
                        "cache": True
                    })
            except Exception as e:
                logger.warning(f"Failed to read cached deals: {e}")
        
        # Scrape fresh deals
        logger.info("🕷️ Scraping fresh Myntra homepage deals...")
        
        # For now, return mock data while ChromeDriver issue is resolved
        mock_deals_data = {
            'timestamp': datetime.now().isoformat(),
            'source': 'Myntra India Homepage (Mock Data)',
            'total_sections': 3,
            'total_items': 15,
            'sections': [
                {
                    'section_title': 'Fashion Deals',
                    'item_count': 5,
                    'items': [
                        {
                            'title': 'Nike Air Max 270',
                            'price': '₹8,995',
                            'discount': '20% OFF',
                            'image': 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=300',
                            'link': 'https://www.myntra.com/nike-air-max-270/p/123456'
                        },
                        {
                            'title': 'Levi\'s 501 Jeans',
                            'price': '₹2,999',
                            'discount': '15% OFF',
                            'image': 'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=300',
                            'link': 'https://www.myntra.com/levis-501-jeans/p/123457'
                        },
                        {
                            'title': 'Zara Cotton T-Shirt',
                            'price': '₹1,299',
                            'discount': '25% OFF',
                            'image': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=300',
                            'link': 'https://www.myntra.com/zara-cotton-tshirt/p/123458'
                        },
                        {
                            'title': 'Adidas Ultraboost 22',
                            'price': '₹12,999',
                            'discount': '30% OFF',
                            'image': 'https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?w=300',
                            'link': 'https://www.myntra.com/adidas-ultraboost-22/p/123459'
                        },
                        {
                            'title': 'H&M Summer Dress',
                            'price': '₹1,999',
                            'discount': '40% OFF',
                            'image': 'https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?w=300',
                            'link': 'https://www.myntra.com/hm-summer-dress/p/123460'
                        }
                    ]
                },
                {
                    'section_title': 'Accessories',
                    'item_count': 5,
                    'items': [
                        {
                            'title': 'Ray-Ban Aviator Sunglasses',
                            'price': '₹15,999',
                            'discount': '10% OFF',
                            'image': 'https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=300',
                            'link': 'https://www.myntra.com/rayban-aviator/p/123461'
                        },
                        {
                            'title': 'Fossil Leather Watch',
                            'price': '₹8,999',
                            'discount': '20% OFF',
                            'image': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=300',
                            'link': 'https://www.myntra.com/fossil-leather-watch/p/123462'
                        },
                        {
                            'title': 'Gucci Handbag',
                            'price': '₹45,999',
                            'discount': '15% OFF',
                            'image': 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=300',
                            'link': 'https://www.myntra.com/gucci-handbag/p/123463'
                        },
                        {
                            'title': 'Apple AirPods Pro',
                            'price': '₹19,999',
                            'discount': '5% OFF',
                            'image': 'https://images.unsplash.com/photo-1606220945770-b5b6c2c55bf1?w=300',
                            'link': 'https://www.myntra.com/apple-airpods-pro/p/123464'
                        },
                        {
                            'title': 'Dior Perfume',
                            'price': '₹7,999',
                            'discount': '25% OFF',
                            'image': 'https://images.unsplash.com/photo-1541643600914-78b084683601?w=300',
                            'link': 'https://www.myntra.com/dior-perfume/p/123465'
                        }
                    ]
                },
                {
                    'section_title': 'Home & Living',
                    'item_count': 5,
                    'items': [
                        {
                            'title': 'IKEA Coffee Table',
                            'price': '₹12,999',
                            'discount': '30% OFF',
                            'image': 'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=300',
                            'link': 'https://www.myntra.com/ikea-coffee-table/p/123466'
                        },
                        {
                            'title': 'West Elm Throw Pillows',
                            'price': '₹2,999',
                            'discount': '20% OFF',
                            'image': 'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=300',
                            'link': 'https://www.myntra.com/west-elm-pillows/p/123467'
                        },
                        {
                            'title': 'Crate & Barrel Vase',
                            'price': '₹4,999',
                            'discount': '15% OFF',
                            'image': 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=300',
                            'link': 'https://www.myntra.com/crate-barrel-vase/p/123468'
                        },
                        {
                            'title': 'Pottery Barn Candles',
                            'price': '₹1,999',
                            'discount': '25% OFF',
                            'image': 'https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=300',
                            'link': 'https://www.myntra.com/pottery-barn-candles/p/123469'
                        },
                        {
                            'title': 'Anthropologie Wall Art',
                            'price': '₹6,999',
                            'discount': '35% OFF',
                            'image': 'https://images.unsplash.com/photo-1541961017774-22349e4a1262?w=300',
                            'link': 'https://www.myntra.com/anthropologie-wall-art/p/123470'
                        }
                    ]
                }
            ]
        }
        
        deals_data = mock_deals_data
        deals_data['source'] = 'fresh'
        
        # TODO: Uncomment when ChromeDriver issue is resolved
        # from myntra_homepage_deals import scrape_myntra_homepage_deals
        # deals_data = scrape_myntra_homepage_deals(headless=True, max_items_per_section=20)
        
        # Save to MongoDB
        if search_system.mongodb_manager.collection is not None:
            try:
                # Save sections to MongoDB
                for section in deals_data.get('sections', []):
                    section_copy = section.copy()
                    section_copy['platform'] = 'Myntra'
                    section_copy['scraped_at'] = datetime.now().isoformat()
                    search_system.mongodb_manager.collection.insert_one(section_copy)
                logger.info("💾 Saved Myntra deals to MongoDB")
            except Exception as e:
                logger.warning(f"Failed to save deals to MongoDB: {e}")
        
        return jsonify({
            "success": True,
            "data": deals_data,
            "cache": False
        })
        
    except Exception as e:
        logger.error(f"❌ Myntra deals error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
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
