# 🔧 Flipkart Image & Price Extraction Fix

## 🎯 Problem
Flipkart scraper wasn't extracting images and prices properly.

## ✅ Solutions Applied

### 1. **Enhanced Image Extraction**

#### Multiple Fallback Methods:
```python
# 1. Try img src attribute
img_src = img.get_attribute('src')

# 2. Try data-src (lazy loaded images)
img_src = img.get_attribute('data-src')

# 3. Try srcset attribute
srcset = img.get_attribute('srcset')

# 4. Look in parent if not in link element
imgs = section_element.find_elements(By.TAG_NAME, 'img')
```

#### Broader Image Source Validation:
```python
# Accept various Flipkart image domains
if any(x in img_src.lower() for x in ['flipkart', 'flixcart', 'fkimg', 'img', 'rukminim']):
    item_info['image'] = img_src
```

#### Handle Protocol-Relative URLs:
```python
if img_src.startswith('//'):
    img_src = 'https:' + img_src
```

---

### 2. **Enhanced Price Extraction**

#### 3-Strategy Approach:

**Strategy 1: Immediate Parent**
```python
# Try multiple Flipkart price class selectors
price_selectors = [
    "div._30jeq3", "span._30jeq3",  # Flipkart specific
    "div._1vC4OE", "span._1vC4OE",  # Flipkart specific
    "div._25b18c", "span._25b18c",  # Flipkart specific
    "div[class*='price']", "span[class*='price']",  # Generic
]
```

**Strategy 2: Section Text with Regex**
```python
# Extract prices from section text using regex
price_pattern = r'₹[\d,]+(?:\.\d+)?'
prices = re.findall(price_pattern, section_text)
```

**Strategy 3: Ancestor Search**
```python
# Look up to 3 ancestor levels
ancestor = item_element.find_element(By.XPATH, './ancestor::div[3]')
# Search all text elements for rupee symbol
```

---

### 3. **Improved Item Validation**

#### Prefer Items with Data:
```python
# Prefer items with price and image, but add anyway if we don't have enough
if item_info.get('image') or item_info.get('price') or len(items) < 3:
    items.append(item_info)
```

#### Debug Logging:
```python
# Log items missing data
for item in valid_items:
    if not item.get('image'):
        logger.debug(f"Item missing image: {item.get('title')}")
    if not item.get('price'):
        logger.debug(f"Item missing price: {item.get('title')}")
```

---

### 4. **Title Extraction from URL**

If all else fails, extract from product URL:
```python
# Extract product name from URL
url_parts = link.split('/p/')[0].split('/')
product_slug = url_parts[-1]
title = product_slug.replace('-', ' ').title()
```

---

## 📊 Extraction Priority

### Images:
1. `<img src="...">`
2. `<img data-src="...">`
3. `<img srcset="...">`
4. Parent element images
5. Accept: flipkart, flixcart, fkimg, img, rukminim domains

### Prices:
1. Direct Flipkart price classes (`_30jeq3`, `_1vC4OE`, etc.)
2. Generic price classes
3. Regex extraction from section text
4. Search in ancestor elements (up to 3 levels)

### Titles:
1. `aria-label` attribute
2. Image `alt` text
3. Element text content
4. Extract from product URL

---

## ✅ Expected Results

Now Flipkart items should have:
- ✅ **Title** (from multiple sources)
- ✅ **Price** (3 fallback strategies)
- ✅ **Image** (multiple attribute sources)
- ✅ **Link** (validated Flipkart URLs)
- ✅ **Discount** (if available)

---

## 🔍 Debugging

Check console logs for:
```
ℹ️ Item missing image: Samsung Galaxy...
ℹ️ Item missing price: iPhone 15...
```

This helps identify which items need better selectors.

---

## 🎯 Result

Much better data extraction with proper images and prices for Flipkart deals! 🚀

