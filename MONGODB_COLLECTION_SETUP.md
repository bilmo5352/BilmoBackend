# 🗄️ Amazon Deals MongoDB Collection - Complete Setup

## ✅ Collection Created Successfully!

Your dedicated MongoDB collection for Amazon homepage deals has been created and configured.

## 📊 Collection Details

### Database & Collection Info
- **Database**: `scraper_db`
- **Collection**: `amazon_homepage_deals`
- **MongoDB Atlas**: `https://cloud.mongodb.com/`
- **Connection**: `mongodb+srv://hrithick:hrithick@bilmo.jmeclfh.mongodb.net/`

### Collection Structure
The collection stores two types of documents:

#### 1. **Main Homepage Documents**
```json
{
  "_id": "ObjectId",
  "timestamp": "2025-09-30T16:05:41.418000",
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

#### 2. **Individual Section Documents**
```json
{
  "_id": "ObjectId",
  "timestamp": "2025-09-30T16:05:41.418000",
  "section_title": "Today's Deals",
  "item_count": 10,
  "items": [
    {
      "title": "Product Name",
      "price": "₹1,999",
      "discount": "50% off",
      "image": "https://...",
      "link": "https://amazon.in/..."
    }
  ],
  "parent_document_id": "ObjectId"
}
```

## 🔗 Access Methods

### 1. **MongoDB Atlas Web Interface**
```
https://cloud.mongodb.com/
```
- Login with your credentials
- Navigate to `bilmo` cluster
- Browse `scraper_db` → `amazon_homepage_deals`

### 2. **Built-in Web Viewer**
```
http://localhost:5000/amazon/deals/view
```
- Beautiful HTML interface
- Shows recent documents
- Displays sections and items
- Refresh button included

### 3. **API Endpoints**

#### Get All Collection Data
```bash
curl http://localhost:5000/amazon/deals/collection
```

#### Get Only Sections
```bash
curl http://localhost:5000/amazon/deals/sections
```

#### Get Fresh Deals (triggers scraping)
```bash
curl http://localhost:5000/amazon/deals
```

### 4. **MongoDB Compass**
Use this connection string:
```
mongodb+srv://hrithick:hrithick@bilmo.jmeclfh.mongodb.net/?retryWrites=true&w=majority&appName=bilmo
```

## 🔧 Collection Features

### ✅ Indexes Created
- **timestamp** - For sorting by date
- **section_title** - For section queries
- **scrape_type** - For filtering homepage scrapes
- **Compound index** - For efficient queries

### ✅ Automatic Saving
When you click the Amazon button:
1. Scrapes entire homepage
2. Groups by sections
3. Saves main document
4. Saves individual section documents
5. Updates timestamps

### ✅ Data Organization
- **Main documents**: Complete homepage snapshots
- **Section documents**: Individual sections for easy querying
- **Metadata**: Scraper version and method info
- **Timestamps**: When data was scraped

## 🚀 How to Use

### Step 1: Start the API
```bash
python smart_api.py
```

### Step 2: Scrape Amazon Homepage
```bash
# Option 1: Use frontend
# Open frontend/index.html
# Click Amazon button (no search text)

# Option 2: Use API directly
curl http://localhost:5000/amazon/deals
```

### Step 3: View the Data
```bash
# Option 1: Web viewer
http://localhost:5000/amazon/deals/view

# Option 2: MongoDB Atlas
https://cloud.mongodb.com/

# Option 3: API JSON
curl http://localhost:5000/amazon/deals/collection
```

## 📈 What Gets Stored

### Complete Homepage Data
- **20-30 sections** (Today's Deals, Electronics, Fashion, etc.)
- **200-400 products** total
- **Product details**: title, price, discount, image, link
- **Section organization**: grouped by category
- **Timestamps**: when scraped

### Example Sections Stored
```
- Today's Deals (10 items)
- Electronics (10 items)
- Fashion (8 items)
- Home & Kitchen (10 items)
- Beauty (8 items)
- Books (6 items)
- Sports & Fitness (7 items)
- Toys & Games (9 items)
- Automotive (5 items)
- Prime Video (3 items)
- Amazon Pay Offers (4 items)
- Fresh & Groceries (6 items)
- Pet Supplies (5 items)
- Baby Products (4 items)
- Health & Wellness (6 items)
- ... and more sections
```

## 🔍 Query Examples

### MongoDB Queries
```javascript
// Get all homepage scrapes
db.amazon_homepage_deals.find({"scrape_type": "complete_homepage"})

// Get specific section
db.amazon_homepage_deals.find({"section_title": "Today's Deals"})

// Get recent data
db.amazon_homepage_deals.find().sort({"timestamp": -1}).limit(10)

// Count total documents
db.amazon_homepage_deals.countDocuments({})
```

### API Queries
```bash
# Get latest homepage scrape
curl "http://localhost:5000/amazon/deals/collection" | jq '.documents[0]'

# Get all sections
curl "http://localhost:5000/amazon/deals/sections" | jq '.sections[].section_title'

# Get specific section
curl "http://localhost:5000/amazon/deals/sections" | jq '.sections[] | select(.section_title == "Today'\''s Deals")'
```

## 📊 Collection Statistics

### Current Status
- **Total Documents**: 1 (sample document)
- **Collection Size**: 0.0 MB
- **Indexes**: 4 indexes created
- **Status**: Ready for data

### After First Scrape
- **Total Documents**: ~25-50 documents
- **Collection Size**: ~1-5 MB
- **Sections**: 20-30 sections
- **Products**: 200-400 products

## 🎯 Benefits

### ✅ Organized Storage
- Dedicated collection for Amazon deals
- Separate from search results
- Easy to query and analyze

### ✅ Performance Optimized
- Indexes for fast queries
- Efficient data structure
- Minimal storage overhead

### ✅ Multiple Access Methods
- Web interface
- API endpoints
- MongoDB tools
- Direct database access

### ✅ Automatic Management
- Auto-saves when scraping
- Timestamps for tracking
- Metadata for versioning

## 🔄 Data Flow

```
1. User clicks Amazon button
   ↓
2. Scraper runs (30-60 seconds)
   ↓
3. Data grouped by sections
   ↓
4. Main document saved
   ↓
5. Individual section documents saved
   ↓
6. Data available in MongoDB
   ↓
7. Accessible via web viewer/API
```

## 🎉 Success!

Your Amazon deals collection is now ready! 

**Next Steps:**
1. ✅ Run `python smart_api.py`
2. ✅ Click Amazon button in frontend
3. ✅ View data at `http://localhost:5000/amazon/deals/view`
4. ✅ Browse MongoDB Atlas at `https://cloud.mongodb.com/`

**Your Amazon homepage deals will be automatically stored and organized in MongoDB!** 🚀


