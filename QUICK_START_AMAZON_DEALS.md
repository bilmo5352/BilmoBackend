# 🚀 Quick Start - Amazon Homepage Deals Feature

## ⚡ 3-Step Setup

### Step 1: Start the Backend
```bash
python smart_api.py
```
**Expected Output:**
```
🚀 Starting Smart E-commerce Search API...
📍 Endpoints:
   GET  /search?q=<query>&force_refresh=<bool>
   POST /search (JSON body)
   GET  /history?limit=<int>
   GET  /cached/<id>
   GET  /status
   GET  /amazon/deals  ← NEW!
```

### Step 2: Open Frontend
```bash
# Just open this file in your browser:
frontend/index.html
```

### Step 3: View Amazon Deals
1. Click the **"Amazon"** button (orange button)
2. **Don't type anything** in search box
3. Wait 15-30 seconds (first time only)
4. Enjoy browsing deals! 🎉

## 📸 What You'll See

### Deals Display
- **Deal Cards** with product images
- **Prices** and discounts
- **Deal Types** (Today's Deal, Lightning Deal, etc.)
- **View Deal** links to Amazon
- **Cache Status** (fresh or cached)

### Sample Deal Card
```
┌─────────────────────────┐
│   TODAY'S DEAL          │
├─────────────────────────┤
│   [Product Image]       │
│                         │
│   Product Title Here    │
│                         │
│   ₹1,999                │
│   50% off               │
│                         │
│   [View Deal 🔗]        │
└─────────────────────────┘
```

## 🧪 Quick Test

### Test 1: API Working?
```bash
curl http://localhost:5000/status
```
**Expected:** `{"success": true, "api_status": "online", ...}`

### Test 2: Get Deals
```bash
curl http://localhost:5000/amazon/deals
```
**Expected:** JSON with 20 deals

### Test 3: Run Test Suite
```bash
python test_amazon_deals.py
```
**Expected:** Test results with ✅ marks

## 💡 How It Works

### First Click (Fresh Scrape)
```
Click Amazon → Loading 15-30s → Scrape Amazon → Save JSON → Show Deals
```

### Second Click (Cached)
```
Click Amazon → Loading <1s → Load from JSON → Show Deals
```

### After 1 Hour
```
Click Amazon → Cache expired → Fresh scrape again
```

## 🎯 Key Features

✅ **No Search Needed** - Just click Amazon button  
✅ **Smart Caching** - 1-hour cache for speed  
✅ **Auto-Refresh** - Fresh deals every hour  
✅ **MongoDB Saved** - Persistent storage  
✅ **Beautiful UI** - Matches your design  

## 🔍 Troubleshooting

### Problem: "Cannot connect to server"
**Fix:** Make sure `python smart_api.py` is running

### Problem: No deals showing
**Fix:** 
1. Check browser console (F12)
2. Verify API is running: `curl http://localhost:5000/status`

### Problem: Deals are old
**Fix:** Delete `amazon_homepage_deals.json` file

## 📂 Files Overview

| File | Purpose |
|------|---------|
| `amazon_homepage_deals.py` | Scraper for deals |
| `smart_api.py` | API with `/amazon/deals` endpoint |
| `frontend/script.js` | UI logic for displaying deals |
| `amazon_homepage_deals.json` | Cached deals (auto-generated) |

## 🐳 Docker Alternative

### Quick Docker Run
```bash
# Build
docker-compose build

# Run
docker-compose up -d

# Access
http://localhost:5000/amazon/deals
```

## 📚 More Information

- **Full Docs:** `AMAZON_DEALS_FEATURE.md`
- **Implementation Details:** `IMPLEMENTATION_SUMMARY.md`
- **Test Suite:** `python test_amazon_deals.py`

## ✨ Pro Tips

1. **First Load:** Takes 15-30 seconds (normal)
2. **Cached Load:** Takes <1 second (super fast!)
3. **Fresh Deals:** Click Amazon button again after 1 hour
4. **Search Mode:** Type a query, then click Amazon for search results
5. **Deal Mode:** Click Amazon without typing for homepage deals

## 🎉 You're All Set!

**Just remember:**
1. ✅ Run: `python smart_api.py`
2. ✅ Open: `frontend/index.html`
3. ✅ Click: Amazon button (no search)
4. ✅ Enjoy: Browse deals!

---

**Happy Deal Hunting! 🛒**

