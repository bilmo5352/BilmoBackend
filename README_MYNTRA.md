# Myntra Search Scraper

A Python script that automates product searches on Myntra.com and extracts detailed product information including prices, discounts, sizes, colors, ratings, and specifications for fashion and lifestyle products.

## Features

- 🔍 **Automated Search**: Search for products on Myntra.com using Selenium WebDriver
- 📊 **Product Extraction**: Extract comprehensive product details from search results
- 🖼️ **Image Collection**: Download product images with high-resolution URLs
- 📄 **Data Export**: Save results in both HTML and JSON formats
- 🎯 **Detailed Analysis**: Visit individual product pages for detailed information
- 🚀 **Headless Mode**: Run in background without opening browser window
- 🛡️ **Anti-Detection**: Uses stealth techniques to avoid bot detection
- 👕 **Fashion-Specific**: Optimized for clothing, shoes, and accessories
- 📏 **Size & Color Options**: Extract available sizes and color variants
- 💰 **Discount Tracking**: Extract original prices and discount percentages
- 📋 **Specifications**: Extract product specifications and descriptions

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
python myntra_search.py

# Search for a specific product
python myntra_search.py "nike shoes"

# Search with multiple words
python myntra_search.py "women's dresses"
```

### Headless Mode

Run the script without opening a browser window:

```bash
python myntra_search.py "men's shirts" --headless
```

### Interactive Mode

If you don't provide a search query, the script will prompt you:

```bash
python myntra_search.py
# Enter product to search on Myntra: adidas sneakers
```

## Output Files

The script generates several output files:

### 1. HTML File
- **Format**: `myntra_search_{query}.html`
- **Content**: Complete HTML source of the search results page
- **Usage**: Open in browser to see the actual Myntra page

### 2. Basic Product Data (JSON)
- **Format**: `myntra_products_{query}.json`
- **Content**: Basic product information from search results
- **Includes**: Title, price, original price, discount, rating, links

### 3. Detailed Product Data (JSON)
- **Format**: `myntra_detailed_products_{query}.json`
- **Content**: Comprehensive product details from individual product pages
- **Includes**: Name, price, original price, discount, brand, category, rating, reviews count, sizes, colors, availability, images, description, specifications

## Example Output

### Console Output
```
✅ Myntra WebDriver initialized with ChromeDriverManager
Waiting for search results to load...

Search results saved as: myntra_search_nike_shoes.html
Current URL: https://www.myntra.com/shoes?search=nike+shoes
Page title: Nike Shoes - Buy Nike Shoes Online at Best Prices in India | Myntra

Found 24 product cards using selector: div[class*='product-base']

============================================================
EXTRACTED PRODUCT INFORMATION
============================================================

1. Nike Air Max 270
   Price: ₹12,995
   Original Price: ₹15,995
   Discount: 19% OFF
   Rating: 4.2
   Link: https://www.myntra.com/shoes/nike/nike-air-max-270/1234567/buy

2. Nike Revolution 6
   Price: ₹3,995
   Original Price: ₹4,995
   Discount: 20% OFF
   Rating: 4.0
   Link: https://www.myntra.com/shoes/nike/nike-revolution-6/1234568/buy
