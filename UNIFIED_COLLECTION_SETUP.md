# 🗄️ Unified Platform Deals Collection - Complete Setup

## ✅ All Platforms Now Store in One Collection!

All e-commerce platform deals (Amazon, Myntra, Flipkart, etc.) are now stored in the **unified `amazon_homepage_deals` collection**.

---

## 📊 Collection Details

### Database & Collection Info
- **Database**: `scraper_db`
- **Collection**: `amazon_homepage_deals` (Unified for all platforms)
- **MongoDB Atlas**: `https://cloud.mongodb.com/`
- **Connection**: `mongodb+srv://hrithick:hrithick@bilmo.jmeclfh.mongodb.net/`

---

## 🎯 Unified Storage Structure

### Main Deal Document (All Platforms)
```json
{
  "_id": "ObjectId",
  "timestamp": "2025-10-01T...",
  "platform": "Amazon|Myntra|Flipkart",  // 🔑 KEY DIFFERENTIATOR
  "source": "Platform India Homepage",
  "total_sections": 25,
  "total_items": 250,
  "scrape_type": "complete_homepage",
  "sections": [...],
  "metadata": {
    "scraper_version": "2.0.0",
    "extraction_method": "auto_scroll_triple_strategy",
    "cache_duration_hours": 1
  }
}
```

### Section Document (All Platforms)
```json
{
  "_id": "ObjectId",
  "timestamp": "2025-10-01T...",
  "platform": "Amazon|Myntra|Flipkart",  // 🔑 KEY DIFFERENTIATOR
  "section_title": "Today's Deals",
  "item_count": 10,
  "items": [
    {
      "title": "Product Name",
      "price": "₹1,999",
      "discount": "50% off",
      "image": "https://...",
      "link": "https://...",
      "platform": "Amazon|Myntra|Flipkart"  // 🔑 Item-level identifier
    }
  ],
  "parent_document_id": "ObjectId"
}
```

---

## 🔍 How to Query Each Platform

### Query Amazon Deals
```javascript
// MongoDB Query
db.amazon_homepage_deals.find({ "platform": "Amazon" })
```

```python
# Python Query
deals_collection = db['amazon_homepage_deals']
amazon_deals = deals_collection.find({"platform": "Amazon"})
```

### Query Myntra Deals
```javascript
// MongoDB Query
db.amazon_homepage_deals.find({ "platform": "Myntra" })
```

```python
# Python Query
deals_collection = db['amazon_homepage_deals']
myntra_deals = deals_collection.find({"platform": "Myntra"})
```

### Query Flipkart Deals
```javascript
// MongoDB Query
db.amazon_homepage_deals.find({ "platform": "Flipkart" })
```

```python
# Python Query
deals_collection = db['amazon_homepage_deals']
flipkart_deals = deals_collection.find({"platform": "Flipkart"})
```

### Query ALL Platform Deals
```javascript
// MongoDB Query - Get all platforms
db.amazon_homepage_deals.find({})

// Get latest from each platform
db.amazon_homepage_deals.aggregate([
  { $sort: { timestamp: -1 } },
  { $group: {
      _id: "$platform",
      latest: { $first: "$$ROOT" }
    }
  }
])
```

---

## 📊 Platform Distribution

| Platform  | Platform Field | Collection              | Status |
|-----------|---------------|-------------------------|--------|
| Amazon    | `"Amazon"`    | `amazon_homepage_deals` | ✅     |
| Myntra    | `"Myntra"`    | `amazon_homepage_deals` | ✅     |
| Flipkart  | `"Flipkart"`  | `amazon_homepage_deals` | ✅     |

---

## 🚀 API Endpoints

### Amazon Deals
```bash
# Scrape and save Amazon deals
curl http://localhost:5000/amazon/deals

# Get Amazon collection data (all platforms)
curl http://localhost:5000/amazon/deals/collection
```

### Myntra Deals
```bash
# Scrape and save Myntra deals
curl http://localhost:5000/myntra/deals
```

### Flipkart Deals
```bash
# Scrape and save Flipkart deals
curl http://localhost:5000/flipkart/deals
```

---

## 🔧 Differentiation Logic

### 1. **Platform Field** (Document Level)
Every document has a `platform` field:
- `"Amazon"` for Amazon deals
- `"Myntra"` for Myntra deals
- `"Flipkart"` for Flipkart deals

### 2. **Platform Field** (Item Level)
Every item within sections has its own `platform` field for granular filtering.

