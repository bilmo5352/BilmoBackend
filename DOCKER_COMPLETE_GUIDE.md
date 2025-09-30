# BILMO DOCKER DEPLOYMENT GUIDE

## Complete Morning Fixes Included

This Docker deployment includes all the fixes implemented this morning:

### ✅ **Myntra Rating Extraction Fix**
- Enhanced Myntra scraper to visit individual product pages
- Comprehensive rating extraction using CSS selectors, regex patterns, and page source analysis
- Handles dynamic content and stale element references
- Successfully extracts ratings (e.g., "1.5") from product detail pages

### ✅ **Amazon Rating Improvements**
- Fixed comprehensive rating extraction using aria-label attributes
- Enhanced CSS selectors for star ratings
- Separated review count from star ratings
- Improved fallback methods for rating detection

### ✅ **Flipkart Enhanced Scraping**
- Fixed MRP parsing issues (removed discount percentages from MRP)
- Enhanced discount calculation and validation
- Improved product title extraction using image alt text
- Better category classification for laptops and electronics

### ✅ **Meesho Image Handling**
- Enhanced image alt text extraction
- Improved product title prioritization
- Better image URL handling with CDN support

### ✅ **Frontend Cache Busting**
- Added `force_refresh=true` to all search requests
- Implemented timestamp-based cache busting
- Added cache-busting headers to prevent browser caching

### ✅ **MongoDB Integration**
- Complete caching system with MongoDB Atlas
- Unified search result storage
- Intelligent cache management

## Quick Deployment

### Option 1: Complete Fresh Deployment
```bash
docker_complete_deploy.bat
```

### Option 2: Reset and Redeploy
```bash
docker_reset_and_deploy.bat
```

### Option 3: Manual Deployment
```bash
# Build and start
docker-compose build --no-cache bilmo-api
docker-compose up -d bilmo-api

# Test
curl http://localhost:5000/status
```

## API Endpoints

- **Home:** http://localhost:5000
- **Search:** http://localhost:5000/search?q=phones
- **Status:** http://localhost:5000/status
- **History:** http://localhost:5000/history

## Features Verification

After deployment, test these features:

1. **Myntra Ratings:** Search for "tshirt" and verify Myntra products show ratings
2. **Amazon Ratings:** Search for "phones" and verify Amazon shows star ratings
3. **Flipkart MRP:** Search for "laptop" and verify MRP/discount parsing
4. **Meesho Images:** Verify all Meesho products show images
5. **Cache Busting:** Verify fresh results with `force_refresh=true`

## Container Management

```bash
# View logs
docker-compose logs -f bilmo-api

# Stop container
docker-compose down

# Restart container
docker-compose restart bilmo-api

# Check status
docker-compose ps
```

## Troubleshooting

1. **Docker not starting:** Ensure Docker Desktop is running
2. **Port conflicts:** Change port mapping in docker-compose.yml
3. **Memory issues:** Increase Docker Desktop memory allocation
4. **Chrome issues:** Container includes all Chrome dependencies
5. **API not responding:** Check logs with `docker-compose logs bilmo-api`

## Development

To rebuild after code changes:
```bash
docker-compose build --no-cache bilmo-api
docker-compose up -d bilmo-api
```

## MongoDB (Optional)

To run with MongoDB caching:
```bash
docker-compose --profile mongodb up -d
```

## Container Specifications

- **Base Image:** Python 3.11-slim
- **Chrome:** Latest stable version with all dependencies
- **Memory:** 2GB shared memory for Chrome
- **Security:** Non-root user with proper capabilities
- **Persistence:** HTML files and logs mounted as volumes
- **Health Checks:** Automatic monitoring every 30 seconds
