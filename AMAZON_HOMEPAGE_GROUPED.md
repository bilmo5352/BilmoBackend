# 🛒 Amazon Homepage - Grouped Sections Feature

## ✨ What's New

The Amazon homepage scraper now captures the **ENTIRE homepage** and groups products by their section titles (e.g., "Top Deals", "Electronics", "Fashion", etc.), displaying them in a beautiful, organized layout.

## 🎯 Features

### ✅ Complete Homepage Scraping
- Scrapes **ALL sections** from Amazon India homepage
- Extracts **section titles** (e.g., "Today's Deals", "Electronics", "Fashion")
- Groups products **by section**
- Maintains section hierarchy and organization

### ✅ Smart Data Extraction
Each section includes:
- **Section Title** - Category/section name
- **Item Count** - Number of items in section
- **Items** - Array of products with:
  - Product title
  - Price
  - Discount
  - Image
  - Link to Amazon

### ✅ Beautiful UI Display
- **Grouped layout** with section headers
- **Gradient headers** for each section
- **Responsive grid** for items
- **Hover effects** and animations
- **Amazon-themed** styling

## 📊 Data Structure

### API Response Format
```json
{
  "success": true,
  "data": {
    "timestamp": "2025-09-30T...",
    "source": "cache" | "fresh",
    "total_sections": 15,
    "total_items": 120,
    "sections": [
      {
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
        ]
      }
    ]
  }
}
```

## 🚀 How to Use

### 1. Start the Backend
```bash
python smart_api.py
```

### 2. Open Frontend
```bash
# Open in browser
frontend/index.html
```

### 3. View Amazon Homepage Sections
1. Click the **"Amazon"** button (orange)
2. **Don't type anything** in search
3. Wait 20-40 seconds (first time)
4. See grouped sections!

## 🎨 UI Layout

### Visual Structure
```
┌─────────────────────────────────────┐
│  Amazon Homepage - 15 Sections • 120 Items  │
├─────────────────────────────────────┤
│                                     │
│  ╔═══════════════════════════════╗ │
│  ║   📱 ELECTRONICS              ║ │
│  ║   10 items                    ║ │
│  ╚═══════════════════════════════╝ │
│                                     │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐      │
│  │Item│ │Item│ │Item│ │Item│      │
│  └────┘ └────┘ └────┘ └────┘      │
│                                     │
│  ╔═══════════════════════════════╗ │
│  ║   👕 FASHION                  ║ │
│  ║   8 items                     ║ │
│  ╚═══════════════════════════════╝ │
│                                     │
│  ┌────┐ ┌────┐ ┌────┐             │
│  │Item│ │Item│ │Item│             │
│  └────┘ └────┘ └────┘             │
│                                     │
│  ... more sections ...             │
└─────────────────────────────────────┘
```

### Section Header Style
- **Gradient background** (Purple to Blue)
- **White text** for contrast
- **Large title** (24px, bold)
- **Item count** below title
- **Rounded corners** (8px)
- **15px padding**

