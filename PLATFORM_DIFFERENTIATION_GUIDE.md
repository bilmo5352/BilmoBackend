# 🔍 Platform Differentiation Guide

## Overview
This guide explains how different e-commerce platforms' deals are stored and differentiated in MongoDB.

---

## 📊 Storage Architecture

### 1. **Amazon Deals**
- **Collection**: `amazon_homepage_deals` (Dedicated)
- **Database**: `scraper_db`
- **Endpoint**: `/amazon/deals`

#### Document Structure:
```json
{
  "_id": "ObjectId",
  "timestamp": "2025-10-01T...",
  "platform": "Amazon",  ✅ Platform identifier
  "source": "Amazon India Homepage",
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

#### Section Document Structure:
```json
{
  "_id": "ObjectId",
  "timestamp": "2025-10-01T...",
  "platform": "Amazon",  ✅ Platform identifier
  "section_title": "Today's Deals",
  "item_count": 10,
  "items": [
    {
      "title": "Product Name",
      "price": "₹1,999",
      "discount": "50% off",
      "image": "https://...",
      "link": "https://amazon.in/...",
      "platform": "Amazon"  ✅ Item-level platform identifier
    }
  ],
  "parent_document_id": "ObjectId"
}
```

---

### 2. **Myntra Deals**
- **Collection**: `unified_search_results` (Shared)
- **Database**: `scraper_db`
- **Endpoint**: `/myntra/deals`

#### Document Structure:
```json
{
  "_id": "ObjectId",
  "platform": "Myntra",  ✅ Platform identifier
  "scraped_at": "2025-10-01T...",
  "section_title": "Fashion Deals",
  "item_count": 10,
  "items": [...]
}
```

---

### 3. **Flipkart Deals**
- **Collection**: `unified_search_results` (Shared)
- **Database**: `scraper_db`
- **Endpoint**: `/flipkart/deals`

#### Document Structure:
```json
{
  "_id": "ObjectId",
  "platform": "Flipkart",  ✅ Platform identifier
  "scraped_at": "2025-10-01T...",
  "section_title": "Electronics Deals",
  "item_count": 10,
  "items": [...]
}
```

---

## 🔧 How to Query Each Platform

### Query Amazon Deals Only
```javascript
// MongoDB Query
db.amazon_homepage_deals.find({ "platform": "Amazon" })
```

```python
# Python Query
deals_collection = db['amazon_homepage_deals']
amazon_deals = deals_collection.find({"platform": "Amazon"})
```

### Query Myntra Deals Only
```javascript
// MongoDB Query
db.unified_search_results.find({ "platform": "Myntra" })
```

```python
# Python Query
unified_collection = db['unified_search_results']
myntra_deals = unified_collection.find({"platform": "Myntra"})
```

### Query Flipkart Deals Only
```javascript
// MongoDB Query
db.unified_search_results.find({ "platform": "Flipkart" })
```

```python
# Python Query
unified_collection = db['unified_search_results']
flipkart_deals = unified_collection.find({"platform": "Flipkart"})
```

---

## 🎯 Key Differences

| Platform  | Collection                | Platform Field | Timestamp Field | Unique Identifier          |
|-----------|---------------------------|----------------|-----------------|----------------------------|
| Amazon    | `amazon_homepage_deals`   | ✅ "Amazon"     | `timestamp`     | Dedicated collection       |
| Myntra    | `unified_search_results`  | ✅ "Myntra"     | `scraped_at`    | Platform field filter      |
| Flipkart  | `unified_search_results`  | ✅ "Flipkart"   | `scraped_at`    | Platform field filter      |

---

## 🚨 Why They Don't Mix

### Separation Strategy:
1. **Amazon** has its **own dedicated collection** (`amazon_homepage_deals`)
2. **Myntra** and **Flipkart** share a **different collection** (`unified_search_results`)
3. Each platform has a **`platform` field** for identification
4. Each item within sections has its own **`platform` field**

### Collection Isolation:
- Collections are **separate databases tables**
- A document in `amazon_homepage_deals` **cannot appear** in `unified_search_results`
- Even if stored in the same collection, the **`platform` field ensures differentiation**

---

## ✅ Verification Methods

### Method 1: Check Collection Names
```python
# List all collections
db.list_collection_names()
# Output: ['amazon_homepage_deals', 'unified_search_results', ...]
```

### Method 2: Count Documents by Platform
```python
# Count Amazon deals
amazon_count = db['amazon_homepage_deals'].count_documents({"platform": "Amazon"})

# Count Myntra deals
myntra_count = db['unified_search_results'].count_documents({"platform": "Myntra"})

# Count Flipkart deals
flipkart_count = db['unified_search_results'].count_documents({"platform": "Flipkart"})

print(f"Amazon: {amazon_count} documents")
print(f"Myntra: {myntra_count} documents")
print(f"Flipkart: {flipkart_count} documents")
```

### Method 3: Verify Platform Field in All Documents
```python
# Check if any document has wrong platform
amazon_collection = db['amazon_homepage_deals']
wrong_platform = amazon_collection.find_one({"platform": {"$ne": "Amazon"}})

if wrong_platform:
    print("⚠️ Found document with wrong platform!")
else:
    print("✅ All documents have correct platform field")
```

---

## 🛠️ API Endpoints for Each Platform

### Amazon Deals
```bash
# Get Amazon deals
curl http://localhost:5000/amazon/deals

# Get Amazon collection data
curl http://localhost:5000/amazon/deals/collection

# Get Amazon sections
curl http://localhost:5000/amazon/deals/sections
```

### Myntra Deals
```bash
# Get Myntra deals
curl http://localhost:5000/myntra/deals
```

### Flipkart Deals
```bash
# Get Flipkart deals
curl http://localhost:5000/flipkart/deals
```

---

## 📝 Summary

✅ **Amazon deals** are stored in a **dedicated collection** with `platform: "Amazon"`  
✅ **Myntra deals** are stored in **shared collection** with `platform: "Myntra"`  
✅ **Flipkart deals** are stored in **shared collection** with `platform: "Flipkart"`  
✅ All items within sections have **item-level platform identifiers**  
✅ **No cross-contamination** possible due to collection separation and platform fields  

---

## 🔍 If You Suspect Data Mixing

Run this verification script:

```python
from pymongo import MongoClient

# Connect
client = MongoClient("mongodb+srv://hrithick:hrithick@bilmo.jmeclfh.mongodb.net/")
db = client['scraper_db']

# Check Amazon collection
amazon_coll = db['amazon_homepage_deals']
print(f"Amazon Collection Total: {amazon_coll.count_documents({})}")
print(f"Amazon Platform Field: {amazon_coll.count_documents({'platform': 'Amazon'})}")
print(f"Non-Amazon in Amazon Coll: {amazon_coll.count_documents({'platform': {'$ne': 'Amazon'}})}")

# Check unified collection
unified_coll = db['unified_search_results']
print(f"\nUnified Collection Total: {unified_coll.count_documents({})}")
print(f"Myntra Deals: {unified_coll.count_documents({'platform': 'Myntra'})}")
print(f"Flipkart Deals: {unified_coll.count_documents({'platform': 'Flipkart'})}")
print(f"Amazon in Unified Coll: {unified_coll.count_documents({'platform': 'Amazon'})}")
```

This will show you if there's any cross-contamination between platforms.

