# E-commerce Scraper Flask API

A unified Flask API that combines scrapers for Amazon, Flipkart, Meesho, and Myntra to search and extract product information.

## Features

- 🔍 **Multi-platform Search**: Search across Amazon, Flipkart, Meesho, and Myntra simultaneously
- 🚀 **Concurrent Processing**: Uses threading for faster results
- 🌐 **RESTful API**: Clean REST endpoints with JSON responses
- 🎯 **Individual Platform Support**: Search specific platforms
- 📱 **Web Interface**: Built-in web interface for testing
- 🔧 **Driver Pool Management**: Efficient WebDriver management
- 🛡️ **Error Handling**: Comprehensive error handling and logging

## Installation

1. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Chrome Browser** (required for Selenium):
   - Download and install Google Chrome from [chrome.google.com](https://chrome.google.com)

## Usage

### Starting the API Server

```bash
python app.py
```

The API will be available at `http://localhost:5000`

### API Endpoints

#### 1. Home Page & Documentation
- **GET** `/` - Interactive web interface with API documentation

#### 2. Health Check
- **GET** `/health` - Check API status and driver pool

#### 3. Search All Platforms
- **GET** `/search?query=PRODUCT_NAME&max_results=NUMBER`
- Example: `GET /search?query=iphone%2014&max_results=5`

#### 4. Search Specific Platform
- **GET** `/search/amazon?query=PRODUCT_NAME&max_results=NUMBER`
- **GET** `/search/flipkart?query=PRODUCT_NAME&max_results=NUMBER`
- **GET** `/search/meesho?query=PRODUCT_NAME&max_results=NUMBER`
- **GET** `/search/myntra?query=PRODUCT_NAME&max_results=NUMBER`

### Example API Calls

#### Search All Platforms
```bash
curl "http://localhost:5000/search?query=iphone%2014&max_results=3"
```

#### Search Amazon Only
```bash
curl "http://localhost:5000/search/amazon?query=laptop&max_results=5"
```

### Response Format

```json
{
  "success": true,
  "query": "iphone 14",
  "total_results": 12,
  "results": [
    {
      "site": "Amazon",
      "query": "iphone 14",
      "total_products": 3,
      "products": [
        {
          "title": "Apple iPhone 14",
          "price": "₹79,900",
          "rating": "4.5 out of 5 stars",
          "reviews": "1,234 ratings",
          "availability": "In Stock",
          "link": "https://amazon.in/...",
          "site": "Amazon"
        }
      ]
    }
  ]
}
```

## Web Interface

Visit `http://localhost:5000` to access the interactive web interface where you can:

- 📖 View complete API documentation
- 🧪 Test API endpoints directly
- 🔍 Search products across all platforms
- 📊 View formatted JSON responses

## Configuration

### Environment Variables
- `FLASK_ENV`: Set to `development` for debug mode
- `FLASK_HOST`: Server host (default: 0.0.0.0)
- `FLASK_PORT`: Server port (default: 5000)

### Driver Pool Settings
- Default pool size: 2 drivers
- Maximum pool size: 5 drivers
- Headless mode: Enabled by default

## Error Handling

The API includes comprehensive error handling:

- **400 Bad Request**: Missing or invalid parameters
- **404 Not Found**: Invalid endpoints
- **500 Internal Server Error**: Scraping failures or driver issues

Error responses include detailed error messages and suggestions.

## Performance Tips

1. **Concurrent Requests**: The API uses threading for concurrent platform searches
2. **Driver Pool**: WebDriver instances are reused to improve performance
3. **Headless Mode**: Browsers run in headless mode for faster execution
4. **Result Limiting**: Use `max_results` parameter to limit response size

## Troubleshooting

### Common Issues

1. **ChromeDriver Issues**:
   - Ensure Chrome browser is installed
   - The API automatically downloads ChromeDriver

2. **No Results Found**:
   - Check if the website structure has changed
   - Try different search terms
   - Check network connectivity

3. **Timeout Errors**:
   - Increase wait times in the scraper code
   - Check if websites are accessible

### Logs

The API logs all operations. Check the console output for detailed error messages.

## Development

### Adding New Platforms

1. Create a new scraper class inheriting from `EcommerceScraper`
2. Implement the `search()` method
3. Add the scraper to the `scrapers` dictionary in `app.py`

### Customizing Scrapers

Each scraper can be customized by modifying the selector patterns and extraction logic in the respective scraper classes.

## License

This project is for educational and research purposes. Please respect the terms of service of the websites being scraped.

## Support

For issues and questions:
1. Check the web interface at `http://localhost:5000`
2. Review the console logs for error details
3. Ensure all dependencies are properly installed


