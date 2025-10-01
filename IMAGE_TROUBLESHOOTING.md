# 🔍 Flipkart Image Troubleshooting Guide

## Issue: Images Not Showing

### Check These Steps:

#### 1. **Open Browser Console** (F12)
When you click Flipkart Deals button, you should see logs like:
```
✅ Flipkart item has image: Product Name -> https://...
```
or
```
⚠️ Flipkart item missing image: Product Name
```

#### 2. **Check What's Being Extracted**
Look for this log in the console:
```javascript
📦 Sample Flipkart item: {
    title: "Product Name",
    image: "https://...",  // ← Should have a URL here
    price: "₹999",
    link: "https://..."
}
```

#### 3. **If Image URL Exists But Doesn't Load**
Look for error logs:
```
❌ Image failed to load: https://...
```

This means:
- Image URL was extracted ✅
- But URL is broken or blocked by CORS ❌

#### 4. **If No Image URL**
If you see:
```javascript
image: ""  // ← Empty!
```

Then the scraper isn't finding images. Check server logs for:
```
⚠️ Item missing image: Product Name
📊 Images: 0/10, Prices: 8/10
```

---

## Solutions

### Solution 1: Check Server Logs
Look at the Python console output when scraping:
```
📊 Images: 0/10, Prices: 8/10  ← No images extracted!
```

### Solution 2: Run Test Scraper
```bash
python flipkart_homepage_deals.py --headless
```

Check the output JSON:
```bash
cat flipkart_homepage_deals.json
```

### Solution 3: Verify Image URLs
If images are being extracted, check if they're valid:
- Should start with `https://`
- Should be from Flipkart domains
- Shouldn't be blocked by CORS

### Solution 4: Check Frontend
Open `flipkart_homepage_deals.json` and verify:
```json
{
  "sections": [
    {
      "items": [
        {
          "title": "Product",
          "image": "https://...",  ← Should have URL
          "price": "₹999"
        }
      ]
    }
  ]
}
```

---

## Debug Commands

### 1. Check if images are in JSON:
```powershell
Get-Content flipkart_homepage_deals.json | Select-String "image"
```

### 2. Count items with images:
```powershell
$json = Get-Content flipkart_homepage_deals.json | ConvertFrom-Json
$totalItems = 0
$itemsWithImages = 0
foreach ($section in $json.sections) {
    foreach ($item in $section.items) {
        $totalItems++
        if ($item.image) { $itemsWithImages++ }
    }
}
Write-Host "Items with images: $itemsWithImages / $totalItems"
```

### 3. Check server output:
Look for these messages in Python output:
```
✅ Found image: https://...
⚠️ Rejected image URL: ...
⚠️ Item missing image: ...
```

---

## Expected Behavior

### When Working Correctly:
1. **Server logs show:**
   ```
   📊 Images: 8/10, Prices: 9/10
   ✅ Found image: https://rukminim2.flixcart.com/...
   ```

2. **Browser console shows:**
   ```
   ✅ Flipkart item has image: Product -> https://...
   ```

3. **Images display** in the UI

### When Not Working:
1. **Server logs show:**
   ```
   📊 Images: 0/10, Prices: 8/10
   ⚠️ Item missing image: Product Name
   ```

2. **Browser console shows:**
   ```
   ⚠️ Flipkart item missing image: Product Name
   ```

3. **Placeholder boxes (📦)** show instead of images

---

## Next Steps

1. ✅ Delete cache: `del flipkart_homepage_deals.json`
2. ✅ Check browser console (F12) when loading deals
3. ✅ Look for debug logs showing image URLs
4. ✅ Check if images are being extracted in server logs
5. ✅ Verify image URLs in the JSON file

---

## Quick Fix

If images still don't show, it's likely:
1. Flipkart changed their HTML structure
2. Images are lazy-loaded differently
3. Need to update CSS selectors

**Check the actual Flipkart site** and inspect product images to see what attributes they use now.