```

### JSON Output Structure
```json
{
  "query": "nike shoes",
  "search_url": "https://www.myntra.com/shoes?search=nike+shoes",
  "total_products": 8,
  "products": [
    {
      "name": "Nike Air Max 270",
      "price": "₹12,995",
      "original_price": "₹15,995",
      "discount": "19% OFF",
      "brand": "Nike",
      "category": "Shoes",
      "rating": "4.2",
      "reviews_count": "1,234 ratings",
      "size_options": ["6", "7", "8", "9", "10", "11"],
      "color_options": ["Black", "White", "Blue", "Red"],
      "availability": "In Stock",
      "link": "https://www.myntra.com/shoes/nike/nike-air-max-270/1234567/buy",
      "images": [
        {
          "url": "https://assets.myntassets.com/h_1440,q_100,w_1080/v1/assets/images/1234567/2023/1/1/abc123.jpg",
          "alt": "Nike Air Max 270",
          "thumbnail": "https://assets.myntassets.com/h_720,q_100,w_540/v1/assets/images/1234567/2023/1/1/abc123.jpg"
        }
      ],
      "description": "The Nike Air Max 270 delivers visible cushioning under every step...",
      "specifications": {
        "Brand": "Nike",
        "Model": "Air Max 270",
        "Type": "Running Shoes",
        "Material": "Mesh and Synthetic",
        "Sole": "Rubber",
        "Closure": "Lace-up"
      }
    }
  ]
}
```

## Key Features for Fashion Products

### 1. **Size Options Extraction**:
   - Extracts available sizes for clothing and shoes
   - Handles different size formats (S, M, L, XL or 6, 7, 8, 9, 10)
   - Removes duplicates and provides clean size lists

### 2. **Color Variants**:
   - Captures available color options
   - Extracts color names and variants
   - Useful for fashion product analysis

### 3. **Price Analysis**:
   - Extracts current selling price
   - Captures original MRP price
   - Calculates discount percentages
   - Tracks price trends and offers

### 4. **Brand Detection**:
   - Enhanced brand extraction for fashion brands
   - Includes major fashion and lifestyle brands
   - Brand identification from product names

### 5. **Fashion-Specific Data**:
   - Product descriptions and details
   - Material and specification information
   - Style and design details
   - Care instructions and features

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
   **Solution**: Myntra may have changed their HTML structure. Check the HTML file for current selectors.

3. **Slow Performance**
   **Solution**: Use headless mode or reduce `max_results` parameter

4. **Image Extraction Issues**
   **Solution**: Myntra's image loading can be slow. The script includes multiple fallback selectors.

### Debug Mode

To debug issues:

1. Check the generated HTML file to see the actual page structure
2. Look at console output for detailed error messages
3. Try running without headless mode to see what's happening

## Myntra-Specific Selectors

The script uses Myntra-specific CSS selectors:

- **Product Cards**: `div[class*='product-base']`
- **Titles**: `h3[class*='product-brand']`
- **Prices**: `span[class*='product-discountedPrice']`
- **Original Prices**: `span[class*='product-strike']`
- **Discounts**: `span[class*='product-discountPercentage']`
- **Images**: `img[class*='pdp-image']`
- **Sizes**: `div[class*='size'] button`
- **Colors**: `div[class*='color'] button`

## Legal Notice

⚠️ **Important**: This script is for educational and research purposes only. Please ensure you comply with Myntra's Terms of Service and robots.txt file. Use responsibly and don't overload their servers.

## Dependencies

- `selenium>=4.15.0`: Web automation framework
- `webdriver-manager>=4.0.1`: Automatic ChromeDriver management

## License

This project is for educational purposes. Please respect Myntra's terms of service and use responsibly.

## Comparison with Other Scrapers

| Feature | Flipkart Scraper | Amazon Scraper | Myntra Scraper |
|---------|------------------|----------------|----------------|
| Product Extraction | ✅ | ✅ | ✅ |
| Image Collection | ✅ | ✅ | ✅ |
| Price Extraction | ✅ | ✅ | ✅ |
| Rating Extraction | ✅ | ✅ | ✅ |
| Brand Detection | ✅ | ✅ | ✅ |
| Category Detection | ✅ | ✅ | ✅ |
| Discount Tracking | ❌ | ❌ | ✅ |
| Size Options | ❌ | ❌ | ✅ |
| Color Variants | ❌ | ❌ | ✅ |
| Original Price | ❌ | ❌ | ✅ |
| Specifications | ❌ | ✅ | ✅ |
| Availability Status | ❌ | ✅ | ✅ |
| Fashion-Specific | ❌ | ❌ | ✅ |
| Anti-Detection | ✅ | ✅ | ✅ |
| Headless Mode | ✅ | ✅ | ✅ |

## Fashion Industry Use Cases

### 1. **Price Monitoring**:
   - Track price changes across products
   - Monitor discount trends
   - Compare prices with competitors

### 2. **Inventory Analysis**:
   - Check size availability
   - Monitor color variants
   - Track stock levels

### 3. **Product Research**:
   - Analyze product descriptions
   - Study specifications
   - Research brand offerings

### 4. **Market Analysis**:
   - Study fashion trends
   - Analyze brand performance
   - Research customer preferences

## Tips for Fashion Scraping

1. **Use Specific Queries**: Be specific with fashion terms (e.g., "women's summer dresses" instead of "dresses")
2. **Check Size Availability**: Use the size options data to understand inventory
3. **Monitor Discounts**: Track discount percentages for sales analysis
4. **Analyze Colors**: Use color variants for trend analysis
5. **Brand Research**: Use brand detection for competitive analysis
