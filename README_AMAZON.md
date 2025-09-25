# Amazon.in Search Scraper

A Python script that automates product searches on Amazon.in and extracts detailed product information including prices, ratings, images, specifications, and availability status.

## Features

- 🔍 **Automated Search**: Search for products on Amazon.in using Selenium WebDriver
- 📊 **Product Extraction**: Extract comprehensive product details from search results
- 🖼️ **Image Collection**: Download product images with high-resolution URLs
- 📄 **Data Export**: Save results in both HTML and JSON formats
- 🎯 **Detailed Analysis**: Visit individual product pages for detailed information
- 🚀 **Headless Mode**: Run in background without opening browser window
- 🛡️ **Anti-Detection**: Uses stealth techniques to avoid bot detection
- 📋 **Specifications**: Extract product specifications and technical details
- 📦 **Availability**: Check product availability and delivery information

## Installation

### Prerequisites

- Python 3.7 or higher
- Google Chrome browser installed
- Internet connection

### Setup

1. **Clone or download the script files**
2. **Install required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

```bash
# Search for a product (interactive mode)
python amazon_search.py

# Search for a specific product
python amazon_search.py "iphone 14"

# Search with multiple words
python amazon_search.py "samsung galaxy s23"
```

### Headless Mode

Run the script without opening a browser window:

```bash
python amazon_search.py "laptop" --headless
```

### Interactive Mode

If you don't provide a search query, the script will prompt you:

```bash
python amazon_search.py
# Enter product to search on Amazon.in: macbook air
```

## Output Files

The script generates several output files:

### 1. HTML File
- **Format**: `amazon_search_{query}.html`
- **Content**: Complete HTML source of the search results page
- **Usage**: Open in browser to see the actual Amazon page

### 2. Basic Product Data (JSON)
- **Format**: `amazon_products_{query}.json`
- **Content**: Basic product information from search results
- **Includes**: Title, price, rating, reviews, availability, links

### 3. Detailed Product Data (JSON)
- **Format**: `amazon_detailed_products_{query}.json`
- **Content**: Comprehensive product details from individual product pages
- **Includes**: Name, price, brand, category, rating, reviews count, availability, images, specifications

## Example Output

### Console Output
```
✅ Amazon WebDriver initialized with ChromeDriverManager
Waiting for search results to load...

Search results saved as: amazon_search_iphone_14.html
Current URL: https://www.amazon.in/s?k=iphone+14
Page title: Amazon.in : iphone 14

Found 16 product cards using selector: div[data-component-type='s-search-result']

============================================================
EXTRACTED PRODUCT INFORMATION
============================================================

1. Apple iPhone 14 (128 GB) - Blue
   Price: ₹54,900
   Rating: 4.5 out of 5 stars
   Reviews: 1,234 ratings
   Availability: In Stock
   Link: https://www.amazon.in/Apple-iPhone-14-128GB-Blue/dp/B0BDJ8J8J8

2. Apple iPhone 14 (128 GB) - Midnight
   Price: ₹54,900
   Rating: 4.5 out of 5 stars
   Reviews: 1,234 ratings
   Availability: In Stock
   Link: https://www.amazon.in/Apple-iPhone-14-128GB-Midnight/dp/B0BDJ8J8J9
```

### JSON Output Structure
```json
{
  "query": "iphone 14",
  "search_url": "https://www.amazon.in/s?k=iphone+14",
  "total_products": 8,
  "products": [
    {
      "name": "Apple iPhone 14 (128 GB) - Blue",
      "price": "₹54,900",
      "brand": "Apple",
      "category": "Electronics",
      "rating": "4.5 out of 5 stars",
      "reviews_count": "1,234 ratings",
      "availability": "In Stock",
      "link": "https://www.amazon.in/Apple-iPhone-14-128GB-Blue/dp/B0BDJ8J8J8",
      "images": [
        {
          "url": "https://m.media-amazon.com/images/I/61YVqHdFRxL._AC_SX2000_.jpg",
          "alt": "Apple iPhone 14 Blue",
          "thumbnail": "https://m.media-amazon.com/images/I/61YVqHdFRxL._AC_SX679_.jpg"
        }
      ],
      "specifications": {
        "Brand": "Apple",
        "Model Name": "iPhone 14",
        "Storage": "128 GB",
        "Color": "Blue",
        "Screen Size": "6.1 Inches",
        "Operating System": "iOS 16"
      }
    }
  ]
}
```

