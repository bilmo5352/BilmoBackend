# Amazon Homepage Deals Feature

## Overview
This feature scrapes deals and offers from the Amazon India homepage and displays them when users click the Amazon button in the frontend.

## Architecture

### Backend Components

#### 1. `amazon_homepage_deals.py`
- Scrapes Amazon India homepage for deals
- Extracts: title, price, discount, images, links, deal types
- Saves results to JSON file
- Handles caching (1-hour expiry)

#### 2. `smart_api.py` - New Endpoint
```python
@app.route('/amazon/deals')
def get_amazon_deals():
    """Get Amazon homepage deals"""
```

**Features:**
- ✅ Automatic caching (1 hour)
- ✅ MongoDB integration
- ✅ Error handling
- ✅ Fresh scraping on cache miss

### Frontend Components

#### 1. `frontend/script.js` - Updated Functions

**New Functions:**
- `loadAmazonDeals()` - Fetches deals from API
- `displayAmazonDeals()` - Renders deals in UI
- `createDealCard()` - Creates deal card HTML

**Modified:**
- Platform button click handler - triggers deal loading when Amazon is clicked without search query

#### 2. User Experience
1. User clicks "Amazon" platform button
2. If no search query entered → Show Amazon homepage deals
3. If search query exists → Perform normal search

## Usage

### Running the Backend
```bash
# Start the smart API
python smart_api.py
```

### Using the Frontend
1. Open `frontend/index.html` in browser
2. Click the "Amazon" button (without entering search)
3. View Amazon homepage deals

### Direct API Access
```bash
# Get Amazon deals
curl http://localhost:5000/amazon/deals

# Response format:
{
  "success": true,
  "data": {
    "timestamp": "2025-09-30T...",
    "source": "cache" | "fresh",
    "total_deals": 20,
    "deals": [
      {
        "title": "Product Name",
        "price": "₹1,999",
        "discount": "50% off",
        "image": "https://...",
        "link": "https://...",
        "deal_type": "Today's Deal"
      }
    ]
  }
}
```

### Testing
```bash
# Run test suite
python test_amazon_deals.py
```

## Data Flow

```
1. User clicks Amazon button (no search query)
   ↓
2. Frontend calls: GET /amazon/deals
   ↓
3. Backend checks cache (< 1 hour old?)
   ├─ Yes → Return cached deals
   └─ No  → Scrape fresh deals
              ↓
              Save to JSON file
              ↓
              Save to MongoDB
              ↓
              Return fresh deals
   ↓
4. Frontend displays deals in grid
```

## Caching Strategy

### File Cache
- Location: `amazon_homepage_deals.json`
- Expiry: 1 hour
- Purpose: Fast response times

### MongoDB Cache
- Collection: Based on `IntelligentSearchSystem` config
- Query: `homepage_deals`
- Platform: `Amazon`

## Features

### Extracted Data
- ✅ Product title
- ✅ Current price
- ✅ Discount percentage
- ✅ Product image
- ✅ Product link
- ✅ Deal type/badge

### Smart Features
- ✅ Automatic caching (1 hour)
- ✅ Duplicate removal
- ✅ Image optimization
- ✅ Error handling
- ✅ MongoDB integration
- ✅ Cache age display

## Configuration

### Scraper Settings
```python
# In amazon_homepage_deals.py
max_deals = 20  # Maximum deals to scrape
headless = True  # Run browser in headless mode
```

### Cache Expiry
```python
# In smart_api.py - get_amazon_deals()
timedelta(hours=1)  # Cache expiry time
```

## Docker Deployment

### Dockerfile Updates
Added to COPY instructions:
- `amazon_homepage_deals.py`
- `smart_api.py`
- `intelligent_search_system.py`
- `unified_mongodb_manager.py`

Changed CMD to:
```dockerfile
CMD ["python", "smart_api.py"]
```

### Building and Running
```bash
# Build Docker image
docker-compose build

# Run container
docker-compose up -d

# Access API
curl http://localhost:5000/amazon/deals
```

## Troubleshooting

### No Deals Found
**Possible causes:**
1. Amazon structure changed
2. Network/firewall issues
3. ChromeDriver issues

**Solution:**
- Check logs in console
- Update selectors in `amazon_homepage_deals.py`
- Verify ChromeDriver installation

### Cache Not Working
**Check:**
1. File permissions on `amazon_homepage_deals.json`
2. Timestamp format in JSON
3. System clock accuracy

### Frontend Not Loading Deals
**Verify:**
1. API is running on port 5000
2. CORS is enabled
3. Browser console for errors
4. Network tab for API calls

## Performance

### Metrics
- **First load (fresh scrape):** 15-30 seconds
- **Cached response:** < 1 second
- **Deals count:** Up to 20 deals
- **Cache duration:** 1 hour

### Optimization Tips
1. Increase cache duration for less frequent updates
2. Reduce max_deals for faster scraping
3. Use headless mode for better performance

## Future Enhancements

### Potential Features
- [ ] Multiple deal categories (Today's Deals, Lightning Deals, etc.)
- [ ] Price tracking and alerts
- [ ] Deal filtering by category/price
- [ ] Personalized recommendations
- [ ] Deal expiry tracking
- [ ] Comparison with other platforms

### API Improvements
- [ ] Pagination for large deal sets
- [ ] Deal categories endpoint
- [ ] Search within deals
- [ ] Deal history tracking

## API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/amazon/deals` | GET | Get Amazon homepage deals |
| `/search` | GET/POST | Search products (existing) |
| `/status` | GET | API status check |
| `/history` | GET | Search history |

## Files Modified/Created

### Created
- ✅ `amazon_homepage_deals.py` - Scraper
- ✅ `test_amazon_deals.py` - Test suite
- ✅ `AMAZON_DEALS_FEATURE.md` - Documentation

### Modified
- ✅ `smart_api.py` - Added `/amazon/deals` endpoint
- ✅ `frontend/script.js` - Added deal loading functions
- ✅ `Dockerfile` - Updated for smart_api.py and new files

## Support

For issues or questions:
1. Check logs: `python smart_api.py` output
2. Run test suite: `python test_amazon_deals.py`
3. Verify API: `curl http://localhost:5000/status`

---

**Last Updated:** September 30, 2025
**Version:** 1.0.0
**Author:** E-commerce Scraper Team

