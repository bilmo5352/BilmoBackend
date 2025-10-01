# ✈️ IndiGo Flight Scraper - Complete Guide

## 🎯 Why IndiGo Scraper?

**IndiGo is India's largest airline** with flights from EVERYWHERE, including Madurai!

### Advantages:
- ✅ **Most domestic routes** in India
- ✅ **Direct URL** to flight results (no form filling needed)
- ✅ **Consistent structure** (easier to scrape)
- ✅ Shows **all available flights** for the route
- ✅ Includes **prices, times, stops, duration**

---

## 🔧 How It Works

### Direct URL Method:
Instead of filling forms, we go directly to results:

```
https://www.goindigo.in/booking/flight-select.html?dep=IXM&arr=BOM&date=2025-10-15&pax=1&class=E
```

**Parameters**:
- `dep` = Departure airport (IXM for Madurai)
- `arr` = Arrival airport  
- `date` = Departure date (YYYY-MM-DD)
- `pax` = Passengers (1)
- `class` = Economy (E)

---

## 📊 Data Extracted

From each flight card:
```json
{
  "airline": "IndiGo",
  "flight_number": "6E 2561",
  "price": "₹7,733",
  "departure_time": "04:20",
  "arrival_time": "06:55",
  "duration": "02h 35m",
  "stops": "Non-stop",
  "origin": "IXM",
  "destination": "BOM",
  "departure_date": "2025-10-15"
}
```

---

## 🚀 Usage

### From Madurai (IXM):

```bash
# To Mumbai
python indigo_scraper.py IXM BOM 2025-10-15

# To Delhi
python indigo_scraper.py IXM DEL 2025-10-15

# To Bangalore
python indigo_scraper.py IXM BLR 2025-10-15

# To Chennai
python indigo_scraper.py IXM MAA 2025-10-15
```

### Through API:
```bash
curl "http://localhost:5000/flights/search?origin=IXM&destination=BOM&date=2025-10-15"
```

---

## 📦 MongoDB Storage

**Collection**: `flight_searches`

```json
{
  "timestamp": "2025-10-01T...",
  "origin": "IXM",
  "destination": "BOM",
  "departure_date": "2025-10-15",
  "total_flights": 12,
  "flights": [
    {
      "airline": "IndiGo",
      "flight_number": "6E 2561",
      "price": "₹7,733",
      "departure_time": "04:20",
      "arrival_time": "06:55",
      "duration": "02h 35m",
      "stops": "Non-stop"
    }
  ],
  "search_metadata": {
    "scraper_version": "2.0.0",
    "data_source": "IndiGo",
    "scraper_type": "indigo_direct_url",
    "cache_duration_hours": 6
  }
}
```

---

## 🔍 Extraction Strategy

### 1. **Multiple Selectors**
Tries different CSS selectors for flight cards:
```python
flight_selectors = [
    "div[class*='flight-card']",
    "div[class*='flightCard']",
    "div[class*='Flight']",
    "li[class*='flight']",
]
```

### 2. **Aggressive Fallback**
If selectors fail, searches ALL divs for flight-like data:
```python
# Look for elements with:
- Times (04:20, 06:55)
- Prices (₹7,733)
- Both present = likely a flight card
```

### 3. **Regex Extraction**
Extracts data using patterns:
```python
# Times: \d{2}:\d{2}
# Price: ₹[\d,]+
# Duration: \d+h\s*\d*m?
# Flight number: 6E\s*\d{3,4}
```

---

## 🎯 What You'll See

### Flight Card Display:
```
┌─────────────────────────────────┐
│ IndiGo 6E 2561                  │
├─────────────────────────────────┤
│ 04:20  →  06:55                 │
│ 02h 35m                         │
│ Non-stop                        │
│ ₹7,733                          │
│ IXM → BOM                       │
└─────────────────────────────────┘
```

---

## 🐛 Debugging

### Files Saved:
- `indigo_flights.html` - Full HTML for inspection
- `indigo_flights.json` - Extracted flight data

### Check If Working:
1. Run scraper with visible browser (`headless=False`)
2. Check `indigo_flights.html` file
3. Look for flight cards in the HTML
4. Update selectors if IndiGo changed their structure

---

## ✅ Advantages Over Other Scrapers

| Feature | IndiGo Scraper | Google Flights | Individual Airlines |
|---------|---------------|----------------|---------------------|
| Direct URL | ✅ Yes | ✅ Yes | ❌ No (form filling) |
| Reliability | ✅ High | ⚠️ Medium | ❌ Low |
| All Airlines | ❌ IndiGo only | ✅ All | ❌ One each |
| Scraping Speed | ✅ Fast | ⚠️ Medium | ❌ Slow (multiple sites) |
| Madurai Support | ✅ Yes | ✅ Yes | ⚠️ Some |

---

## 🚀 Result

Now you can search flights from **Madurai to anywhere** with:
- ✅ All IndiGo flights shown
- ✅ Real prices and times
- ✅ Flight numbers and stops
- ✅ Cached in MongoDB
- ✅ Instant results on repeat searches

Test it now! 🎉