### 3. **Source Field**
- Amazon: `"Amazon India Homepage"`
- Myntra: `"Myntra India Homepage"`
- Flipkart: `"Flipkart India Homepage"`

---

## 📈 Query Examples

### Count Deals by Platform
```python
from pymongo import MongoClient

client = MongoClient("mongodb+srv://hrithick:hrithick@bilmo.jmeclfh.mongodb.net/")
db = client['scraper_db']
collection = db['amazon_homepage_deals']

# Count by platform
amazon_count = collection.count_documents({"platform": "Amazon"})
myntra_count = collection.count_documents({"platform": "Myntra"})
flipkart_count = collection.count_documents({"platform": "Flipkart"})

print(f"Amazon: {amazon_count}")
print(f"Myntra: {myntra_count}")
print(f"Flipkart: {flipkart_count}")
```

### Get Latest Deals from Each Platform
```python
# Get latest Amazon deals
latest_amazon = collection.find_one(
    {"platform": "Amazon", "scrape_type": "complete_homepage"},
    sort=[("timestamp", -1)]
)

# Get latest Myntra deals
latest_myntra = collection.find_one(
    {"platform": "Myntra", "scrape_type": "complete_homepage"},
    sort=[("timestamp", -1)]
)

# Get latest Flipkart deals
latest_flipkart = collection.find_one(
    {"platform": "Flipkart", "scrape_type": "complete_homepage"},
    sort=[("timestamp", -1)]
)
```

### Get All Deals from Last 24 Hours
```python
from datetime import datetime, timedelta

yesterday = datetime.now() - timedelta(hours=24)

recent_deals = collection.find({
    "timestamp": {"$gte": yesterday}
})

# Group by platform
for deal in recent_deals:
    platform = deal.get('platform')
    sections = deal.get('total_sections', 0)
    print(f"{platform}: {sections} sections")
```

---

## ✅ Benefits of Unified Collection

1. **Single Source of Truth**: All platform deals in one place
2. **Easy Comparison**: Compare deals across platforms easily
3. **Unified Queries**: Query all platforms at once
4. **Better Organization**: Consistent structure across platforms
5. **Platform Field**: Clear differentiation with `platform` field
6. **No Data Mixing**: Each document clearly tagged with platform

---

## 🛠️ Verification Script

Run this to verify all platforms are storing correctly:

```python
from pymongo import MongoClient

client = MongoClient("mongodb+srv://hrithick:hrithick@bilmo.jmeclfh.mongodb.net/")
db = client['scraper_db']
collection = db['amazon_homepage_deals']

# Get platform distribution
pipeline = [
    {"$group": {
        "_id": "$platform",
        "count": {"$sum": 1},
        "latest": {"$max": "$timestamp"}
    }},
    {"$sort": {"_id": 1}}
]

results = list(collection.aggregate(pipeline))

print("\n📊 Platform Distribution in Unified Collection:")
print("="*50)
for result in results:
    platform = result['_id']
    count = result['count']
    latest = result['latest']
    print(f"{platform:15} {count:5} documents (Latest: {latest})")
print("="*50)
```

---

## 📝 Summary

✅ **All platforms** now store in `amazon_homepage_deals` collection  
✅ **Platform field** differentiates between Amazon, Myntra, Flipkart  
✅ **Item-level platform** field for granular filtering  
✅ **Unified structure** across all platforms  
✅ **Easy querying** with platform filters  
✅ **No confusion** - clear separation via platform field  

---

## 🔗 Access Methods

### 1. MongoDB Atlas Web Interface
```
https://cloud.mongodb.com/
```
- Navigate to `bilmo` cluster → `scraper_db` → `amazon_homepage_deals`
- Filter by `platform` field to see specific platform deals

### 2. MongoDB Compass
```
mongodb+srv://hrithick:hrithick@bilmo.jmeclfh.mongodb.net/?retryWrites=true&w=majority&appName=bilmo
```
- Use filter: `{"platform": "Amazon"}` for Amazon only
- Use filter: `{"platform": "Myntra"}` for Myntra only
- Use filter: `{"platform": "Flipkart"}` for Flipkart only

### 3. API Endpoints
```bash
# Get all deals from collection
curl http://localhost:5000/amazon/deals/collection

# Individual platform endpoints still work
curl http://localhost:5000/amazon/deals
curl http://localhost:5000/myntra/deals
curl http://localhost:5000/flipkart/deals
```