### Item Card Style
- **White background**
- **Shadow on hover** with lift effect
- **Amazon orange** badge
- **Product image** (200px height)
- **Price in red** (#B12704)
- **Discount in green** (#007600)
- **Orange button** for Amazon link

## 🔧 Configuration

### Scraper Settings
```python
# In amazon_homepage_deals.py

# Maximum items per section
max_items_per_section = 10

# Run headless
headless = True
```

### Command Line Options
```bash
# Headless mode
python amazon_homepage_deals.py --headless

# Custom items per section
python amazon_homepage_deals.py --max=15

# Both
python amazon_homepage_deals.py --headless --max=15
```

## 📂 File Structure

### Modified Files
```
amazon_homepage_deals.py        # Updated scraper
├── scrape_amazon_homepage_deals()
├── extract_section_title()      # NEW
├── extract_section_items()      # NEW
├── extract_item_info()          # NEW
└── extract_sections_alternative() # NEW

smart_api.py                    # Updated API
└── /amazon/deals endpoint      # Returns grouped sections

frontend/script.js              # Updated frontend
├── loadAmazonDeals()
├── displayAmazonDeals()        # Updated for sections
├── createGroupedSectionsHTML() # NEW
└── createSectionItemCard()     # NEW
```

### Output Files
```
amazon_homepage_deals.json      # Cached homepage data
amazon_homepage.html            # Raw HTML for debugging
```

## 🔍 Example Sections Captured

Common sections found on Amazon homepage:
- **Today's Deals** - Daily deals
- **Electronics** - Phones, laptops, accessories
- **Fashion** - Clothing, shoes, accessories
- **Home & Kitchen** - Appliances, furniture
- **Beauty** - Cosmetics, personal care
- **Books** - Latest releases, bestsellers
- **Sports & Fitness** - Equipment, clothing
- **Toys & Games** - Kids products
- **Automotive** - Car accessories
- **Prime Video** - Streaming content
- **Amazon Pay** - Offers and cashback
- **Fresh Recommendations** - Groceries
- **Gaming** - Consoles, games
- **Pet Supplies** - Food, toys, accessories

## ⚡ Performance

| Metric | Value |
|--------|-------|
| First Load (Scraping) | 30-60 seconds |
| Cached Load | <1 second |
| Sections Captured | 10-20 sections |
| Items Per Section | Up to 10 items |
| Total Items | 80-150 items |
| Cache Duration | 1 hour |
| File Size | 200-500 KB |

## 🧪 Testing

### API Test
```bash
# Test endpoint
curl http://localhost:5000/amazon/deals

# Expected response
{
  "success": true,
  "data": {
    "total_sections": 15,
    "sections": [...]
  }
}
```

### Manual Test
1. Start API: `python smart_api.py`
2. Open frontend: `frontend/index.html`
3. Click Amazon button (no search)
4. Verify:
   - ✓ Sections are displayed with titles
   - ✓ Items are grouped correctly
   - ✓ Images load properly
   - ✓ Links work
   - ✓ Hover effects work

### Console Verification
```javascript
// In browser console (F12)
// After clicking Amazon button

// Should see logs like:
// "🛒 Loading Amazon homepage deals..."
// "🛒 Amazon deals response: {success: true, ...}"
// "🛒 Displaying Amazon homepage sections: ..."
```

## 🎯 User Flow

### Complete User Journey
```
1. User opens frontend
   ↓
2. User clicks "Amazon" button (no search query)
   ↓
3. Loading screen shows
   ↓
4. API checks cache
   ├─ Cached (< 1 hour) → Return instantly
   └─ Not cached → Scrape homepage (30-60s)
      ↓
5. Scraper extracts sections
   ↓
6. Data saved to JSON + MongoDB
   ↓
7. API returns grouped data
   ↓
8. Frontend renders sections
   ├─ Section headers (gradient style)
   ├─ Product cards (grid layout)
   └─ Interactive elements (hover, links)
   ↓
9. User browses organized sections
   ↓
10. User clicks "View on Amazon" → Opens product page
```

## 🔄 Comparison: Old vs New

### Old Implementation
```
❌ Only scraped deals
❌ No organization
❌ Flat list of products
❌ No section context
❌ Limited information
```

### New Implementation
```
✅ Scrapes ENTIRE homepage
✅ Organized by sections
✅ Grouped display
✅ Section titles preserved
✅ Complete homepage structure
✅ Beautiful grouped UI
✅ Section-based navigation
```

## 🎨 Styling Details

### Color Scheme
- **Section Headers**: Purple-Blue gradient (#667eea → #764ba2)
- **Amazon Badge**: Orange (#ff9900)
- **Price Text**: Red (#B12704)
- **Discount Text**: Green (#007600)
- **Buttons**: Amazon Orange with hover

### Typography
- **Section Title**: 24px, bold, white
- **Item Count**: 14px, white, 0.9 opacity
- **Product Title**: 14px, medium weight
- **Price**: 20px, bold
- **Discount**: 14px, semi-bold

### Spacing
- **Section Margin**: 30px bottom
- **Header Padding**: 15px
- **Card Padding**: 15px
- **Grid Gap**: 20px
- **Border Radius**: 8px (sections), 4px (elements)

## 💡 Pro Tips

### For Best Results
1. **First load takes time** - Be patient (30-60s)
2. **Cached is instant** - Subsequent loads <1s
3. **Refresh after 1 hour** - For latest deals
4. **Scroll down slowly** - To see all sections
5. **Hover for effects** - Interactive cards

### Customization
```javascript
// In frontend/script.js

// Change grid columns
minmax(280px, 1fr) → minmax(250px, 1fr)  // Smaller cards
minmax(280px, 1fr) → minmax(320px, 1fr)  // Larger cards

// Change section header color
#667eea → #your-color  // Start color
#764ba2 → #your-color  // End color
```

## 🚨 Troubleshooting

### Issue: No sections showing
**Fix:**
1. Check console for errors
2. Verify API is running
3. Delete `amazon_homepage_deals.json`
4. Click Amazon again

### Issue: Section titles missing
**Fix:**
1. Amazon changed structure
2. Update selectors in `extract_section_title()`
3. Add new selectors

### Issue: Items not grouped
**Fix:**
1. Check JSON structure
2. Verify `sections` array exists
3. Check browser console

## 📈 Future Enhancements

### Potential Features
- [ ] Section filtering
- [ ] Section search
- [ ] Expandable/collapsible sections
- [ ] Section-specific sorting
- [ ] Category icons for sections
- [ ] Section bookmarking
- [ ] Price comparison within sections
- [ ] Section-based recommendations

## 🎉 Success Criteria

✅ **Complete homepage scraping**  
✅ **Section-based grouping**  
✅ **Beautiful UI with headers**  
✅ **Responsive design**  
✅ **Hover interactions**  
✅ **Fast caching (1 hour)**  
✅ **MongoDB integration**  
✅ **Error handling**  
✅ **Amazon-themed styling**  

## 📋 Quick Reference

### Endpoints
- `GET /amazon/deals` - Get grouped homepage sections

### Files
- `amazon_homepage_deals.py` - Scraper
- `amazon_homepage_deals.json` - Cache file
- `smart_api.py` - API with endpoint
- `frontend/script.js` - Frontend display

### Commands
```bash
# Run scraper
python amazon_homepage_deals.py --headless --max=10

# Start API
python smart_api.py

# Test endpoint
curl http://localhost:5000/amazon/deals
```

---

**Last Updated:** September 30, 2025  
**Version:** 2.0.0 (Grouped Sections)  
**Status:** ✅ Fully Implemented