## Key Differences from Flipkart Scraper

### Amazon-Specific Features

1. **Enhanced Specifications Extraction**:
   - Extracts detailed product specifications
   - Captures technical details from product pages
   - Includes feature bullets and product descriptions

2. **Availability Status**:
   - Checks product availability
   - Shows delivery information
   - Displays stock status

3. **Reviews Count**:
   - Extracts detailed review counts
   - Shows rating breakdowns
   - Includes customer review information

4. **Brand Detection**:
   - Enhanced brand extraction from product pages
   - Better brand identification from product names
   - Includes more brand names in detection list

5. **Image Quality**:
   - Higher resolution image extraction
   - Better image URL processing
   - More comprehensive image selectors

## Configuration

### Adjustable Parameters

You can modify these parameters in the script:

- `max_results`: Maximum number of products to extract (default: 8)
- `headless`: Run browser in background (default: False)
- `timeout`: Wait time for page loading (default: 5-10 seconds)

### Chrome Options

The script includes several Chrome options for optimal performance:

- Disabled GPU acceleration
- Disabled automation indicators
- Disabled extensions
- Custom window size for headless mode
- Anti-detection measures

## Troubleshooting

### Common Issues

1. **ChromeDriver Issues**
   ```
   ❌ All ChromeDriver methods failed: [Error details]
   ```
   **Solution**: Update Chrome browser or install ChromeDriver manually

2. **No Product Cards Found**
   ```
   No product cards found with standard selectors.
   ```
   **Solution**: Amazon may have changed their HTML structure. Check the HTML file for current selectors.

3. **Slow Performance**
   **Solution**: Use headless mode or reduce `max_results` parameter

4. **Image Extraction Issues**
   **Solution**: Amazon's image loading can be slow. The script includes multiple fallback selectors.

### Debug Mode

To debug issues:

1. Check the generated HTML file to see the actual page structure
2. Look at console output for detailed error messages
3. Try running without headless mode to see what's happening

## Amazon-Specific Selectors

The script uses Amazon-specific CSS selectors:

- **Product Cards**: `div[data-component-type='s-search-result']`
- **Titles**: `h2.a-size-mini a span`
- **Prices**: `span.a-price-whole`
- **Ratings**: `span.a-icon-alt`
- **Images**: `img#landingImage`
- **Specifications**: `div#feature-bullets ul li span`

## Legal Notice

⚠️ **Important**: This script is for educational and research purposes only. Please ensure you comply with Amazon's Terms of Service and robots.txt file. Use responsibly and don't overload their servers.

## Dependencies

- `selenium>=4.15.0`: Web automation framework
- `webdriver-manager>=4.0.1`: Automatic ChromeDriver management

## License

This project is for educational purposes. Please respect Amazon's terms of service and use responsibly.

## Comparison with Flipkart Scraper

| Feature | Flipkart Scraper | Amazon Scraper |
|---------|------------------|----------------|
| Product Extraction | ✅ | ✅ |
| Image Collection | ✅ | ✅ |
| Price Extraction | ✅ | ✅ |
| Rating Extraction | ✅ | ✅ |
| Brand Detection | ✅ | ✅ |
| Category Detection | ✅ | ✅ |
| Specifications | ❌ | ✅ |
| Availability Status | ❌ | ✅ |
| Reviews Count | Basic | Detailed |
| Image Quality | Good | Enhanced |
| Anti-Detection | ✅ | ✅ |
| Headless Mode | ✅ | ✅ |
