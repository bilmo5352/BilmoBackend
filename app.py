#!/usr/bin/env python3
"""
E-commerce Scraper Flask API
Combines Amazon, Flipkart, Meesho, and Myntra scrapers into a unified API
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json
import time
import threading
from typing import Optional, Dict, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import logging
from datetime import datetime
import os
import shutil
import tempfile
import pymongo
from pymongo import MongoClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# MongoDB Configuration
MONGODB_URI = "mongodb+srv://hrithick:hrimee@0514@goat.kgtnygx.mongodb.net/?retryWrites=true&w=majority&appName=goat"
DB_NAME = "scraper_db"
COLLECTION_NAME = "search_results"

# MongoDB connection
mongodb_client = None
mongodb_db = None
mongodb_collection = None

def connect_mongodb():
    """Connect to MongoDB Atlas"""
    global mongodb_client, mongodb_db, mongodb_collection
    try:
        mongodb_client = MongoClient(MONGODB_URI)
        mongodb_db = mongodb_client[DB_NAME]
        mongodb_collection = mongodb_db[COLLECTION_NAME]
        # Test connection
        mongodb_client.admin.command('ping')
        logger.info("✅ Successfully connected to MongoDB Atlas")
        return True
    except Exception as e:
        logger.error(f"❌ MongoDB connection error: {e}")
        return False

def save_to_mongodb(data, search_type, query, platform=None):
    """Save search results to MongoDB"""
    global mongodb_collection
    if not mongodb_collection:
        if not connect_mongodb():
            return False
    
    try:
        document = {
            "search_type": search_type,
            "query": query,
            "platform": platform,
            "timestamp": datetime.now(),
            "data": data,
            "total_results": len(data) if isinstance(data, list) else 1
        }
        
        result = mongodb_collection.insert_one(document)
        logger.info(f"✅ Saved {search_type} search for '{query}' to MongoDB with ID: {result.inserted_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to save to MongoDB: {e}")
        return False

def cleanup_mongodb():
    """Close MongoDB connection"""
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()
        logger.info("✅ MongoDB connection closed")

# Add cleanup function for graceful shutdown
import atexit

def cleanup_drivers():
    """Clean up all drivers on app shutdown"""
    logger.info("🧹 Cleaning up all drivers...")
    with driver_lock:
        while driver_pool:
            try:
                driver = driver_pool.pop()
                driver.quit()
                logger.info("✅ Driver cleaned up")
            except:
                pass
    logger.info("✅ All drivers cleaned up")

def cleanup_temp_dirs():
    """Clean up all temporary directories"""
    logger.info("🧹 Cleaning up temporary directories...")
    with temp_dirs_lock:
        for temp_dir in temp_dirs[:]:  # Copy list to avoid modification during iteration
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    logger.info(f"✅ Cleaned up temp directory: {temp_dir}")
                temp_dirs.remove(temp_dir)
            except Exception as e:
                logger.warning(f"⚠️ Failed to clean temp directory {temp_dir}: {e}")
    logger.info("✅ All temporary directories cleaned up")

def cleanup_old_json_files():
    """Clean up old JSON files to prevent accumulation"""
    try:
        import glob
        json_files = glob.glob("unified_search_*.json") + glob.glob("*_search_*.json") + glob.glob("*_detailed_*.json")
        
        # Keep only the 10 most recent files
        if len(json_files) > 10:
            # Sort by modification time (newest first)
            json_files.sort(key=os.path.getmtime, reverse=True)
            files_to_delete = json_files[10:]
            
            for file_path in files_to_delete:
                try:
                    os.remove(file_path)
                    logger.info(f"🧹 Deleted old JSON file: {file_path}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to delete {file_path}: {e}")
                    
    except Exception as e:
        logger.warning(f"⚠️ Failed to clean up old JSON files: {e}")

def cleanup_all():
    """Clean up everything"""
    cleanup_drivers()
    cleanup_temp_dirs()
    cleanup_old_json_files()
    cleanup_mongodb()

# Register cleanup function
atexit.register(cleanup_all)

# Global driver pool for concurrent requests
driver_pool = []
driver_lock = threading.Lock()

# Global list to track temporary directories for cleanup
temp_dirs = []
temp_dirs_lock = threading.Lock()

def create_driver(headless: bool = True) -> webdriver.Chrome:
    """Create a Chrome WebDriver with stable settings"""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")
    
    # Essential stability options
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Anti-detection measures
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Memory optimization
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--disable-sync")
    chrome_options.add_argument("--disable-translate")
    chrome_options.add_argument("--hide-scrollbars")
    chrome_options.add_argument("--mute-audio")
    chrome_options.add_argument("--no-first-run")
    
    # Temporary files cleanup - use a single shared directory
    shared_temp_dir = os.path.join(tempfile.gettempdir(), "chrome_scraper_shared")
    chrome_options.add_argument(f"--user-data-dir={shared_temp_dir}")
    chrome_options.add_argument("--disk-cache-size=0")
    chrome_options.add_argument("--media-cache-size=0")
    
    # Additional stability options for Windows
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-features=TranslateUI")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    chrome_options.add_argument("--disable-hang-monitor")
    chrome_options.add_argument("--disable-prompt-on-repost")
    chrome_options.add_argument("--disable-domain-reliability")
    
    # Track shared temporary directory for cleanup
    if shared_temp_dir not in temp_dirs:
        with temp_dirs_lock:
            temp_dirs.append(shared_temp_dir)
    
    # User agent
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        # Try system ChromeDriver first (more reliable on Windows)
            driver = webdriver.Chrome(options=chrome_options)
            logger.info("✅ WebDriver initialized with system ChromeDriver")
    except Exception as e:
        logger.warning(f"⚠️ System ChromeDriver failed: {e}")
        try:
            # Fallback to ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("✅ WebDriver initialized with ChromeDriverManager")
        except Exception as e2:
            logger.error(f"❌ All ChromeDriver methods failed: {e2}")
            raise e2
    
    # Execute JavaScript to remove webdriver properties
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_script("delete navigator.__proto__.webdriver")
    
    return driver

def get_driver():
    """Get a driver from the pool or create a new one"""
    with driver_lock:
        if driver_pool:
            return driver_pool.pop()
        else:
            # Add small delay to prevent driver conflicts
            time.sleep(1)
            return create_driver()

def return_driver(driver):
    """Return a driver to the pool or quit it to save memory"""
    try:
        # Clear browser data to free up memory
        driver.delete_all_cookies()
        driver.execute_script("window.localStorage.clear();")
        driver.execute_script("window.sessionStorage.clear();")
        
        # Use shared temporary directory
        shared_temp_dir = os.path.join(tempfile.gettempdir(), "chrome_scraper_shared")
        
        with driver_lock:
            # Always quit drivers to prevent memory accumulation
            # Only keep 1 driver in pool maximum
            if len(driver_pool) < 1:
                driver_pool.append(driver)
            else:
                driver.quit()
                logger.info("🧹 Driver quit to prevent memory leaks")
                
                # Clean up the shared temporary directory immediately
                if os.path.exists(shared_temp_dir):
                    try:
                        shutil.rmtree(shared_temp_dir, ignore_errors=True)
                        logger.info(f"🧹 Cleaned up shared temp directory: {shared_temp_dir}")
                        # Recreate empty directory for next use
                        os.makedirs(shared_temp_dir, exist_ok=True)
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to clean shared temp directory {shared_temp_dir}: {e}")
                        
    except Exception as e:
        logger.warning(f"Error cleaning up driver: {e}")
        try:
            driver.quit()
        except:
            pass

class EcommerceScraper:
    """Base class for e-commerce scrapers"""
    
    def __init__(self, site_name: str):
        self.site_name = site_name
        self.driver = None
    
    def search(self, query: str, max_results: int = 8) -> Dict:
        """Search for products on the e-commerce site"""
        raise NotImplementedError("Subclasses must implement search method")
    
    def extract_product_details(self, driver: webdriver.Chrome) -> Dict:
        """Extract detailed product information from a product page"""
        raise NotImplementedError("Subclasses must implement extract_product_details method")

class AmazonScraper(EcommerceScraper):
    """Amazon scraper implementation"""
    
    def __init__(self):
        super().__init__("Amazon")
    
    def extract_product_details(self, driver: webdriver.Chrome) -> Dict:
        """Extract detailed product information from an Amazon product page"""
        product_details = {
            "name": "",
            "title": "",
            "price": "",
            "original_price": "",
            "discount": "",
            "brand": "",
            "category": "",
            "rating": "",
            "reviews_count": "",
            "availability": "",
            "link": driver.current_url,
            "images": [],
            "specifications": {}
        }
        
        try:
            time.sleep(3)
            
            # Extract product name and title
            name_selectors = [
                "span#productTitle",
                "h1#title",
                "h1.a-size-large",
                "span[data-automation-id='product-title']",
                "h1[data-automation-id='product-title']",
                "div#titleSection h1",
                "div#titleSection span",
                "h1[class*='product-title']",
                "span[class*='product-title']"
            ]
            
            for selector in name_selectors:
                try:
                    name_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    name_text = name_elem.text.strip()
                    if name_text and len(name_text) > 5:
                        product_details["name"] = name_text
                        product_details["title"] = name_text
                        break
                except:
                    continue
            
            # Extract current price - improved selectors
            price_selectors = [
                "span.a-price-whole",
                "span.a-price.a-text-price",
                "span.a-offscreen",
                "div.a-section.a-spacing-none.aok-align-center span.a-price-whole",
                "span[data-automation-id='product-price']",
                "div[data-automation-id='product-price']",
                "span.a-price.a-text-price.a-size-medium",
                "span.a-price.a-text-price.a-size-large",
                "span.a-price.a-text-price.a-size-base",
                "div.a-section.a-spacing-none.aok-align-center span.a-price-whole",
                "div.a-section.a-spacing-none.aok-align-center span.a-price-symbol",
                "span.a-price-symbol",
                "span.a-price-whole"
            ]
            
            for selector in price_selectors:
                try:
                    price_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    price_text = price_elem.text.strip()
                    if price_text and ('₹' in price_text or 'Rs' in price_text or price_text.replace(',', '').replace('.', '').isdigit()):
                        product_details["price"] = price_text
                        break
                except:
                    continue
            
            # If no price found, try to extract from parent elements
            if not product_details["price"]:
                try:
                    price_elem = driver.find_element(By.CSS_SELECTOR, "span.a-price")
                    price_text = price_elem.text.strip()
                    if price_text and ('₹' in price_text or 'Rs' in price_text):
                        product_details["price"] = price_text
                except:
                    pass
            
            # Extract original price (MRP)
            original_price_selectors = [
                "span.a-price.a-text-price.a-size-base",
                "span.a-text-strike",
                "span[class*='a-text-strike']",
                "div[class*='a-text-strike']",
                "span[class*='a-price-a-text-price']",
                "div[class*='a-price-a-text-price']"
            ]
            
            for selector in original_price_selectors:
                try:
                    price_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    price_text = price_elem.text.strip()
                    if price_text and ('₹' in price_text or 'Rs' in price_text or price_text.replace(',', '').replace('.', '').isdigit()):
                        product_details["original_price"] = price_text
                        break
                except:
                    continue
            
            # Extract discount percentage
            discount_selectors = [
                "span.a-size-large.a-color-price",
                "span[class*='a-color-price']",
                "div[class*='a-color-price']",
                "span[class*='savings']",
                "div[class*='savings']"
            ]
            
            for selector in discount_selectors:
                try:
                    discount_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    discount_text = discount_elem.text.strip()
                    if discount_text and ('%' in discount_text or 'off' in discount_text.lower() or 'save' in discount_text.lower()):
                        product_details["discount"] = discount_text
                        break
                except:
                    continue
            
            # Extract brand
            try:
                brand_selectors = [
                    "a#bylineInfo",
                    "span#bylineInfo",
                    "div#bylineInfo a",
                    "span[data-automation-id='product-brand']",
                    "div[data-automation-id='product-brand']"
                ]
                
                for selector in brand_selectors:
                    try:
                        brand_elem = driver.find_element(By.CSS_SELECTOR, selector)
                        brand_text = brand_elem.text.strip()
                        if brand_text and len(brand_text) < 50:
                            product_details["brand"] = brand_text
                            break
                    except:
                        continue
            except:
                pass
            
            # Extract rating - improved to match JSON format
            rating_selectors = [
                "span.a-icon-alt",
                "div[data-automation-id='product-rating'] span",
                "span[data-automation-id='product-rating']",
                "div#averageCustomerReviews span.a-icon-alt",
                "span[aria-label*='star']",
                "span[aria-label*='out of']",
                "div#averageCustomerReviews",
                "div[data-automation-id='product-rating']",
                "span.a-icon-alt",
                "div.a-section.a-spacing-none.aok-align-center span.a-icon-alt"
            ]
            
            for selector in rating_selectors:
                try:
                    rating_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    rating_text = rating_elem.text.strip()
                    aria_label = rating_elem.get_attribute('aria-label') or ''
                    
                    if rating_text and ('out of' in rating_text.lower() or rating_text.replace('.', '').replace(',', '').isdigit()):
                        product_details["rating"] = rating_text
                        break
                    elif aria_label and ('out of' in aria_label.lower() or 'star' in aria_label.lower()):
                        product_details["rating"] = aria_label
                        break
                except:
                    continue
            
            # If no rating found, try to extract from the entire rating section
            if not product_details["rating"]:
                try:
                    rating_section = driver.find_element(By.CSS_SELECTOR, "div#averageCustomerReviews")
                    rating_text = rating_section.text.strip()
                    if rating_text and ('out of' in rating_text.lower() or 'star' in rating_text.lower()):
                        product_details["rating"] = rating_text
                except:
                    pass
            
            # Extract reviews count - improved to match JSON format
            try:
                review_count_selectors = [
                    "span#acrCustomerReviewText",
                    "a#acrCustomerReviewLink span",
                    "div[data-automation-id='product-reviews-count']",
                    "span[data-automation-id='product-reviews-count']",
                    "a#acrCustomerReviewLink",
                    "span.a-size-base",
                    "div.a-section.a-spacing-none.aok-align-center span.a-size-base"
                ]
                
                for selector in review_count_selectors:
                    try:
                        review_elem = driver.find_element(By.CSS_SELECTOR, selector)
                        review_text = review_elem.text.strip()
                        if review_text and ('rating' in review_text.lower() or 'review' in review_text.lower() or ',' in review_text):
                            product_details["reviews_count"] = review_text
                            break
                    except:
                        continue
            except:
                pass
            
            # Extract availability
            try:
                availability_selectors = [
                    "span#availability span",
                    "div#availability span",
                    "span[data-automation-id='product-availability']",
                    "div[data-automation-id='product-availability']",
                    "span.a-size-medium.a-color-success",
                    "span.a-size-medium.a-color-price"
                ]
                
                for selector in availability_selectors:
                    try:
                        avail_elem = driver.find_element(By.CSS_SELECTOR, selector)
                        avail_text = avail_elem.text.strip()
                        if avail_text and ('stock' in avail_text.lower() or 'available' in avail_text.lower() or 'delivery' in avail_text.lower()):
                            product_details["availability"] = avail_text
                            break
                    except:
                        continue
            except:
                pass
            
            # Extract product images - improved to match JSON format
            try:
                image_selectors = [
                    "img#landingImage",
                    "div#imgTagWrapperId img",
                    "div#altImages img",
                    "div#imageBlock img",
                    "div[data-automation-id='product-image'] img",
                    "div#imageBlockThumbs img",
                    "div#altImages img",
                    "div#imageBlock img",
                    "div#imgTagWrapperId img",
                    "div#altImages img",
                    "div#imageBlock img",
                    "div#imgTagWrapperId img"
                ]
                
                all_images = []
                found_images = set()
                
                for selector in image_selectors:
                    try:
                        images = driver.find_elements(By.CSS_SELECTOR, selector)
                        for img in images:
                            try:
                                img_src = img.get_attribute('src')
                                img_alt = img.get_attribute('alt') or ''
                                
                                if img_src and ('amazon' in img_src.lower() or 'ssl-images' in img_src.lower()) and 'placeholder' not in img_src.lower():
                                    if '._' in img_src:
                                        high_res_src = img_src.replace('._AC_SX679_', '._AC_SX2000_').replace('._AC_SX466_', '._AC_SX2000_').replace('._AC_SX522_', '._AC_SX2000_')
                                    else:
                                        high_res_src = img_src
                                    
                                    if high_res_src not in found_images:
                                        found_images.add(high_res_src)
                                        image_info = {
                                            "url": high_res_src,
                                            "alt": img_alt,
                                            "thumbnail": img_src
                                        }
                                        all_images.append(image_info)
                            except:
                                continue
                    except:
                        continue
                
                product_details["images"] = all_images[:8]
            except:
                product_details["images"] = []
            
            # Extract specifications
            try:
                spec_selectors = [
                    "div#feature-bullets ul li span",
                    "div#productDescription p",
                    "div#detailBullets_feature_div ul li span",
                    "div#productDetails_feature_div table tr",
                    "div#technicalSpecifications_feature_div table tr"
                ]
                
                specifications = {}
                for selector in spec_selectors:
                    try:
                        spec_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for elem in spec_elements:
                            text = elem.text.strip()
                            if text and len(text) > 10 and ':' in text:
                                parts = text.split(':', 1)
                                if len(parts) == 2:
                                    key = parts[0].strip()
                                    value = parts[1].strip()
                                    if key and value:
                                        specifications[key] = value
                        if specifications:
                            break
                    except:
                        continue
                
                product_details["specifications"] = specifications
            except:
                product_details["specifications"] = {}
            
        except Exception as e:
            logger.error(f"Amazon: Error extracting product details: {e}")
        
        return product_details
    
    def search(self, query: str, max_results: int = 8) -> Dict:
        """Search Amazon for products"""
        driver = get_driver()
        try:
            # Navigate to Amazon
            driver.get("https://www.amazon.in")
            wait = WebDriverWait(driver, 15)

            # Wait for page to load completely
            wait.until(EC.presence_of_element_located((By.ID, "twotabsearchtextbox")))

            # Search input
            search_input = driver.find_element(By.ID, "twotabsearchtextbox")
            search_input.clear()
            search_input.send_keys(query)
            search_input.send_keys(Keys.ENTER)

            # Wait for search results to load
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-component-type='s-search-result']")))
            time.sleep(3)  # Additional wait for dynamic content
            
            
            # Extract product information
            products_info = []
            
            # Get all product cards
            product_cards = driver.find_elements(By.CSS_SELECTOR, "[data-component-type='s-search-result']")
            
            if not product_cards:
                # Fallback selectors
                fallback_selectors = [
                    "div.s-result-item",
                    "div[data-asin]",
                    "div.s-card-container"
                ]
                for selector in fallback_selectors:
                    product_cards = driver.find_elements(By.CSS_SELECTOR, selector)
                    if product_cards:
                        break
            
            if not product_cards:
                return {"error": "No product cards found", "products": []}
            
            # Extract information from each product card
            for i, card in enumerate(product_cards[:max_results]):
                try:
                    product_info = {
                        "name": "",
                        "price": "",
                        "brand": "",
                        "category": "",
                        "rating": "",
                        "link": ""
                    }
                    
                    # Extract product link first - comprehensive approach
                    link_selectors = [
                        "h2 a",  # Primary Amazon product link
                        "a[href*='/dp/']",  # Amazon product links
                        "a[href*='/gp/product/']",  # Alternative Amazon product links
                        "a[data-automation-id='product-title']",  # Product title links
                        "a[href*='amazon.in']",  # Any Amazon link
                        "a"  # Any link as fallback
                    ]
                    
                    for selector in link_selectors:
                        try:
                            link_elem = card.find_element(By.CSS_SELECTOR, selector)
                            href = link_elem.get_attribute('href')
                            if href and ('/dp/' in href or '/gp/product/' in href):
                                product_info['link'] = href
                                break
                        except:
                            continue
                    
                    # If still no link, try to find any clickable element
                    if not product_info['link']:
                        try:
                            clickable_elements = card.find_elements(By.TAG_NAME, "a")
                            for elem in clickable_elements:
                                href = elem.get_attribute('href')
                                if href and ('amazon.in' in href or '/dp/' in href):
                                    product_info['link'] = href
                                    break
                        except:
                            pass
                    
                    # Extract product name/title - more comprehensive approach
                    title_selectors = [
                        "h2 a span",  # Primary Amazon title selector
                        "h2 a",       # Alternative title selector
                        "span[data-automation-id='product-title']",
                        "a[data-automation-id='product-title']",
                        "h2[data-automation-id='product-title']",
                        "span.a-size-medium",  # Common Amazon title class
                        "span.a-size-base-plus",  # Another common title class
                        "div[data-automation-id='product-title'] a",
                        "a[href*='/dp/'] span",  # Title within product link
                        "h2 span",  # Generic h2 span
                        "span[class*='title']",  # Any span with title class
                        "div[class*='title']"   # Any div with title class
                    ]
                    
                    for selector in title_selectors:
                        try:
                            title_elem = card.find_element(By.CSS_SELECTOR, selector)
                            title_text = title_elem.text.strip()
                            if title_text and len(title_text) > 5 and len(title_text) < 300:
                                # Filter out non-product text
                                if not any(word in title_text.lower() for word in ['sponsored', 'advertisement', 'best seller', 'amazon choice']):
                                    product_info['name'] = title_text
                                    break
                        except:
                            continue
                    
                    # If still no name, try extracting from card text
                    if not product_info['name']:
                        try:
                            card_text = card.text.strip()
                            lines = card_text.split('\n')
                            for line in lines:
                                line = line.strip()
                                if (line and len(line) > 10 and len(line) < 300 and 
                                    not line.startswith('₹') and 
                                    not line.startswith('Rs') and
                                    not line.endswith('%') and
                                    'off' not in line.lower() and 
                                    'delivery' not in line.lower() and 
                                    'reviews' not in line.lower() and
                                    'rating' not in line.lower() and
                                    'M.R.P:' not in line and
                                    not line.startswith('Best seller') and
                                    not line.startswith('Sponsored') and
                                    not line.startswith('Amazon Choice')):
                                    product_info['name'] = line
                                    break
                        except:
                            pass
                    
                    # Extract price - comprehensive approach for Amazon
                            price_selectors = [
                        "span.a-price-whole",
                                "span.a-price.a-text-price",
                                "span.a-offscreen",
                        ".a-price-range .a-price-whole",
                        "span[class*='price']",
                        "div[class*='price']",
                        "span[class*='cost']",
                        "div[class*='cost']",
                        "span[class*='amount']",
                        "div[class*='amount']"
                    ]
                    
                    for selector in price_selectors:
                        try:
                            price_elem = card.find_element(By.CSS_SELECTOR, selector)
                            price_text = price_elem.text.strip()
                            if price_text and ('₹' in price_text or 'Rs' in price_text or price_text.replace(',', '').replace('.', '').isdigit()):
                                if not price_text.startswith('₹'):
                                    product_info['price'] = f"₹{price_text}"
                                else:
                                    product_info['price'] = price_text
                                break
                        except:
                            continue
                    
                    # Extract original price (MRP) - comprehensive approach for Amazon
                    original_price_selectors = [
                        "span.a-text-strike",
                        "span.a-price.a-text-strike",
                        "span[class*='strike']",
                        "div[class*='strike']",
                        "span[class*='mrp']",
                        "div[class*='mrp']",
                        "span[class*='original']",
                        "div[class*='original']",
                        "span[class*='list']",
                        "div[class*='list']",
                        "span[class*='was']",
                        "div[class*='was']",
                        "span[class*='before']",
                        "div[class*='before']"
                    ]
                    
                    for selector in original_price_selectors:
                        try:
                            orig_elem = card.find_element(By.CSS_SELECTOR, selector)
                            orig_text = orig_elem.text.strip()
                            if orig_text and ('₹' in orig_text or 'Rs' in orig_text or 'INR' in orig_text):
                                product_info['original_price'] = orig_text
                                break
                        except:
                            continue
                    
                    # Try to extract original price from card text content
                    if not product_info.get('original_price'):
                        try:
                            import re
                            card_text = card.text
                            # Look for original price patterns in Amazon
                            orig_price_patterns = [
                                r'MRP[:\s]*₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                                r'M\.R\.P[:\s]*₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                                r'Original[:\s]*₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                                r'Was[:\s]*₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                                r'List[:\s]*₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                                r'₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)\s*₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',  # Two prices
                                r'₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)\s*-\s*₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)'  # Price range
                            ]
                            
                            for pattern in orig_price_patterns:
                                match = re.search(pattern, card_text, re.IGNORECASE)
                                if match:
                                    if len(match.groups()) == 1:
                                        orig_price_value = match.group(1)
                                        product_info['original_price'] = f"₹{orig_price_value}"
                                        break
                                    elif len(match.groups()) == 2:
                                        # If two prices found, use the higher one as original
                                        price1 = int(match.group(1).replace(',', ''))
                                        price2 = int(match.group(2).replace(',', ''))
                                        higher_price = max(price1, price2)
                                        product_info['original_price'] = f"₹{higher_price:,}"
                                        break
                        except:
                            pass
                    
                    # Extract brand - comprehensive approach for Amazon
                    brand_selectors = [
                        "span[data-automation-id='product-brand']",
                        "div[data-automation-id='product-brand']",
                        "span.a-size-base-plus",  # Common Amazon brand class
                        "div.a-size-base-plus",
                        "span[class*='brand']",
                        "div[class*='brand']",
                        "span[class*='manufacturer']",
                        "div[class*='manufacturer']",
                        "span[class*='seller']",
                        "div[class*='seller']"
                    ]
                    
                    for selector in brand_selectors:
                        try:
                            brand_elem = card.find_element(By.CSS_SELECTOR, selector)
                            brand_text = brand_elem.text.strip()
                            if brand_text and len(brand_text) > 1 and len(brand_text) < 50:
                                product_info['brand'] = brand_text
                                break
                        except:
                            continue
                    
                    # If no brand found with selectors, try to extract from product name
                    if not product_info['brand'] and product_info['name']:
                        name_parts = product_info['name'].split()
                        if name_parts:
                            # Common brand names
                            brands = ['Apple', 'Samsung', 'OnePlus', 'Xiaomi', 'Realme', 'Oppo', 'Vivo', 'Nokia', 'Motorola', 'LG', 'Sony', 'HP', 'Dell', 'Lenovo', 'Asus', 'Acer', 'Nike', 'Adidas', 'Puma', 'Reebok', 'Woodland', 'Red Tape', 'Bata', 'Liberty', 'Sparx', 'Campus', 'Bacca Bucci', 'HOCKEY', 'Urbanbox', 'Bruton']
                            for brand in brands:
                                if brand.lower() in product_info['name'].lower():
                                    product_info['brand'] = brand
                                    break
                    
                    # Extract category (try to infer from product name)
                    if product_info['name']:
                        name_lower = product_info['name'].lower()
                        if any(word in name_lower for word in ['phone', 'mobile', 'smartphone', 'iphone', 'galaxy']):
                            product_info['category'] = 'Mobile Phones'
                        elif any(word in name_lower for word in ['laptop', 'notebook', 'computer']):
                            product_info['category'] = 'Laptops'
                        elif any(word in name_lower for word in ['shoes', 'sneakers', 'footwear']):
                            product_info['category'] = 'Shoes'
                        elif any(word in name_lower for word in ['shirt', 't-shirt', 'clothing']):
                            product_info['category'] = 'Clothing'
                        elif any(word in name_lower for word in ['book', 'novel']):
                            product_info['category'] = 'Books'
                        else:
                            product_info['category'] = 'General'
                    
                    # Extract rating - comprehensive approach for Amazon (ACTUAL STAR RATINGS ONLY)
                    rating_selectors = [
                        "a.a-popover-trigger[aria-label*='out of 5 stars']",  # Primary Amazon rating selector
                        "span.a-icon-alt",  # Alternative Amazon rating selector
                        "span[aria-label*='stars']",
                        "div[aria-label*='stars']",
                        "span[aria-label*='out of']",
                        "div[aria-label*='out of']",
                        "a[aria-label*='out of']",
                        "span[class*='a-icon-star']",
                        "div[class*='a-icon-star']",
                        "span[class*='a-star-mini']",
                        "div[class*='a-star-mini']"
                    ]
                    
                    for selector in rating_selectors:
                        try:
                            rating_elem = card.find_element(By.CSS_SELECTOR, selector)
                            rating_text = rating_elem.text.strip()
                            aria_label = rating_elem.get_attribute('aria-label') or ''
                            
                            # Check aria-label first (most reliable for Amazon)
                            if aria_label and ('out of' in aria_label.lower() or 'star' in aria_label.lower()):
                                # Extract just the rating number from aria-label like "4.5 out of 5 stars"
                                import re
                                rating_match = re.search(r'(\d+\.?\d*)\s*out of', aria_label)
                                if rating_match:
                                    product_info['rating'] = rating_match.group(1)
                                    break
                                else:
                                    product_info['rating'] = aria_label
                                    break
                            # Check text content for star ratings only
                            elif rating_text and 'out of' in rating_text.lower() and 'star' in rating_text.lower():
                                product_info['rating'] = rating_text
                                break
                        except:
                            continue
                    
                    # If no rating found with selectors, try XPath
                    if not product_info['rating']:
                        try:
                            rating_xpaths = [
                                "//span[contains(@aria-label, 'out of')]",
                                "//div[contains(@aria-label, 'out of')]",
                                "//span[contains(@aria-label, 'stars')]",
                                "//div[contains(@aria-label, 'stars')]"
                            ]
                            
                            for xpath in rating_xpaths:
                                try:
                                    rating_elem = card.find_element(By.XPATH, xpath)
                                    aria_label = rating_elem.get_attribute('aria-label') or ''
                                    
                                    if aria_label and ('out of' in aria_label.lower() or 'star' in aria_label.lower()):
                                        # Extract just the rating number from aria-label
                                        import re
                                        rating_match = re.search(r'(\d+\.?\d*)\s*out of', aria_label)
                                        if rating_match:
                                            product_info['rating'] = rating_match.group(1)
                                            break
                                        else:
                                            product_info['rating'] = aria_label
                                            break
                                except:
                                    continue
                        except:
                            pass
                    
                    # If still no rating, try to extract from card text content (look for star ratings only)
                    if not product_info['rating']:
                        try:
                            card_text = card.text.strip()
                            lines = card_text.split('\n')
                            for line in lines:
                                line = line.strip()
                                # Look for rating patterns like "4.5 out of 5 stars" - NOT review counts
                                if 'out of' in line.lower() and 'star' in line.lower():
                                    # Extract just the rating number
                                    import re
                                    rating_match = re.search(r'(\d+\.?\d*)\s*out of', line)
                                    if rating_match:
                                        product_info['rating'] = rating_match.group(1)
                                        break
                        except:
                            pass
                    
                    # Extract reviews count
                    review_selectors = [
                        "span.a-size-base",
                        "span[data-automation-id='product-reviews-count']",
                        "div[data-automation-id='product-reviews-count']",
                        "a span.a-size-base",
                    ]
                    
                    for selector in review_selectors:
                        try:
                            review_elem = card.find_element(By.CSS_SELECTOR, selector)
                            review_text = review_elem.text.strip()
                            if review_text and ('rating' in review_text.lower() or 'review' in review_text.lower() or ',' in review_text):
                                product_info['reviews'] = review_text
                                break
                        except:
                            continue
                    
                    # Extract availability
                    availability_selectors = [
                        "span.a-size-small.a-color-success",
                        "span.a-size-small.a-color-price",
                        "span[data-automation-id='product-availability']",
                        "div[data-automation-id='product-availability']",
                    ]
                    
                    for selector in availability_selectors:
                        try:
                            avail_elem = card.find_element(By.CSS_SELECTOR, selector)
                            avail_text = avail_elem.text.strip()
                            if avail_text and ('stock' in avail_text.lower() or 'available' in avail_text.lower() or 'delivery' in avail_text.lower()):
                                product_info['availability'] = avail_text
                                break
                        except:
                            continue
                    
                    # Extract reviews count - comprehensive approach for Amazon
                    reviews_selectors = [
                        "a[href*='reviews']",
                        "span[class*='review']",
                        "div[class*='review']",
                        "span[class*='rating']",
                        "div[class*='rating']",
                        "span[class*='count']",
                        "div[class*='count']",
                        "span[class*='total']",
                        "div[class*='total']",
                        "span[class*='number']",
                        "div[class*='number']",
                        "span[class*='reviews']",
                        "div[class*='reviews']",
                        "span[class*='ratings']",
                        "div[class*='ratings']"
                    ]
                    
                    for selector in reviews_selectors:
                        try:
                            reviews_elem = card.find_element(By.CSS_SELECTOR, selector)
                            reviews_text = reviews_elem.text.strip()
                            if reviews_text and any(word in reviews_text.lower() for word in ['review', 'rating', 'feedback', 'comment']):
                                # Extract number from text like "1,234 reviews" or "123 ratings"
                                import re
                                number_match = re.search(r'(\d+(?:,\d{3})*)', reviews_text)
                                if number_match:
                                    product_info['reviews_count'] = reviews_text
                                    break
                        except:
                            continue
                    
                    # Try to extract reviews count from card text content
                    if not product_info.get('reviews_count'):
                        try:
                            import re
                            card_text = card.text
                            # Look for reviews count patterns in Amazon
                            reviews_patterns = [
                                r'(\d+(?:,\d{3})*)\s*reviews?',
                                r'(\d+(?:,\d{3})*)\s*ratings?',
                                r'(\d+(?:,\d{3})*)\s*feedback',
                                r'(\d+(?:,\d{3})*)\s*comments?',
                                r'(\d+(?:,\d{3})*)\s*★',
                                r'(\d+(?:,\d{3})*)\s*stars?',
                                r'(\d+(?:,\d{3})*)\s*people',
                                r'(\d+(?:,\d{3})*)\s*customers?'
                            ]
                            
                            for pattern in reviews_patterns:
                                match = re.search(pattern, card_text, re.IGNORECASE)
                                if match:
                                    reviews_count = match.group(1)
                                    product_info['reviews_count'] = f"{reviews_count} reviews"
                                    break
                        except:
                            pass
                    
                    # Calculate discount if we have both prices
                    if product_info.get('price') and product_info.get('original_price'):
                        try:
                            import re
                            current_price_text = product_info['price']
                            original_price_text = product_info['original_price']
                            
                            # Extract numbers from price strings
                            current_match = re.search(r'(\d+(?:,\d{3})*)', current_price_text)
                            original_match = re.search(r'(\d+(?:,\d{3})*)', original_price_text)
                            
                            if current_match and original_match:
                                current_price = int(current_match.group(1).replace(',', ''))
                                original_price = int(original_match.group(1).replace(',', ''))
                                
                                if original_price > current_price:
                                    discount_amount = original_price - current_price
                                    discount_percentage = round((discount_amount / original_price) * 100)
                                    product_info['discount'] = f"{discount_percentage}% off"
                                    product_info['discount_amount'] = f"₹{discount_amount:,}"
                        except:
                            pass
                    
                    # Extract image URL - comprehensive approach for Amazon
                    image_selectors = [
                        "img[data-src]",  # Lazy loaded images
                        "img[src]",       # Direct images
                        "img[class*='s-image']",  # Amazon product images
                        "img[class*='product']",  # Product images
                        "img[class*='thumbnail']", # Thumbnail images
                        "img[class*='main']",      # Main images
                        "img[class*='primary']",    # Primary images
                        "img[class*='hero']",      # Hero images
                        "img[class*='gallery']",    # Gallery images
                        "img[class*='carousel']",   # Carousel images
                        "img[alt*='product']",      # Images with product alt text
                        "img[alt*='Product']",      # Images with Product alt text
                        "img"                       # Any image as fallback
                    ]
                    
                    for selector in image_selectors:
                        try:
                            img_elem = card.find_element(By.CSS_SELECTOR, selector)
                            img_src = img_elem.get_attribute('src') or img_elem.get_attribute('data-src') or ''
                            img_alt = img_elem.get_attribute('alt') or ''
                            
                            if img_src and ('amazon' in img_src.lower() or 'ssl-images' in img_src.lower() or 'media-amazon' in img_src.lower()):
                                # Filter out placeholder images
                                if not any(word in img_src.lower() for word in ['placeholder', 'loading', 'spinner', 'default']):
                                    product_info['image_url'] = img_src
                                    product_info['image_alt'] = img_alt
                                break
                        except:
                            continue
                    
                    # If we found any meaningful information, add it
                    if product_info.get('name') or product_info.get('price'):
                        product_info['site'] = 'Amazon'
                        products_info.append(product_info)
                        
                except Exception as e:
                    logger.error(f"Error extracting info from Amazon product {i+1}: {e}")
                    continue
            
            # Extract detailed product information for first few products
            detailed_products = []
            for i, product in enumerate(products_info[:2]):  # Limit to first 2 products
                try:
                    if product.get('link'):
                        logger.info(f"Amazon: Extracting details for product {i+1}: {product.get('title', 'Unknown')}")
                        
                        # Navigate to product page
                        driver.get(product['link'])
                        time.sleep(3)
                        
                        # Extract detailed information
                        detailed_product = self.extract_product_details(driver)
                        detailed_product.update(product)  # Merge with basic info
                        detailed_products.append(detailed_product)
                        
                except Exception as e:
                    logger.error(f"Amazon: Error extracting details for product {i+1}: {e}")
                    continue
            
            # For regular search, return basic structure
            if not hasattr(self, '_detailed_search'):
                return {
                    "site": "Amazon",
                    "query": query,
                    "total_products": len(products_info),
                    "products": products_info
                }
            else:
                # For detailed search, return detailed structure
                return {
                    "site": "Amazon",
                    "query": query,
                    "total_products": len(products_info),
                    "basic_products": products_info,
                    "detailed_products": detailed_products
                }
            
        except Exception as e:
            logger.error(f"Amazon search error: {e}")
            return {"error": str(e), "products": []}
        finally:
            return_driver(driver)

class FlipkartScraper(EcommerceScraper):
    """Flipkart scraper implementation"""
    
    def __init__(self):
        super().__init__("Flipkart")
    
    def extract_product_details(self, driver: webdriver.Chrome) -> Dict:
        """Extract detailed product information from a Flipkart product page"""
        product_details = {
            "name": "",
            "title": "",
            "price": "",
            "original_price": "",
            "discount": "",
            "brand": "",
            "category": "",
            "rating": "",
            "reviews_count": "",
            "availability": "",
            "link": driver.current_url,
            "images": [],
            "specifications": {}
        }
        
        try:
            time.sleep(3)
            
            # Extract product name and title
            name_selectors = [
                "span.B_NuCI",
                "h1[class*='B_NuCI']",
                "h1",
                "span[class*='B_NuCI']",
                "div[class*='B_NuCI']",
                "div[data-automation-id='product-title']",
                "h1[data-automation-id='product-title']",
                "span[data-automation-id='product-title']",
                "h1[class*='product-title']",
                "span[class*='product-title']"
            ]
            
            for selector in name_selectors:
                try:
                    name_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    name_text = name_elem.text.strip()
                    if name_text and len(name_text) > 5:
                        product_details["name"] = name_text
                        product_details["title"] = name_text
                        break
                except:
                    continue
            
            # Extract current price
            price_selectors = [
                "div._30jeq3",
                "div[class*='_30jeq3']",
                "span[class*='_30jeq3']",
                "div[class*='_25b18c']",
                "span[class*='_25b18c']",
                "div[class*='_16Jk6d']",
                "span[class*='_16Jk6d']",
                "div[class*='_1vC4OE']",
                "span[class*='_1vC4OE']",
                "div[data-automation-id='product-price']",
                "span[data-automation-id='product-price']"
            ]
            
            for selector in price_selectors:
                try:
                    price_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    price_text = price_elem.text.strip()
                    if price_text and ('₹' in price_text or 'Rs' in price_text or 'INR' in price_text):
                        product_details["price"] = price_text
                        break
                except:
                    continue
            
            # Extract original price (MRP)
            original_price_selectors = [
                "div._3I9_wc",
                "div[class*='_3I9_wc']",
                "span[class*='_3I9_wc']",
                "div[class*='_3Ay6Sb']",
                "span[class*='_3Ay6Sb']",
                "div[class*='_2TpdnF']",
                "span[class*='_2TpdnF']",
                "div[class*='_3I9_wc']",
                "span[class*='_3I9_wc']"
            ]
            
            for selector in original_price_selectors:
                try:
                    price_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    price_text = price_elem.text.strip()
                    if price_text and ('₹' in price_text or 'Rs' in price_text or 'INR' in price_text):
                        product_details["original_price"] = price_text
                        break
                except:
                    continue
            
            # Extract discount percentage
            discount_selectors = [
                "div._3Ay6Sb",
                "div[class*='_3Ay6Sb']",
                "span[class*='_3Ay6Sb']",
                "div[class*='_2TpdnF']",
                "span[class*='_2TpdnF']",
                "div[class*='_3I9_wc']",
                "span[class*='_3I9_wc']"
            ]
            
            for selector in discount_selectors:
                try:
                    discount_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    discount_text = discount_elem.text.strip()
                    if discount_text and ('%' in discount_text or 'off' in discount_text.lower()):
                        product_details["discount"] = discount_text
                        break
                except:
                    continue
            
            # Extract brand from breadcrumbs or product info
            try:
                brand_selectors = [
                    "a._2whKao",
                    "a[class*='_2whKao']",
                    "nav a",
                    "div[class*='breadcrumb'] a",
                    "ol[class*='breadcrumb'] a",
                    "span[class*='brand']",
                    "div[class*='brand']",
                    "span[class*='Brand']",
                    "div[class*='Brand']"
                ]
                
                breadcrumbs = []
                for selector in brand_selectors:
                    try:
                        breadcrumbs = driver.find_elements(By.CSS_SELECTOR, selector)
                        if breadcrumbs:
                            break
                    except:
                        continue
                
                if breadcrumbs:
                    for crumb in breadcrumbs[1:3]:
                        crumb_text = crumb.text.strip()
                        if crumb_text and len(crumb_text) < 20:
                            product_details["brand"] = crumb_text
                            break
            except:
                pass
            
            # Extract reviews count
            try:
                review_count_selectors = [
                    "span._2_R_DZ",
                    "span[class*='_2_R_DZ']",
                    "div[class*='_2_R_DZ']",
                    "span[class*='review']",
                    "div[class*='review']",
                    "span[class*='rating']",
                    "div[class*='rating']"
                ]
                
                for selector in review_count_selectors:
                    try:
                        review_elem = driver.find_element(By.CSS_SELECTOR, selector)
                        review_text = review_elem.text.strip()
                        if review_text and ('rating' in review_text.lower() or 'review' in review_text.lower() or ',' in review_text):
                            product_details["reviews_count"] = review_text
                            break
                    except:
                        continue
            except:
                pass
            
            # Extract category from breadcrumbs
            try:
                if breadcrumbs:
                    category_text = breadcrumbs[0].text.strip()
                    if category_text:
                        product_details["category"] = category_text
            except:
                pass
            
            # Extract rating
            rating_selectors = [
                "div._3LWZlK",
                "span[class*='_3LWZlK']",
                "div[class*='_3LWZlK']",
                "span[class*='rating']",
                "div[class*='rating']",
                "div[class*='_2d4LTz']",
                "span[class*='_2d4LTz']",
                "div[class*='_3uSWvM']",
                "span[class*='_3uSWvM']",
                "div[data-automation-id='product-rating']",
                "span[data-automation-id='product-rating']"
            ]
            
            for selector in rating_selectors:
                try:
                    rating_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    rating_text = rating_elem.text.strip()
                    if rating_text and rating_text.replace('.', '').replace(',', '').isdigit():
                        product_details["rating"] = rating_text
                        break
                except:
                    continue
            
            # Extract product images
            try:
                image_selectors = [
                    "img._396cs4",
                    "img[class*='_396cs4']",
                    "img._2r_T1I",
                    "img[class*='_2r_T1I']",
                    "img[class*='product-image']",
                    "img[class*='_1BweB8']",
                    "img[class*='_2d1DkJ']",
                    "img[class*='_3exPp9']",
                    "img[class*='_2QcJZg']",
                    "img[class*='_3n6B0X']",
                    "img[class*='_1BweB8']",
                    "img[class*='_2d1DkJ']",
                    "img[class*='_3exPp9']",
                    "img[class*='_2QcJZg']",
                    "img[class*='_3n6B0X']",
                    "img[class*='_1BweB8']",
                    "img[class*='_2d1DkJ']",
                    "img[class*='_3exPp9']",
                    "img[class*='_2QcJZg']",
                    "img[class*='_3n6B0X']"
                ]
                
                all_images = []
                found_images = set()
                
                for selector in image_selectors:
                    try:
                        images = driver.find_elements(By.CSS_SELECTOR, selector)
                        for img in images:
                            try:
                                img_src = img.get_attribute('src')
                                img_alt = img.get_attribute('alt') or ''
                                
                                if img_src and ('flipkart' in img_src.lower() or 'rukminim' in img_src.lower()) and 'placeholder' not in img_src.lower():
                                    if 'image' in img_src and 'q=' in img_src:
                                        high_res_src = img_src.replace('q=70', 'q=100').replace('q=50', 'q=100')
                                    else:
                                        high_res_src = img_src
                                    
                                    if high_res_src not in found_images:
                                        found_images.add(high_res_src)
                                        image_info = {
                                            "url": high_res_src,
                                            "alt": img_alt,
                                            "thumbnail": img_src
                                        }
                                        all_images.append(image_info)
                            except:
                                continue
                    except:
                        continue
                
                product_details["images"] = all_images[:8]
            except:
                product_details["images"] = []
            
        except Exception as e:
            logger.error(f"Flipkart: Error extracting product details: {e}")
        
        return product_details
    
    def close_login_popup(self, driver: webdriver.Chrome, timeout: int = 5):
        """Close Flipkart login popup if present"""
        try:
            wait = WebDriverWait(driver, timeout)
            try:
                close_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button._2KpZ6l._2doB4z")))
                close_btn.click()
                return
            except Exception:
                try:
                    el = driver.find_element(By.XPATH, "//button[contains(., '✕') or contains(., 'Close')]")
                    el.click()
                    return
                except Exception:
                    return
        except TimeoutException:
            return
    
    def search(self, query: str, max_results: int = 8) -> Dict:
        """Search Flipkart for products"""
        driver = get_driver()
        try:
            # Navigate to Flipkart
            driver.get("https://www.flipkart.com")
            wait = WebDriverWait(driver, 15)

            # Close login popup if present
            self.close_login_popup(driver)

            # Wait for search input to be available
            wait.until(EC.presence_of_element_located((By.NAME, "q")))

            # Search input
            search_input = driver.find_element(By.NAME, "q")
            search_input.clear()
            search_input.send_keys(query)
            search_input.send_keys(Keys.ENTER)

            # Wait for search results to load
            print("Waiting for Flipkart search results to load...")
            time.sleep(5)  # Give more time for results to load
            
            # Extract product information
            products_info = []
            
            # Try different selectors for product cards
            product_selectors = [
                "div._1AtVbE",  # Main product card container
                "div[data-id]",  # Generic product containers
                "div._2kHMtA",  # Alternative card selector
                "div._13oc-S",  # Another card selector
            ]
            
            product_cards = []
            for selector in product_selectors:
                try:
                    cards = driver.find_elements(By.CSS_SELECTOR, selector)
                    if cards:
                        product_cards = cards
                        print(f"Found {len(cards)} product cards using selector: {selector}")
                        break
                except Exception:
                    continue
            
            if not product_cards:
                print("No product cards found with standard selectors.")
                return {"error": "No product cards found", "products": []}
            
            # Extract information from each product card
            for i, card in enumerate(product_cards[:max_results]):
                try:
                    product_info = {
                        "name": "",
                        "price": "",
                        "brand": "",
                        "category": "",
                        "rating": "",
                        "link": ""
                    }
                    
                    # Extract product link first - comprehensive approach for Flipkart
                    link_selectors = [
                        "a[href*='/p/']",  # Flipkart product links
                        "a[href*='flipkart.com']",  # Any Flipkart link
                        "a[title]",  # Links with title attribute
                        "a"  # Any link as fallback
                    ]
                    
                    for selector in link_selectors:
                        try:
                            link_elem = card.find_element(By.CSS_SELECTOR, selector)
                            href = link_elem.get_attribute('href')
                            if href and ('flipkart.com' in href or '/p/' in href):
                                product_info['link'] = href
                                break
                        except:
                            continue
                    
                    # More comprehensive title selectors
                    title_selectors = [
                        "div._4rR01T",  # Grid view title
                        "a.s1Q9rs",     # List view title
                        "a[title]",     # Title attribute
                        "div[class*='title']",
                        "span[class*='title']",
                        "a",            # Any link
                        "div[class*='_4rR01T']",  # Alternative grid title
                        "span[class*='_4rR01T']", # Alternative grid title
                        "h3",           # Heading tags
                        "h2",           # Heading tags
                        "h1",           # Heading tags
                    ]
                    
                    for selector in title_selectors:
                        try:
                            title_elem = card.find_element(By.CSS_SELECTOR, selector)
                            title_text = title_elem.text.strip()
                            if title_text and len(title_text) > 5:  # Only use if meaningful text
                                product_info['name'] = title_text
                                # Only set link if we don't have one already
                                if not product_info.get('link'):
                                    product_info['link'] = title_elem.get_attribute('href') or ''
                                break
                        except:
                            continue
                    
                    # More comprehensive price selectors for Flipkart
                    price_selectors = [
                        "div._30jeq3",  # Main price
                        "div[class*='_30jeq3']",
                        "span[class*='_30jeq3']",
                        "div[class*='_25b18c']",  # Alternative price selector
                        "span[class*='_25b18c']", # Alternative price selector
                        "div[class*='_16Jk6d']",  # Another price selector
                        "span[class*='_16Jk6d']",
                        "div[class*='_1vC4OE']",  # Another price selector
                        "span[class*='_1vC4OE']",
                        "div[class*='price']",
                        "span[class*='price']",
                        "div[data-automation-id='product-price']",
                        "span[data-automation-id='product-price']"
                    ]
                    
                    for selector in price_selectors:
                        try:
                            price_elem = card.find_element(By.CSS_SELECTOR, selector)
                            price_text = price_elem.text.strip()
                            if price_text and ('₹' in price_text or 'Rs' in price_text or 'INR' in price_text):
                                product_info['price'] = price_text
                                break
                        except:
                            continue
                    
                    # If no price found with selectors, try XPath
                    if not product_info['price']:
                        try:
                            price_xpaths = [
                                "//div[contains(text(), '₹')]",
                                "//span[contains(text(), '₹')]",
                                "//div[contains(@class, 'price')]",
                                "//span[contains(@class, 'price')]"
                            ]
                            
                            for xpath in price_xpaths:
                                try:
                                    price_elem = card.find_element(By.XPATH, xpath)
                                    price_text = price_elem.text.strip()
                                    if price_text and ('₹' in price_text or 'Rs' in price_text):
                                        product_info['price'] = price_text
                                        break
                                except:
                                    continue
                        except:
                            pass
                    
                    # More comprehensive rating selectors for Flipkart
                    rating_selectors = [
                        "div._3LWZlK",  # Rating stars
                        "span[class*='_3LWZlK']",
                        "div[class*='_3LWZlK']",
                        "span[class*='rating']",
                        "div[class*='rating']",
                        "div[class*='_2d4LTz']",  # Alternative rating selector
                        "span[class*='_2d4LTz']",
                        "div[class*='_3uSWvM']",  # Another rating selector
                        "span[class*='_3uSWvM']",
                        "div[data-automation-id='product-rating']",
                        "span[data-automation-id='product-rating']"
                    ]
                    
                    for selector in rating_selectors:
                        try:
                            rating_elem = card.find_element(By.CSS_SELECTOR, selector)
                            rating_text = rating_elem.text.strip()
                            if rating_text and rating_text.replace('.', '').replace(',', '').isdigit():
                                product_info['rating'] = rating_text
                                break
                        except:
                            continue
                    
                    # If no rating found with selectors, try XPath
                    if not product_info['rating']:
                        try:
                            rating_xpaths = [
                                "//div[contains(@class, 'rating')]",
                                "//span[contains(@class, 'rating')]",
                                "//div[contains(text(), '.') and string-length(text()) < 5]"
                            ]
                            
                            for xpath in rating_xpaths:
                                try:
                                    rating_elem = card.find_element(By.XPATH, xpath)
                                    rating_text = rating_elem.text.strip()
                                    if rating_text and rating_text.replace('.', '').replace(',', '').isdigit():
                                        product_info['rating'] = rating_text
                                        break
                                except:
                                    continue
                        except:
                            pass
                    
                    # If still no rating, try to extract from card text content (Flipkart specific)
                    if not product_info['rating']:
                        try:
                            card_text = card.text.strip()
                            lines = card_text.split('\n')
                            for line in lines:
                                line = line.strip()
                                # Look for Flipkart rating patterns like "4.61,363 Ratings & 99 Reviews"
                                if 'ratings' in line.lower() and 'reviews' in line.lower():
                                    # Extract the rating number from the beginning
                                    import re
                                    rating_match = re.search(r'(\d+\.?\d*)', line)
                                    if rating_match:
                                        product_info['rating'] = rating_match.group(1)
                                        break
                                # Also look for simple rating patterns like "4.5"
                                elif line.replace('.', '').replace(',', '').isdigit() and len(line) <= 5:
                                    product_info['rating'] = line
                                    break
                        except:
                            pass
                    
                    # Extract original price (MRP) - comprehensive approach for Flipkart
                    original_price_selectors = [
                        "div._3I9_wc",  # Flipkart MRP selector
                        "div[class*='_3I9_wc']",
                        "span[class*='_3I9_wc']",
                        "div[class*='_2Tpdn3']",  # Alternative MRP selector
                        "span[class*='_2Tpdn3']",
                        "div[class*='_1vC4OE']",  # Another MRP selector
                        "span[class*='_1vC4OE']",
                        "div[class*='strike']",
                        "span[class*='strike']",
                        "div[class*='mrp']",
                        "span[class*='mrp']",
                        "div[class*='original']",
                        "span[class*='original']",
                        "div[class*='list']",
                        "span[class*='list']",
                        "div[class*='was']",
                        "span[class*='was']",
                        "div[class*='before']",
                        "span[class*='before']"
                    ]
                    
                    for selector in original_price_selectors:
                        try:
                            orig_elem = card.find_element(By.CSS_SELECTOR, selector)
                            orig_text = orig_elem.text.strip()
                            if orig_text and ('₹' in orig_text or 'Rs' in orig_text or 'INR' in orig_text):
                                product_info['original_price'] = orig_text
                                break
                        except:
                            continue
                    
                    # Try to extract original price from card text content
                    if not product_info.get('original_price'):
                        try:
                            import re
                            card_text = card.text
                            # Look for original price patterns in Flipkart
                            orig_price_patterns = [
                                r'MRP[:\s]*₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                                r'M\.R\.P[:\s]*₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                                r'Original[:\s]*₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                                r'Was[:\s]*₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                                r'List[:\s]*₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                                r'₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)\s*₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',  # Two prices
                                r'₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)\s*-\s*₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)'  # Price range
                            ]
                            
                            for pattern in orig_price_patterns:
                                match = re.search(pattern, card_text, re.IGNORECASE)
                                if match:
                                    if len(match.groups()) == 1:
                                        orig_price_value = match.group(1)
                                        product_info['original_price'] = f"₹{orig_price_value}"
                                        break
                                    elif len(match.groups()) == 2:
                                        # If two prices found, use the higher one as original
                                        price1 = int(match.group(1).replace(',', ''))
                                        price2 = int(match.group(2).replace(',', ''))
                                        higher_price = max(price1, price2)
                                        product_info['original_price'] = f"₹{higher_price:,}"
                                        break
                        except:
                            pass
                    
                    # Extract reviews count - comprehensive approach for Flipkart
                    reviews_selectors = [
                        "span._2_R_DZ",  # Flipkart reviews count
                        "span[class*='_2_R_DZ']",
                        "div[class*='_2_R_DZ']",
                        "span[class*='_3LWZlK']",  # Reviews near rating
                        "div[class*='_3LWZlK']",
                        "span[class*='review']",
                        "div[class*='review']",
                        "span[class*='rating']",
                        "div[class*='rating']",
                        "span[class*='count']",
                        "div[class*='count']",
                        "span[class*='total']",
                        "div[class*='total']",
                        "span[class*='number']",
                        "div[class*='number']",
                        "span[class*='reviews']",
                        "div[class*='reviews']",
                        "span[class*='ratings']",
                        "div[class*='ratings']"
                    ]
                    
                    for selector in reviews_selectors:
                        try:
                            reviews_elem = card.find_element(By.CSS_SELECTOR, selector)
                            reviews_text = reviews_elem.text.strip()
                            if reviews_text and any(word in reviews_text.lower() for word in ['review', 'rating', 'feedback', 'comment']):
                                # Extract number from text like "1,234 reviews" or "123 ratings"
                                import re
                                number_match = re.search(r'(\d+(?:,\d{3})*)', reviews_text)
                                if number_match:
                                    product_info['reviews_count'] = reviews_text
                                    break
                        except:
                            continue
                    
                    # Try to extract reviews count from card text content
                    if not product_info.get('reviews_count'):
                        try:
                            import re
                            card_text = card.text
                            # Look for reviews count patterns in Flipkart
                            reviews_patterns = [
                                r'(\d+(?:,\d{3})*)\s*reviews?',
                                r'(\d+(?:,\d{3})*)\s*ratings?',
                                r'(\d+(?:,\d{3})*)\s*feedback',
                                r'(\d+(?:,\d{3})*)\s*comments?',
                                r'(\d+(?:,\d{3})*)\s*★',
                                r'(\d+(?:,\d{3})*)\s*stars?',
                                r'(\d+(?:,\d{3})*)\s*people',
                                r'(\d+(?:,\d{3})*)\s*customers?'
                            ]
                            
                            for pattern in reviews_patterns:
                                match = re.search(pattern, card_text, re.IGNORECASE)
                                if match:
                                    reviews_count = match.group(1)
                                    product_info['reviews_count'] = f"{reviews_count} reviews"
                                    break
                        except:
                            pass
                    
                    # Calculate discount if we have both prices
                    if product_info.get('price') and product_info.get('original_price'):
                        try:
                            import re
                            current_price_text = product_info['price']
                            original_price_text = product_info['original_price']
                            
                            # Extract numbers from price strings
                            current_match = re.search(r'(\d+(?:,\d{3})*)', current_price_text)
                            original_match = re.search(r'(\d+(?:,\d{3})*)', original_price_text)
                            
                            if current_match and original_match:
                                current_price = int(current_match.group(1).replace(',', ''))
                                original_price = int(original_match.group(1).replace(',', ''))
                                
                                if original_price > current_price:
                                    discount_amount = original_price - current_price
                                    discount_percentage = round((discount_amount / original_price) * 100)
                                    product_info['discount'] = f"{discount_percentage}% off"
                                    product_info['discount_amount'] = f"₹{discount_amount:,}"
                        except:
                            pass
                    
                    # Extract image URL - comprehensive approach for Flipkart
                    image_selectors = [
                        "img[data-src]",  # Lazy loaded images
                        "img[src]",       # Direct images
                        "img[class*='_396cs4']",  # Flipkart product images
                        "img[class*='_2r_T1I']",  # Alternative Flipkart images
                        "img[class*='_1Nyybr']",  # Another Flipkart image class
                        "img[class*='product']",  # Product images
                        "img[class*='thumbnail']", # Thumbnail images
                        "img[class*='main']",      # Main images
                        "img[class*='primary']",    # Primary images
                        "img[class*='hero']",      # Hero images
                        "img[class*='gallery']",    # Gallery images
                        "img[class*='carousel']",   # Carousel images
                        "img[alt*='product']",      # Images with product alt text
                        "img[alt*='Product']",      # Images with Product alt text
                        "img"                       # Any image as fallback
                    ]
                    
                    for selector in image_selectors:
                        try:
                            img_elem = card.find_element(By.CSS_SELECTOR, selector)
                            img_src = img_elem.get_attribute('src') or img_elem.get_attribute('data-src') or ''
                            img_alt = img_elem.get_attribute('alt') or ''
                            
                            if img_src and ('flipkart' in img_src.lower() or 'img.fkcdn' in img_src.lower() or 'rukminim2' in img_src.lower()):
                                # Filter out placeholder images
                                if not any(word in img_src.lower() for word in ['placeholder', 'loading', 'spinner', 'default']):
                                    product_info['image_url'] = img_src
                                    product_info['image_alt'] = img_alt
                                    break
                        except:
                            continue
                    
                    # Extract brand - comprehensive approach for Flipkart
                    brand_selectors = [
                        "span[data-automation-id='product-brand']",
                        "div[data-automation-id='product-brand']",
                        "span[class*='brand']",
                        "div[class*='brand']",
                        "span[class*='manufacturer']",
                        "div[class*='manufacturer']",
                        "span[class*='seller']",
                        "div[class*='seller']",
                        "span[class*='company']",
                        "div[class*='company']"
                    ]
                    
                    for selector in brand_selectors:
                        try:
                            brand_elem = card.find_element(By.CSS_SELECTOR, selector)
                            brand_text = brand_elem.text.strip()
                            if brand_text and len(brand_text) > 1 and len(brand_text) < 50:
                                product_info['brand'] = brand_text
                                break
                        except:
                            continue
                    
                    # If no brand found with selectors, try to extract from product name
                    if not product_info['brand'] and product_info['name']:
                        name_parts = product_info['name'].split()
                        if name_parts:
                            # Common brand names - expanded list
                            brands = ['Apple', 'Samsung', 'OnePlus', 'Xiaomi', 'Realme', 'Oppo', 'Vivo', 'Nokia', 'Motorola', 'LG', 'Sony', 'HP', 'Dell', 'Lenovo', 'Asus', 'Acer', 'Nike', 'Adidas', 'Puma', 'Reebok', 'Woodland', 'Red Tape', 'Bata', 'Liberty', 'Sparx', 'Campus', 'Bacca Bucci', 'HOCKEY', 'Urbanbox', 'Bruton', 'MIKE', 'TERFILL', 'BRUTON', 'Crocs', 'Skechers', 'New Balance', 'Converse', 'Vans', 'Under Armour', 'Reebok', 'Fila', 'Kappa', 'Umbro', 'Diadora', 'Lotto', 'Kelme', 'Joma', 'Mizuno', 'Asics', 'Brooks', 'Saucony', 'Hoka', 'Onitsuka Tiger', 'Jordan', 'Air Jordan']
                            for brand in brands:
                                if brand.lower() in product_info['name'].lower():
                                    product_info['brand'] = brand
                                    break
                    
                    # Try to extract brand from product link FIRST (most reliable)
                    if not product_info['brand'] and product_info.get('link'):
                        try:
                            product_url = product_info['link'].lower()
                            for brand in ['nike', 'adidas', 'puma', 'reebok', 'woodland', 'red tape', 'bata', 'liberty', 'sparx', 'campus', 'bacca bucci', 'hockey', 'urbanbox', 'bruton', 'mike', 'terfill', 'asian', 'skechers', 'new balance', 'converse', 'vans', 'under armour', 'fila', 'kappa', 'umbro', 'diadora', 'lotto', 'kelme', 'joma', 'mizuno', 'asics', 'brooks', 'saucony', 'hoka', 'onitsuka tiger', 'jordan', 'air jordan']:
                                if brand in product_url:
                                    product_info['brand'] = brand.title()
                                    break
                        except:
                            pass
                    
                    # Additional brand extraction for Flipkart - look for brand in product name
                    if not product_info['brand'] and product_info['name']:
                        name_lower = product_info['name'].lower()
                        # Common shoe brands that might appear in product names
                        shoe_brands = ['nike', 'adidas', 'puma', 'reebok', 'woodland', 'red tape', 'bata', 'liberty', 'sparx', 'campus', 'bacca bucci', 'hockey', 'urbanbox', 'bruton', 'mike', 'terfill', 'asian', 'skechers', 'new balance', 'converse', 'vans', 'under armour', 'fila', 'kappa', 'umbro', 'diadora', 'lotto', 'kelme', 'joma', 'mizuno', 'asics', 'brooks', 'saucony', 'hoka', 'onitsuka tiger', 'jordan', 'air jordan']
                        for brand in shoe_brands:
                            if brand in name_lower:
                                product_info['brand'] = brand.title()
                                break
                    
                    # If still no brand, try to extract first word from name as brand
                    if not product_info['brand'] and product_info['name']:
                        name_words = product_info['name'].split()
                        for word in name_words:
                            # Skip words that start with numbers or special characters
                            if word and len(word) > 2 and word.isalpha() and not word.startswith('-'):
                                product_info['brand'] = word
                                break
                    
                    # Extract category (try to infer from product name)
                    if product_info['name']:
                        name_lower = product_info['name'].lower()
                        if any(word in name_lower for word in ['phone', 'mobile', 'smartphone', 'iphone', 'galaxy']):
                            product_info['category'] = 'Mobile Phones'
                        elif any(word in name_lower for word in ['laptop', 'notebook', 'computer']):
                            product_info['category'] = 'Laptops'
                        elif any(word in name_lower for word in ['shoes', 'sneakers', 'footwear', 'sandals']):
                            product_info['category'] = 'Shoes'
                        elif any(word in name_lower for word in ['shirt', 't-shirt', 'clothing', 'dress', 'top']):
                            product_info['category'] = 'Clothing'
                        elif any(word in name_lower for word in ['book', 'novel']):
                            product_info['category'] = 'Books'
                        elif any(word in name_lower for word in ['headphone', 'earphone', 'speaker']):
                            product_info['category'] = 'Audio'
                        else:
                            product_info['category'] = 'General'
                    
                    # If we found any meaningful information, add it
                    if product_info.get('name') or product_info.get('price'):
                        product_info['site'] = 'Flipkart'
                        products_info.append(product_info)
                        
                except Exception as e:
                    logger.error(f"Error extracting info from Flipkart product {i+1}: {e}")
                    continue
            
            # Extract detailed product information for first few products
            detailed_products = []
            for i, product in enumerate(products_info[:2]):  # Limit to first 2 products
                try:
                    if product.get('link'):
                        logger.info(f"Flipkart: Extracting details for product {i+1}: {product.get('title', 'Unknown')}")
                        
                        # Navigate to product page
                        driver.get(product['link'])
                        time.sleep(3)
                        
                        # Extract detailed information
                        detailed_product = self.extract_product_details(driver)
                        detailed_product.update(product)  # Merge with basic info
                        detailed_products.append(detailed_product)
                        
                except Exception as e:
                    logger.error(f"Flipkart: Error extracting details for product {i+1}: {e}")
                    continue
            
            return {
                "site": "Flipkart",
                "query": query,
                "total_products": len(products_info),
                "products": products_info
            }
            
        except Exception as e:
            logger.error(f"Flipkart search error: {e}")
            return {"error": str(e), "products": []}
        finally:
            return_driver(driver)

class MeeshoScraper(EcommerceScraper):
    """Meesho scraper implementation"""
    
    def __init__(self):
        super().__init__("Meesho")
    
    def extract_product_details(self, driver: webdriver.Chrome) -> Dict:
        """Extract detailed product information from a Meesho product page"""
        product_details = {
            "name": "",
            "title": "",
            "price": "",
            "original_price": "",
            "discount": "",
            "brand": "",
            "category": "",
            "rating": "",
            "reviews_count": "",
            "availability": "",
            "link": driver.current_url,
            "images": [],
            "specifications": {}
        }
        
        try:
            time.sleep(3)
            
            # Extract product name and title
            name_selectors = [
                "h1[class*='product-title']",
                "h1[class*='ProductTitle']",
                "h1[class*='title']",
                "h1[class*='Title']",
                "h1",
                "div[class*='product-title']",
                "div[class*='ProductTitle']",
                "span[class*='product-title']",
                "span[class*='ProductTitle']",
                "div[class*='title']",
                "span[class*='title']"
            ]
            
            for selector in name_selectors:
                try:
                    name_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    name_text = name_elem.text.strip()
                    if name_text and len(name_text) > 5:
                        product_details["name"] = name_text
                        product_details["title"] = name_text
                        break
                except:
                    continue
            
            # Extract current price
            price_selectors = [
                "span[class*='price']",
                "div[class*='price']",
                "span[class*='selling']",
                "div[class*='selling']",
                "span[class*='Price']",
                "div[class*='Price']",
                "span[class*='Selling']",
                "div[class*='Selling']"
            ]
            
            for selector in price_selectors:
                try:
                    price_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    price_text = price_elem.text.strip()
                    if price_text and ('₹' in price_text or 'Rs' in price_text or 'INR' in price_text):
                        product_details["price"] = price_text
                        break
                except:
                    continue
            
            # Extract original price (MRP)
            original_price_selectors = [
                "span[class*='mrp']",
                "div[class*='mrp']",
                "span[class*='MRP']",
                "div[class*='MRP']",
                "span[class*='original']",
                "div[class*='original']"
            ]
            
            for selector in original_price_selectors:
                try:
                    price_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    price_text = price_elem.text.strip()
                    if price_text and ('₹' in price_text or 'Rs' in price_text or 'INR' in price_text):
                        product_details["original_price"] = price_text
                        break
                except:
                    continue
            
            # Extract discount percentage
            discount_selectors = [
                "span[class*='discount']",
                "div[class*='discount']",
                "span[class*='Discount']",
                "div[class*='Discount']",
                "span[class*='off']",
                "div[class*='off']"
            ]
            
            for selector in discount_selectors:
                try:
                    discount_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    discount_text = discount_elem.text.strip()
                    if discount_text and ('%' in discount_text or 'off' in discount_text.lower() or 'save' in discount_text.lower()):
                        product_details["discount"] = discount_text
                        break
                except:
                    continue
            
            # Extract brand
            try:
                brand_selectors = [
                    "span[class*='brand']",
                    "div[class*='brand']",
                    "span[class*='Brand']",
                    "div[class*='Brand']",
                    "span[class*='seller']",
                    "div[class*='seller']",
                    "span[class*='Seller']",
                    "div[class*='Seller']"
                ]
                
                for selector in brand_selectors:
                    try:
                        brand_elem = driver.find_element(By.CSS_SELECTOR, selector)
                        brand_text = brand_elem.text.strip()
                        if brand_text and len(brand_text) < 50:
                            product_details["brand"] = brand_text
                            break
                    except:
                        continue
            except:
                pass
            
            # Extract category
            try:
                category_selectors = [
                    "span[class*='category']",
                    "div[class*='category']",
                    "span[class*='Category']",
                    "div[class*='Category']",
                    "nav a",
                    "div[class*='breadcrumb'] a",
                    "ol[class*='breadcrumb'] a"
                ]
                
                for selector in category_selectors:
                    try:
                        category_elem = driver.find_element(By.CSS_SELECTOR, selector)
                        category_text = category_elem.text.strip()
                        if category_text and len(category_text) < 30:
                            product_details["category"] = category_text
                            break
                    except:
                        continue
            except:
                pass
            
            # Extract rating
            rating_selectors = [
                "span[class*='rating']",
                "div[class*='rating']",
                "span[class*='Rating']",
                "div[class*='Rating']",
                "span[class*='star']",
                "div[class*='star']",
                "span[class*='Star']",
                "div[class*='Star']",
                "span[class*='review']",
                "div[class*='review']"
            ]
            
            for selector in rating_selectors:
                try:
                    rating_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    rating_text = rating_elem.text.strip()
                    if rating_text and rating_text.replace('.', '').replace(',', '').isdigit():
                        product_details["rating"] = rating_text
                        break
                except:
                    continue
            
            # Extract product images
            try:
                image_selectors = [
                    "img[class*='product-image']",
                    "img[class*='ProductImage']",
                    "img[class*='main-image']",
                    "img[class*='MainImage']",
                    "img[class*='thumbnail']",
                    "img[class*='Thumbnail']",
                    "img[class*='gallery']",
                    "img[class*='Gallery']",
                    "img[class*='carousel']",
                    "img[class*='Carousel']"
                ]
                
                all_images = []
                found_images = set()
                
                for selector in image_selectors:
                    try:
                        images = driver.find_elements(By.CSS_SELECTOR, selector)
                        for img in images:
                            try:
                                img_src = img.get_attribute('src')
                                img_alt = img.get_attribute('alt') or ''
                                
                                if img_src and ('meesho' in img_src.lower() or 'cdn' in img_src.lower()) and 'placeholder' not in img_src.lower():
                                    if high_res_src not in found_images:
                                        found_images.add(img_src)
                                        image_info = {
                                            "url": img_src,
                                            "alt": img_alt,
                                            "thumbnail": img_src
                                        }
                                        all_images.append(image_info)
                            except:
                                continue
                    except:
                        continue
                
                product_details["images"] = all_images[:5]
            except:
                product_details["images"] = []
            
        except Exception as e:
            logger.error(f"Meesho: Error extracting product details: {e}")
        
        return product_details
    
    def search(self, query: str, max_results: int = 8) -> Dict:
        """Search Meesho for products"""
        driver = get_driver()
        try:
            # Try multiple approaches to avoid detection
            approaches = [
                f"https://www.meesho.com/search?q={query.replace(' ', '+')}",
                f"https://www.meesho.com/search?q={query.replace(' ', '%20')}",
                f"https://meesho.com/search?q={query.replace(' ', '+')}"
            ]
            
            success = False
            for search_url in approaches:
                try:
                    logger.info(f"Meesho: Trying URL: {search_url}")
                    driver.get(search_url)
                    time.sleep(5)
                    
                    # Check if we got blocked
                    if "access denied" in driver.title.lower() or "blocked" in driver.title.lower():
                        logger.warning(f"Meesho: Access denied for {search_url}")
                        continue
                    
                    # Check if we're on the right page
                    if "search" in driver.current_url.lower() or "meesho" in driver.title.lower():
                        success = True
                        break
                        
                except Exception as e:
                    logger.warning(f"Meesho: Failed to load {search_url}: {e}")
                    continue
            
            if not success:
                logger.error("Meesho: All search approaches failed")
                return {"error": "Unable to access Meesho - may be blocked", "products": []}
            
            time.sleep(3)  # Additional wait time
            
            # Extract product information
            products_info = []
            
            # More specific selectors for Meesho product cards
            product_selectors = [
                "a[href*='/p/']",  # Product links
                "div[data-testid*='product']",  # Test ID products
                "div[class*='ProductCard']",  # Product card class
                "div[class*='product-card']",  # Alternative product card
                "div[class*='Product']",  # Product class
                "div[class*='product']",  # Generic product
                "div[class*='card']",  # Card class
                "div[class*='item']",  # Item class
                "div[class*='grid']",  # Grid item
                "div[class*='tile']",  # Tile class
                "div[class*='listing']"  # Listing class
            ]
            
            product_cards = []
            for selector in product_selectors:
                try:
                    cards = driver.find_elements(By.CSS_SELECTOR, selector)
                    if cards and len(cards) > 1:
                        product_cards = cards
                        logger.info(f"Meesho: Found {len(cards)} cards with selector: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"Meesho selector {selector} failed: {e}")
                    continue
            
            if not product_cards:
                # Try fallback approach - look for any clickable elements
                logger.warning("Meesho: No product cards found with main selectors, trying fallback...")
                try:
                    # Try to find any elements that might be products
                    fallback_selectors = [
                        "a[href*='meesho.com']",
                        "div[class*='Card']",
                        "div[class*='Tile']",
                        "div[class*='Item']",
                        "div[class*='Box']",
                        "div[class*='Container']",
                        "div[class*='Wrapper']"
                    ]
                    
                    for selector in fallback_selectors:
                        try:
                            cards = driver.find_elements(By.CSS_SELECTOR, selector)
                            if cards and len(cards) > 1:
                                product_cards = cards
                                logger.info(f"Meesho: Found {len(cards)} cards with fallback selector: {selector}")
                                break
                        except:
                            continue
                    
                    if not product_cards:
                        logger.error(f"Meesho: No product cards found. Page title: {driver.title}")
                        logger.error(f"Meesho: Current URL: {driver.current_url}")
                        return {"error": "No product cards found", "products": []}
                except Exception as e:
                    logger.error(f"Meesho: Fallback failed: {e}")
                    return {"error": "No product cards found", "products": []}
            
            # Extract information from each product card
            for i, card in enumerate(product_cards[:max_results]):
                try:
                    product_info = {
                        "name": "",
                        "price": "",
                        "brand": "",
                        "category": "",
                        "rating": "",
                        "link": ""
                    }
                    
                    # Extract product link first
                    link_selectors = [
                        "a[href*='/product/']",
                        "a[href*='meesho.com']",
                        "a[href*='product']"
                    ]
                    
                    for selector in link_selectors:
                        try:
                            link_elem = card.find_element(By.CSS_SELECTOR, selector)
                            href = link_elem.get_attribute('href')
                            if href and 'meesho.com' in href:
                                product_info['link'] = href
                                break
                        except:
                            continue
                    
                    # Extract product name/title
                    name_selectors = [
                        "h3", "h4", "h2", "h1",
                        "a[title]",
                        "div[class*='title']",
                        "span[class*='title']",
                        "div[class*='name']",
                        "span[class*='name']",
                        "div[class*='product-name']",
                        "span[class*='product-name']",
                        "div[class*='product-title']",
                        "span[class*='product-title']",
                        "a", "p"
                    ]
                    
                    for selector in name_selectors:
                        try:
                            name_elem = card.find_element(By.CSS_SELECTOR, selector)
                            name_text = name_elem.text.strip()
                            if (name_text and len(name_text) > 3 and len(name_text) < 200 and
                                not name_text.endswith('%') and
                                not name_text.endswith('off') and
                                not name_text.startswith('%') and
                                'off' not in name_text.lower() and
                                not name_text.startswith('₹') and
                                not name_text.startswith('Rs') and
                                'delivery' not in name_text.lower() and
                                'free' not in name_text.lower()):
                                product_info['name'] = name_text
                                break
                        except:
                            continue
                    
                    # If no name found, try to extract from card text
                    if not product_info['name']:
                        try:
                            card_text = card.text.strip()
                            lines = card_text.split('\n')
                            for line in lines:
                                line = line.strip()
                                if (line and len(line) > 5 and len(line) < 100 and 
                                    not line.startswith('₹') and 
                                    not line.startswith('%') and 
                                    not line.endswith('%') and
                                    not line.endswith('off') and
                                    'off' not in line.lower() and 
                                    'delivery' not in line.lower() and 
                                    'reviews' not in line.lower() and
                                    'rating' not in line.lower() and
                                    'free' not in line.lower() and
                                    ':' not in line and
                                    not line.replace(':', '').replace('h', '').replace('m', '').replace('s', '').replace(' ', '').isdigit()):
                                    product_info['name'] = line
                                    break
                        except:
                            pass
                    
                    # Extract brand - comprehensive approach for Meesho
                    # Try to extract brand from product link FIRST (most reliable)
                    if not product_info['brand'] and product_info.get('link'):
                        try:
                            product_url = product_info['link'].lower()
                            brands = ['nike', 'adidas', 'puma', 'reebok', 'woodland', 'red tape', 'bata', 'liberty', 'sparx', 'campus', 'bacca bucci', 'hockey', 'urbanbox', 'bruton', 'mike', 'terfill', 'asian', 'skechers', 'new balance', 'converse', 'vans', 'under armour', 'fila', 'kappa', 'umbro', 'diadora', 'lotto', 'kelme', 'joma', 'mizuno', 'asics', 'brooks', 'saucony', 'hoka', 'onitsuka tiger', 'jordan', 'air jordan', 'apple', 'samsung', 'oneplus', 'xiaomi', 'realme', 'oppo', 'vivo', 'nokia', 'motorola', 'lg', 'sony', 'hp', 'dell', 'lenovo', 'asus', 'acer', 'infinix', 'itelpower', 'redmi']
                            for brand in brands:
                                if brand in product_url:
                                    product_info['brand'] = brand.title()
                                    break
                        except:
                            pass
                    
                    # Try to extract brand from product name
                    if not product_info['brand'] and product_info['name']:
                        name_lower = product_info['name'].lower()
                        brands = ['nike', 'adidas', 'puma', 'reebok', 'woodland', 'red tape', 'bata', 'liberty', 'sparx', 'campus', 'bacca bucci', 'hockey', 'urbanbox', 'bruton', 'mike', 'terfill', 'asian', 'skechers', 'new balance', 'converse', 'vans', 'under armour', 'fila', 'kappa', 'umbro', 'diadora', 'lotto', 'kelme', 'joma', 'mizuno', 'asics', 'brooks', 'saucony', 'hoka', 'onitsuka tiger', 'jordan', 'air jordan', 'apple', 'samsung', 'oneplus', 'xiaomi', 'realme', 'oppo', 'vivo', 'nokia', 'motorola', 'lg', 'sony', 'hp', 'dell', 'lenovo', 'asus', 'acer', 'infinix', 'itelpower', 'redmi']
                        for brand in brands:
                            if brand in name_lower:
                                product_info['brand'] = brand.title()
                                break
                    
                    # If still no brand, try to extract first word from name as brand
                    if not product_info['brand'] and product_info['name']:
                        name_words = product_info['name'].split()
                        for word in name_words:
                            # Skip words that start with numbers or special characters
                            if word and len(word) > 2 and word.isalpha() and not word.startswith('-'):
                                product_info['brand'] = word
                                break
                    
                    # Extract category (try to infer from product name)
                    if product_info['name']:
                        name_lower = product_info['name'].lower()
                        if any(word in name_lower for word in ['phone', 'mobile', 'smartphone', 'iphone', 'galaxy']):
                            product_info['category'] = 'Mobile Phones'
                        elif any(word in name_lower for word in ['laptop', 'notebook', 'computer']):
                            product_info['category'] = 'Laptops'
                        elif any(word in name_lower for word in ['shoes', 'sneakers', 'footwear', 'sandals']):
                            product_info['category'] = 'Shoes'
                        elif any(word in name_lower for word in ['shirt', 't-shirt', 'clothing', 'dress', 'top', 'pant', 'tshirt']):
                            product_info['category'] = 'Clothing'
                        elif any(word in name_lower for word in ['book', 'novel']):
                            product_info['category'] = 'Books'
                        elif any(word in name_lower for word in ['headphone', 'earphone', 'speaker']):
                            product_info['category'] = 'Audio'
                        else:
                            product_info['category'] = 'General'
                    
                    # Extract price - improved selectors for Meesho
                    price_selectors = [
                        "span[class*='price']",
                        "div[class*='price']",
                        "span[class*='selling']",
                        "div[class*='selling']",
                        "span[class*='mrp']",
                        "div[class*='mrp']",
                        "span[class*='cost']",
                        "div[class*='cost']",
                        "span[class*='amount']",
                        "div[class*='amount']",
                        "span[class*='rupee']",
                        "div[class*='rupee']",
                        "span[class*='rs']",
                        "div[class*='rs']",
                        "span[class*='₹']",
                        "div[class*='₹']",
                        "span[class*='ProductPrice']",
                        "div[class*='ProductPrice']",
                        "span[class*='product-price']",
                        "div[class*='product-price']",
                        "span[class*='selling-price']",
                        "div[class*='selling-price']",
                        "span[class*='current-price']",
                        "div[class*='current-price']"
                    ]
                    
                    for selector in price_selectors:
                        try:
                            price_elem = card.find_element(By.CSS_SELECTOR, selector)
                            price_text = price_elem.text.strip()
                            if price_text and ('₹' in price_text or 'Rs' in price_text or 'INR' in price_text or price_text.replace(',', '').replace('.', '').isdigit()):
                                product_info['price'] = price_text
                                break
                        except:
                            continue
                    
                    # Try to extract price from card text content if selectors fail
                    if not product_info['price']:
                        try:
                            import re
                            card_text = card.text
                            # Look for price patterns in Meesho
                            price_patterns = [
                                r'₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                                r'Rs\.?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                                r'INR\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                                r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*₹',
                                r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*Rs',
                                r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*INR'
                            ]
                            
                            for pattern in price_patterns:
                                match = re.search(pattern, card_text)
                                if match:
                                    price_value = match.group(1)
                                    product_info['price'] = f"₹{price_value}"
                                    break
                        except:
                            pass
                    
                    # Extract rating - improved comprehensive approach for Meesho
                    rating_selectors = [
                        "div[class*='rating']",
                        "span[class*='rating']",
                        "div[class*='star']",
                        "span[class*='star']",
                        "div[class*='review']",
                        "span[class*='review']",
                        "div[class*='score']",
                        "span[class*='score']",
                        "div[class*='average']",
                        "span[class*='average']",
                        "div[class*='rate']",
                        "span[class*='rate']",
                        "div[class*='stars']",
                        "span[class*='stars']",
                        "div[class*='reviews']",
                        "span[class*='reviews']",
                        "div[class*='ratings']",
                        "span[class*='ratings']",
                        "div[class*='feedback']",
                        "span[class*='feedback']",
                        "div[class*='evaluation']",
                        "span[class*='evaluation']",
                        "div[class*='grade']",
                        "span[class*='grade']"
                    ]
                    
                    for selector in rating_selectors:
                        try:
                            rating_elem = card.find_element(By.CSS_SELECTOR, selector)
                            rating_text = rating_elem.text.strip()
                            if rating_text and rating_text.replace('.', '').replace(',', '').isdigit():
                                product_info['rating'] = rating_text
                                break
                        except:
                            continue
                    
                    # Try to extract rating from card text content with improved patterns
                    if not product_info['rating']:
                        try:
                            import re
                            card_text = card.text
                            # Look for rating patterns in Meesho - improved patterns
                            rating_patterns = [
                                r'(\d+\.?\d*)\s*out\s*of\s*5',
                                r'(\d+\.?\d*)\s*★',
                                r'(\d+\.?\d*)\s*stars',
                                r'Rating:\s*(\d+\.?\d*)',
                                r'(\d+\.?\d*)\s*ratings',
                                r'(\d+\.?\d*)\s*reviews',
                                r'(\d+\.?\d*)\s*★\s*\d+',
                                r'(\d+\.?\d*)\s*,\d+\s*Ratings',
                                r'(\d+\.?\d*)\s*★\s*\((\d+)\)',
                                r'(\d+\.?\d*)\s*out\s*of\s*5\s*stars',
                                r'(\d+\.?\d*)\s*★\s*stars',
                                r'(\d+\.?\d*)\s*\/\s*5',
                                r'(\d+\.?\d*)\s*of\s*5',
                                r'(\d+\.?\d*)\s*★\s*\((\d+)\s*ratings\)',
                                r'(\d+\.?\d*)\s*★\s*\((\d+)\s*reviews\)'
                            ]
                            
                            for pattern in rating_patterns:
                                match = re.search(pattern, card_text, re.IGNORECASE)
                                if match:
                                    rating_value = match.group(1)
                                    try:
                                        rating_float = float(rating_value)
                                        if 0 <= rating_float <= 5.0:
                                            product_info['rating'] = rating_value
                                            break
                                    except ValueError:
                                        continue
                        except:
                            pass
                    
                    # Additional aggressive rating extraction methods for Meesho
                    if not product_info.get('rating'):
                        try:
                            import re
                            card_text = card.text
                            
                            # Look for any number that could be a rating (0.0 to 5.0)
                            rating_patterns = [
                                r'\b(\d+\.?\d*)\s*★',
                                r'\b(\d+\.?\d*)\s*stars?',
                                r'\b(\d+\.?\d*)\s*out\s*of\s*5',
                                r'\b(\d+\.?\d*)\s*\/\s*5',
                                r'\b(\d+\.?\d*)\s*of\s*5',
                                r'Rating[:\s]*(\d+\.?\d*)',
                                r'Score[:\s]*(\d+\.?\d*)',
                                r'(\d+\.?\d*)\s*★\s*\((\d+)\)',
                                r'(\d+\.?\d*)\s*★\s*stars?\s*\((\d+)\)',
                                r'(\d+\.?\d*)\s*★\s*\((\d+)\s*ratings?\)',
                                r'(\d+\.?\d*)\s*★\s*\((\d+)\s*reviews?\)'
                            ]
                            
                            for pattern in rating_patterns:
                                match = re.search(pattern, card_text, re.IGNORECASE)
                                if match:
                                    rating_value = match.group(1)
                                    try:
                                        rating_float = float(rating_value)
                                        if 0 <= rating_float <= 5.0:
                                            product_info['rating'] = rating_value
                                            break
                                    except ValueError:
                                        continue
                        except:
                            pass
                    
                    # Extract original price (MRP) - comprehensive approach for Meesho
                    original_price_selectors = [
                        "span[class*='mrp']",
                        "div[class*='mrp']",
                        "span[class*='original']",
                        "div[class*='original']",
                        "span[class*='list']",
                        "div[class*='list']",
                        "span[class*='marked']",
                        "div[class*='marked']",
                        "span[class*='strike']",
                        "div[class*='strike']",
                        "span[class*='cross']",
                        "div[class*='cross']",
                        "span[class*='old']",
                        "div[class*='old']",
                        "span[class*='was']",
                        "div[class*='was']",
                        "span[class*='before']",
                        "div[class*='before']",
                        "span[class*='previous']",
                        "div[class*='previous']"
                    ]
                    
                    for selector in original_price_selectors:
                        try:
                            orig_elem = card.find_element(By.CSS_SELECTOR, selector)
                            orig_text = orig_elem.text.strip()
                            if orig_text and ('₹' in orig_text or 'Rs' in orig_text or 'INR' in orig_text):
                                product_info['original_price'] = orig_text
                                break
                        except:
                            continue
                    
                    # Try to extract original price from card text content
                    if not product_info.get('original_price'):
                        try:
                            import re
                            card_text = card.text
                            # Look for original price patterns in Meesho
                            orig_price_patterns = [
                                r'MRP[:\s]*₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                                r'Original[:\s]*₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                                r'Was[:\s]*₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                                r'List[:\s]*₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                                r'₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)\s*₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',  # Two prices
                                r'₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)\s*-\s*₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)'  # Price range
                            ]
                            
                            for pattern in orig_price_patterns:
                                match = re.search(pattern, card_text, re.IGNORECASE)
                                if match:
                                    if len(match.groups()) == 1:
                                        orig_price_value = match.group(1)
                                        product_info['original_price'] = f"₹{orig_price_value}"
                                        break
                                    elif len(match.groups()) == 2:
                                        # If two prices found, use the higher one as original
                                        price1 = int(match.group(1).replace(',', ''))
                                        price2 = int(match.group(2).replace(',', ''))
                                        higher_price = max(price1, price2)
                                        product_info['original_price'] = f"₹{higher_price:,}"
                                        break
                        except:
                            pass
                    
                    # Extract reviews count - comprehensive approach for Meesho
                    reviews_selectors = [
                        "span[class*='review']",
                        "div[class*='review']",
                        "span[class*='rating']",
                        "div[class*='rating']",
                        "span[class*='count']",
                        "div[class*='count']",
                        "span[class*='total']",
                        "div[class*='total']",
                        "span[class*='number']",
                        "div[class*='number']",
                        "span[class*='reviews']",
                        "div[class*='reviews']",
                        "span[class*='ratings']",
                        "div[class*='ratings']",
                        "span[class*='feedback']",
                        "div[class*='feedback']",
                        "span[class*='comments']",
                        "div[class*='comments']"
                    ]
                    
                    for selector in reviews_selectors:
                        try:
                            reviews_elem = card.find_element(By.CSS_SELECTOR, selector)
                            reviews_text = reviews_elem.text.strip()
                            if reviews_text and any(word in reviews_text.lower() for word in ['review', 'rating', 'feedback', 'comment']):
                                # Extract number from text like "1,234 reviews" or "123 ratings"
                                import re
                                number_match = re.search(r'(\d+(?:,\d{3})*)', reviews_text)
                                if number_match:
                                    product_info['reviews_count'] = reviews_text
                                    break
                        except:
                            continue
                    
                    # Try to extract reviews count from card text content
                    if not product_info.get('reviews_count'):
                        try:
                            import re
                            card_text = card.text
                            # Look for reviews count patterns in Meesho
                            reviews_patterns = [
                                r'(\d+(?:,\d{3})*)\s*reviews?',
                                r'(\d+(?:,\d{3})*)\s*ratings?',
                                r'(\d+(?:,\d{3})*)\s*feedback',
                                r'(\d+(?:,\d{3})*)\s*comments?',
                                r'(\d+(?:,\d{3})*)\s*★',
                                r'(\d+(?:,\d{3})*)\s*stars?',
                                r'(\d+(?:,\d{3})*)\s*people',
                                r'(\d+(?:,\d{3})*)\s*customers?'
                            ]
                            
                            for pattern in reviews_patterns:
                                match = re.search(pattern, card_text, re.IGNORECASE)
                                if match:
                                    reviews_count = match.group(1)
                                    product_info['reviews_count'] = f"{reviews_count} reviews"
                                    break
                        except:
                            pass
                    
                    # Calculate discount if we have both prices
                    if product_info.get('price') and product_info.get('original_price'):
                        try:
                            import re
                            current_price_text = product_info['price']
                            original_price_text = product_info['original_price']
                            
                            # Extract numbers from price strings
                            current_match = re.search(r'(\d+(?:,\d{3})*)', current_price_text)
                            original_match = re.search(r'(\d+(?:,\d{3})*)', original_price_text)
                            
                            if current_match and original_match:
                                current_price = int(current_match.group(1).replace(',', ''))
                                original_price = int(original_match.group(1).replace(',', ''))
                                
                                if original_price > current_price:
                                    discount_amount = original_price - current_price
                                    discount_percentage = round((discount_amount / original_price) * 100)
                                    product_info['discount'] = f"{discount_percentage}% off"
                                    product_info['discount_amount'] = f"₹{discount_amount:,}"
                        except:
                            pass
                    
                    # Extract image URL
                    try:
                        img_elem = card.find_element(By.TAG_NAME, "img")
                        product_info['image_url'] = img_elem.get_attribute('src') or ''
                    except:
                        product_info['image_url'] = ''
                    
                    # Extract product link
                    if not product_info.get('link'):
                        try:
                            if card.tag_name.lower() == 'a':
                                href = card.get_attribute('href')
                                if href and '/p/' in href:
                                    if href.startswith('/'):
                                        href = 'https://www.meesho.com' + href
                                    product_info['link'] = href
                        except:
                            pass
                    
                    # Extract brand from title
                    try:
                        if product_info.get('title'):
                            common_brands = ["Nike", "Adidas", "Puma", "Reebok", "Converse", "Vans", "New Balance", "Under Armour", "Skechers", "Fila", "Jordan", "Champion", "Levi's", "Tommy Hilfiger", "Calvin Klein", "H&M", "Zara", "Forever 21", "Uniqlo", "Gap", "American Eagle", "Hollister", "Abercrombie", "Ralph Lauren", "Lacoste", "Polo"]
                            for brand in common_brands:
                                if brand.lower() in product_info['title'].lower():
                                    product_info['brand'] = brand
                                    break
                    except:
                        pass
                    
                    # If we found any meaningful information, add it
                    if product_info.get('name') or product_info.get('price'):
                        product_info['site'] = 'Meesho'
                        products_info.append(product_info)
                        
                except Exception as e:
                    logger.error(f"Error extracting info from Meesho product {i+1}: {e}")
                    continue
            
            # Extract detailed product information for first few products
            detailed_products = []
            for i, product in enumerate(products_info[:2]):  # Limit to first 2 products
                try:
                    if product.get('link'):
                        logger.info(f"Meesho: Extracting details for product {i+1}: {product.get('title', 'Unknown')}")
                        
                        # Navigate to product page
                        driver.get(product['link'])
                        time.sleep(3)
                        
                        # Extract detailed information
                        detailed_product = self.extract_product_details(driver)
                        detailed_product.update(product)  # Merge with basic info
                        detailed_products.append(detailed_product)
                        
                except Exception as e:
                    logger.error(f"Meesho: Error extracting details for product {i+1}: {e}")
                    continue
            
            return {
                "site": "Meesho",
                "query": query,
                "total_products": len(products_info),
                "basic_products": products_info,
                "detailed_products": detailed_products
            }
            
        except Exception as e:
            logger.error(f"Meesho search error: {e}")
            logger.error(f"Meesho error details - URL: {driver.current_url if driver else 'No driver'}")
            logger.error(f"Meesho error details - Title: {driver.title if driver else 'No driver'}")
            return {"error": str(e), "products": []}
        finally:
            return_driver(driver)

class MyntraScraper(EcommerceScraper):
    """Myntra scraper implementation"""
    
    def __init__(self):
        super().__init__("Myntra")
    
    def extract_product_details(self, driver: webdriver.Chrome) -> Dict:
        """Extract detailed product information from a Myntra product page"""
        product_details = {
            "name": "",
            "price": "",
            "brand": "",
            "category": "",
            "rating": "",
            "link": driver.current_url,
            "images": []
        }
        
        try:
            time.sleep(3)
            
            # Extract product name
            name_selectors = [
                "h1[class*='product-title']",
                "h1[class*='ProductTitle']",
                "h1[class*='title']",
                "h1[class*='Title']",
                "h1",
                "div[class*='product-title']",
                "div[class*='ProductTitle']",
                "span[class*='product-title']",
                "span[class*='ProductTitle']",
                "div[class*='title']",
                "span[class*='title']",
                "h1[class*='pdp-product-name']",
                "div[class*='pdp-product-name']"
            ]
            
            for selector in name_selectors:
                try:
                    name_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    name_text = name_elem.text.strip()
                    if name_text and len(name_text) > 5:
                        product_details["name"] = name_text
                        break
                except:
                    continue
            
            # Extract price
            price_selectors = [
                "span[class*='price']",
                "div[class*='price']",
                "span[class*='selling']",
                "div[class*='selling']",
                "span[class*='mrp']",
                "div[class*='mrp']",
                "span[class*='Price']",
                "div[class*='Price']",
                "span[class*='Selling']",
                "div[class*='Selling']",
                "span[class*='pdp-price']",
                "div[class*='pdp-price']",
                "span[class*='discounted-price']",
                "div[class*='discounted-price']"
            ]
            
            for selector in price_selectors:
                try:
                    price_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    price_text = price_elem.text.strip()
                    if price_text and ('₹' in price_text or 'Rs' in price_text or 'INR' in price_text):
                        product_details["price"] = price_text
                        break
                except:
                    continue
            
            # Extract brand
            try:
                brand_selectors = [
                    "span[class*='brand']",
                    "div[class*='brand']",
                    "span[class*='Brand']",
                    "div[class*='Brand']",
                    "span[class*='seller']",
                    "div[class*='seller']",
                    "span[class*='Seller']",
                    "div[class*='Seller']",
                    "span[class*='pdp-brand']",
                    "div[class*='pdp-brand']",
                    "h1[class*='product-brand']",
                    "span[class*='product-brand']"
                ]
                
                for selector in brand_selectors:
                    try:
                        brand_elem = driver.find_element(By.CSS_SELECTOR, selector)
                        brand_text = brand_elem.text.strip()
                        if brand_text and len(brand_text) < 50:
                            product_details["brand"] = brand_text
                            break
                    except:
                        continue
            except:
                pass
            
            # Extract category
            try:
                category_selectors = [
                    "span[class*='category']",
                    "div[class*='category']",
                    "span[class*='Category']",
                    "div[class*='Category']",
                    "nav a",
                    "div[class*='breadcrumb'] a",
                    "ol[class*='breadcrumb'] a",
                    "span[class*='pdp-category']",
                    "div[class*='pdp-category']"
                ]
                
                for selector in category_selectors:
                    try:
                        category_elem = driver.find_element(By.CSS_SELECTOR, selector)
                        category_text = category_elem.text.strip()
                        if category_text and len(category_text) < 30:
                            product_details["category"] = category_text
                            break
                    except:
                        continue
            except:
                pass
            
            # Extract rating - comprehensive approach for Myntra
            rating_selectors = [
                "span[class*='rating']",
                "div[class*='rating']",
                "span[class*='Rating']",
                "div[class*='Rating']",
                "span[class*='star']",
                "div[class*='star']",
                "span[class*='Star']",
                "div[class*='Star']",
                "span[class*='review']",
                "div[class*='review']",
                "span[class*='pdp-rating']",
                "div[class*='pdp-rating']",
                "span[class*='product-rating']",
                "div[class*='product-rating']",
                "span[class*='average-rating']",
                "div[class*='average-rating']",
                "span[class*='overall-rating']",
                "div[class*='overall-rating']"
            ]
            
            for selector in rating_selectors:
                try:
                    rating_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    rating_text = rating_elem.text.strip()
                    if rating_text and rating_text.replace('.', '').replace(',', '').isdigit():
                        product_details["rating"] = rating_text
                        break
                except:
                    continue
            
            # Try to extract rating from page text content
            if not product_details["rating"]:
                try:
                    import re
                    page_text = driver.page_source
                    # Look for rating patterns in Myntra
                    rating_patterns = [
                        r'(\d+\.?\d*)\s*out\s*of\s*5',
                        r'(\d+\.?\d*)\s*★',
                        r'(\d+\.?\d*)\s*stars',
                        r'Rating:\s*(\d+\.?\d*)',
                        r'(\d+\.?\d*)\s*ratings',
                        r'(\d+\.?\d*)\s*reviews',
                        r'(\d+\.?\d*)\s*★\s*\d+',
                        r'(\d+\.?\d*)\s*,\d+\s*Ratings'
                    ]
                    
                    for pattern in rating_patterns:
                        match = re.search(pattern, page_text, re.IGNORECASE)
                        if match:
                            rating_value = match.group(1)
                            if float(rating_value) <= 5.0:
                                product_details["rating"] = rating_value
                                break
                except:
                    pass
            
            # Extract product images
            try:
                image_selectors = [
                    "img[class*='product-image']",
                    "img[class*='ProductImage']",
                    "img[class*='main-image']",
                    "img[class*='MainImage']",
                    "img[class*='thumbnail']",
                    "img[class*='Thumbnail']",
                    "img[class*='gallery']",
                    "img[class*='Gallery']",
                    "img[class*='carousel']",
                    "img[class*='Carousel']",
                    "img[class*='pdp-image']",
                    "img[class*='PdpImage']"
                ]
                
                all_images = []
                found_images = set()
                
                for selector in image_selectors:
                    try:
                        images = driver.find_elements(By.CSS_SELECTOR, selector)
                        for img in images:
                            try:
                                img_src = img.get_attribute('src')
                                img_alt = img.get_attribute('alt') or ''
                                
                                if img_src and ('myntra' in img_src.lower() or 'cdn' in img_src.lower()) and 'placeholder' not in img_src.lower():
                                    if img_src not in found_images:
                                        found_images.add(img_src)
                                        image_info = {
                                            "url": img_src,
                                            "alt": img_alt,
                                            "thumbnail": img_src
                                        }
                                        all_images.append(image_info)
                            except:
                                continue
                    except:
                        continue
                
                product_details["images"] = all_images[:5]
            except:
                product_details["images"] = []
            
        except Exception as e:
            logger.error(f"Myntra: Error extracting product details: {e}")
        
        return product_details
    
    def search(self, query: str, max_results: int = 8) -> Dict:
        """Search Myntra for products"""
        driver = get_driver()
        try:
            # Try multiple approaches for Myntra
            approaches = [
                f"https://www.myntra.com/{query.replace(' ', '-')}",
                f"https://www.myntra.com/search?q={query.replace(' ', '+')}",
                f"https://www.myntra.com/search?q={query.replace(' ', '%20')}"
            ]
            
            success = False
            for search_url in approaches:
                try:
                    logger.info(f"Myntra: Trying URL: {search_url}")
                    driver.get(search_url)
                    time.sleep(5)
                    
                    # Check if we're on a valid page
                    if ("myntra" in driver.title.lower() and 
                        ("search" in driver.current_url.lower() or 
                         "results" in driver.current_url.lower() or
                         query.lower().replace(' ', '-') in driver.current_url.lower())):
                        success = True
                        break
                        
                except Exception as e:
                    logger.warning(f"Myntra: Failed to load {search_url}: {e}")
                    continue
            
            # If direct URLs don't work, try search form
            if not success:
                logger.info("Myntra: Direct URLs failed, trying search form")
                try:
                    driver.get("https://www.myntra.com")
                    time.sleep(3)
                    wait = WebDriverWait(driver, 10)

                    # Search input - try multiple selectors for Myntra
                    search_input_selectors = [
                        "input[class*='search']",
                        "input[placeholder*='Search']",
                        "input[placeholder*='search']",
                        "input[type='search']",
                        "input[name='search']",
                        "input[class*='desktop-searchBar']",
                        "input[class*='search-bar']",
                        "input[class*='desktop-search']",
                        "input[data-testid*='search']",
                        "input[data-automation-id*='search']",
                        "input"
                    ]
                    
                    search_input = None
                    for selector in search_input_selectors:
                        try:
                            search_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                            logger.info(f"Myntra: Found search input with selector: {selector}")
                            break
                        except:
                            continue
                    
                    if search_input:
                        search_input.clear()
                        search_input.send_keys(query)
                        search_input.send_keys(Keys.ENTER)
                        time.sleep(8)
                        success = True
                    else:
                        logger.error("Myntra: Could not find search input")
                        
                except Exception as e:
                    logger.error(f"Myntra: Search form approach failed: {e}")
            
            if not success:
                logger.error("Myntra: All search approaches failed")
                return {"error": "Unable to search Myntra", "products": []}
            
            # Extract product information
            products_info = []
            
            # More comprehensive selectors for Myntra product cards
            product_selectors = [
                "a[href*='/p/']",  # Product links
                "div[class*='product-productMetaInfo']",  # Product meta info
                "a[class*='product']",  # Product links
                "div[class*='product-base']",  # Product base
                "div[class*='product-card']",  # Product card
                "div[class*='product-item']",  # Product item
                "div[class*='product']",  # Generic product
                "div[class*='ProductCard']",  # Product card class
                "div[class*='Product']",  # Product class
                "div[class*='card']",  # Card class
                "div[class*='item']",  # Item class
                "div[class*='tile']",  # Tile class
                "div[class*='listing']",  # Listing class
                "div[class*='grid']"  # Grid item
            ]
            
            product_cards = []
            for selector in product_selectors:
                try:
                    cards = driver.find_elements(By.CSS_SELECTOR, selector)
                    if cards and len(cards) > 1:
                        product_cards = cards
                        logger.info(f"Myntra: Found {len(cards)} cards with selector: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"Myntra selector {selector} failed: {e}")
                    continue
            
            if not product_cards:
                # Try fallback approach - look for any clickable elements
                logger.warning("Myntra: No product cards found with main selectors, trying fallback...")
                try:
                    # Try to find any elements that might be products
                    fallback_selectors = [
                        "a[href*='myntra.com']",
                        "div[class*='Card']",
                        "div[class*='Tile']",
                        "div[class*='Item']",
                        "div[class*='Box']",
                        "div[class*='Container']",
                        "div[class*='Wrapper']",
                        "div[class*='Base']"
                    ]
                    
                    for selector in fallback_selectors:
                        try:
                            cards = driver.find_elements(By.CSS_SELECTOR, selector)
                            if cards and len(cards) > 1:
                                product_cards = cards
                                logger.info(f"Myntra: Found {len(cards)} cards with fallback selector: {selector}")
                                break
                        except:
                            continue
                    
                    if not product_cards:
                        logger.error(f"Myntra: No product cards found. Page title: {driver.title}")
                        logger.error(f"Myntra: Current URL: {driver.current_url}")
                        return {"error": "No product cards found", "products": []}
                except Exception as e:
                    logger.error(f"Myntra: Fallback failed: {e}")
                    return {"error": "No product cards found", "products": []}
            
            # Extract information from each product card
            for i, card in enumerate(product_cards[:max_results]):
                try:
                    product_info = {
                        "name": "",
                        "price": "",
                        "brand": "",
                        "category": "",
                        "rating": "",
                        "link": ""
                    }
                    
                    # Handle different card types
                    if card.tag_name == 'div' and 'product-productMetaInfo' in card.get_attribute('class'):
                        try:
                            parent_link = card.find_element(By.XPATH, "./ancestor::a")
                            product_info['link'] = parent_link.get_attribute('href') or ''
                            card = parent_link
                        except:
                            pass
                    
                    if card.tag_name == 'a':
                        product_info['link'] = card.get_attribute('href') or ''
                    
                    # Extract title - improved selectors for Myntra
                    title_selectors = [
                        "h3.product-brand",  # Exact brand class
                        "h4.product-product",  # Exact product class
                        "h3[class*='product-brand']",  # Brand class
                        "h4[class*='product-brand']",  # Alternative brand
                        "span[class*='product-brand']",  # Brand span
                        "div[class*='product-brand']",  # Brand div
                        "h3[class*='product-product']",  # Product class
                        "h4[class*='product-product']",  # Alternative product
                        "span[class*='product-product']",  # Product span
                        "div[class*='product-product']",  # Product div
                        "a[class*='product']",  # Product link
                        "h3", "h4", "h2", "h1",  # Generic headings
                        "span[class*='title']",  # Title span
                        "div[class*='title']",  # Title div
                        "span[class*='name']",  # Name span
                        "div[class*='name']",  # Name div
                        "a",  # Any link
                        "p"  # Paragraph tags
                    ]
                    
                    brand_found = False
                    product_name_found = False
                    
                    for selector in title_selectors:
                        try:
                            title_elem = card.find_element(By.CSS_SELECTOR, selector)
                            title_text = title_elem.text.strip()
                            if title_text and len(title_text) > 2:
                                if 'brand' in selector.lower():
                                    product_info['brand'] = title_text
                                    brand_found = True
                                elif 'product' in selector.lower() and not product_name_found:
                                    product_info['name'] = title_text
                                    product_name_found = True
                                elif not product_info.get('name') and len(title_text) > 5:
                                    product_info['name'] = title_text
                                
                                if not product_info.get('link'):
                                    try:
                                        parent_link = title_elem.find_element(By.XPATH, "./ancestor::a")
                                        product_info['link'] = parent_link.get_attribute('href') or ''
                                    except:
                                        try:
                                            link_elem = card.find_element(By.TAG_NAME, "a")
                                            product_info['link'] = link_elem.get_attribute('href') or ''
                                        except:
                                            product_info['link'] = ''
                        except:
                            continue
                    
                    # If still no title found, try to get it from the card's text content
                    if not product_info.get('title'):
                        try:
                            card_text = card.text.strip()
                            if card_text and len(card_text) > 5:
                                # Extract the first meaningful line
                                lines = card_text.split('\n')
                                for line in lines:
                                    line = line.strip()
                                    if (line and len(line) > 5 and 
                                        not line.startswith('Rs.') and
                                        not line.startswith('₹') and
                                        not line.startswith('%') and
                                        not line.endswith('%') and
                                        'off' not in line.lower() and
                                        'delivery' not in line.lower() and
                                        'rating' not in line.lower()):
                                        product_info['title'] = line
                                        break
                        except:
                            pass
                    
                    # Extract price
                    price_selectors = [
                        "span.product-discountedPrice",
                        "span[class*='product-discountedPrice']",
                        "div.product-price span",
                        "span[class*='product-price']",
                        "div[class*='product-price'] span",
                        "span[class*='price']",
                        "div[class*='price'] span",
                    ]
                    
                    for selector in price_selectors:
                        try:
                            price_elem = card.find_element(By.CSS_SELECTOR, selector)
                            price_text = price_elem.text.strip()
                            if price_text and ('₹' in price_text or 'Rs' in price_text or price_text.replace(',', '').replace('.', '').isdigit()):
                                product_info['price'] = price_text
                                break
                        except:
                            continue
                    
                    # Extract original price
                    original_price_selectors = [
                        "span.product-strike",
                        "span[class*='product-strike']",
                        "span[class*='product-mrp']",
                        "div[class*='product-mrp'] span",
                        "span[class*='mrp']",
                        "div[class*='mrp'] span",
                    ]
                    
                    for selector in original_price_selectors:
                        try:
                            price_elem = card.find_element(By.CSS_SELECTOR, selector)
                            price_text = price_elem.text.strip()
                            if price_text and ('₹' in price_text or 'Rs' in price_text):
                                product_info['original_price'] = price_text
                                break
                        except:
                            continue
                    
                    # Extract discount
                    discount_selectors = [
                        "span.product-discountPercentage",
                        "span[class*='product-discountPercentage']",
                        "span[class*='discount']",
                        "div[class*='discount'] span",
                        "span[class*='off']",
                        "div[class*='off'] span",
                    ]
                    
                    for selector in discount_selectors:
                        try:
                            discount_elem = card.find_element(By.CSS_SELECTOR, selector)
                            discount_text = discount_elem.text.strip()
                            if discount_text and ('%' in discount_text or 'off' in discount_text.lower() or 'save' in discount_text.lower()):
                                product_info['discount'] = discount_text
                                break
                        except:
                            continue
                    
                    # Extract category (try to infer from product name)
                    if product_info['name']:
                        name_lower = product_info['name'].lower()
                        if any(word in name_lower for word in ['phone', 'mobile', 'smartphone', 'iphone', 'galaxy']):
                            product_info['category'] = 'Mobile Phones'
                        elif any(word in name_lower for word in ['laptop', 'notebook', 'computer']):
                            product_info['category'] = 'Laptops'
                        elif any(word in name_lower for word in ['shoes', 'sneakers', 'footwear', 'sandals']):
                            product_info['category'] = 'Shoes'
                        elif any(word in name_lower for word in ['shirt', 't-shirt', 'clothing', 'dress', 'top', 'pant', 'tshirt']):
                            product_info['category'] = 'Clothing'
                        elif any(word in name_lower for word in ['book', 'novel']):
                            product_info['category'] = 'Books'
                        elif any(word in name_lower for word in ['headphone', 'earphone', 'speaker']):
                            product_info['category'] = 'Audio'
                        else:
                            product_info['category'] = 'General'
                    
                    # Extract rating - comprehensive approach for Myntra
                    rating_selectors = [
                        "span[class*='rating']",
                        "div[class*='rating'] span",
                        "span[class*='stars']",
                        "div[class*='stars'] span",
                        "span[class*='review']",
                        "div[class*='review'] span",
                        "span[class*='score']",
                        "div[class*='score'] span",
                        "span[class*='average']",
                        "div[class*='average'] span",
                        "span[class*='rate']",
                        "div[class*='rate'] span",
                        "span[class*='stars']",
                        "div[class*='stars'] span",
                        "span[class*='reviews']",
                        "div[class*='reviews'] span",
                        "span[class*='ratings']",
                        "div[class*='ratings'] span",
                        "span[class*='feedback']",
                        "div[class*='feedback'] span",
                        "span[class*='evaluation']",
                        "div[class*='evaluation'] span",
                        "span[class*='grade']",
                        "div[class*='grade'] span"
                    ]
                    
                    for selector in rating_selectors:
                        try:
                            rating_elem = card.find_element(By.CSS_SELECTOR, selector)
                            rating_text = rating_elem.text.strip()
                            if rating_text and (rating_text.replace('.', '').replace(',', '').isdigit() or rating_text.count('.') == 1):
                                try:
                                    rating_value = float(rating_text)
                                    if 0 <= rating_value <= 5:
                                        product_info['rating'] = rating_text
                                        break
                                except ValueError:
                                    continue
                        except:
                            continue
                    
                    # Additional aggressive rating extraction methods for Myntra
                    if not product_info.get('rating'):
                        try:
                            import re
                            card_text = card.text
                            
                            # Look for any number that could be a rating (0.0 to 5.0)
                            rating_patterns = [
                                r'\b(\d+\.?\d*)\s*★',
                                r'\b(\d+\.?\d*)\s*stars?',
                                r'\b(\d+\.?\d*)\s*out\s*of\s*5',
                                r'\b(\d+\.?\d*)\s*\/\s*5',
                                r'\b(\d+\.?\d*)\s*of\s*5',
                                r'Rating[:\s]*(\d+\.?\d*)',
                                r'Score[:\s]*(\d+\.?\d*)',
                                r'(\d+\.?\d*)\s*★\s*\((\d+)\)',
                                r'(\d+\.?\d*)\s*★\s*stars?\s*\((\d+)\)',
                                r'(\d+\.?\d*)\s*★\s*\((\d+)\s*ratings?\)',
                                r'(\d+\.?\d*)\s*★\s*\((\d+)\s*reviews?\)'
                            ]
                            
                            for pattern in rating_patterns:
                                match = re.search(pattern, card_text, re.IGNORECASE)
                                if match:
                                    rating_value = match.group(1)
                                    try:
                                        rating_float = float(rating_value)
                                        if 0 <= rating_float <= 5.0:
                                            product_info['rating'] = rating_value
                                            break
                                    except ValueError:
                                        continue
                        except:
                            pass
                    
                    # Extract reviews count - comprehensive approach for Myntra
                    reviews_selectors = [
                        "span[class*='review']",
                        "div[class*='review']",
                        "span[class*='rating']",
                        "div[class*='rating']",
                        "span[class*='count']",
                        "div[class*='count']",
                        "span[class*='total']",
                        "div[class*='total']",
                        "span[class*='number']",
                        "div[class*='number']",
                        "span[class*='reviews']",
                        "div[class*='reviews']",
                        "span[class*='ratings']",
                        "div[class*='ratings']",
                        "span[class*='feedback']",
                        "div[class*='feedback']",
                        "span[class*='comments']",
                        "div[class*='comments']"
                    ]
                    
                    for selector in reviews_selectors:
                        try:
                            reviews_elem = card.find_element(By.CSS_SELECTOR, selector)
                            reviews_text = reviews_elem.text.strip()
                            if reviews_text and any(word in reviews_text.lower() for word in ['review', 'rating', 'feedback', 'comment']):
                                # Extract number from text like "1,234 reviews" or "123 ratings"
                                import re
                                number_match = re.search(r'(\d+(?:,\d{3})*)', reviews_text)
                                if number_match:
                                    product_info['reviews_count'] = reviews_text
                                    break
                        except:
                            continue
                    
                    # Try to extract reviews count from card text content
                    if not product_info.get('reviews_count'):
                        try:
                            import re
                            card_text = card.text
                            # Look for reviews count patterns in Myntra
                            reviews_patterns = [
                                r'(\d+(?:,\d{3})*)\s*reviews?',
                                r'(\d+(?:,\d{3})*)\s*ratings?',
                                r'(\d+(?:,\d{3})*)\s*feedback',
                                r'(\d+(?:,\d{3})*)\s*comments?',
                                r'(\d+(?:,\d{3})*)\s*★',
                                r'(\d+(?:,\d{3})*)\s*stars?',
                                r'(\d+(?:,\d{3})*)\s*people',
                                r'(\d+(?:,\d{3})*)\s*customers?'
                            ]
                            
                            for pattern in reviews_patterns:
                                match = re.search(pattern, card_text, re.IGNORECASE)
                                if match:
                                    reviews_count = match.group(1)
                                    product_info['reviews_count'] = f"{reviews_count} reviews"
                                    break
                        except:
                            pass
                    
                    # Calculate discount if we have both prices but no discount found
                    if product_info.get('price') and product_info.get('original_price') and not product_info.get('discount'):
                        try:
                            import re
                            current_price_text = product_info['price']
                            original_price_text = product_info['original_price']
                            
                            # Extract numbers from price strings
                            current_match = re.search(r'(\d+(?:,\d{3})*)', current_price_text)
                            original_match = re.search(r'(\d+(?:,\d{3})*)', original_price_text)
                            
                            if current_match and original_match:
                                current_price = int(current_match.group(1).replace(',', ''))
                                original_price = int(original_match.group(1).replace(',', ''))
                                
                                if original_price > current_price:
                                    discount_amount = original_price - current_price
                                    discount_percentage = round((discount_amount / original_price) * 100)
                                    product_info['discount'] = f"{discount_percentage}% off"
                                    product_info['discount_amount'] = f"₹{discount_amount:,}"
                        except:
                            pass
                    
                    # Extract image URL - comprehensive approach for Myntra
                    image_selectors = [
                        "img[data-src]",  # Lazy loaded images
                        "img[src]",       # Direct images
                        "img[class*='img-responsive']",  # Myntra responsive images
                        "img[class*='product-image']",   # Myntra product images
                        "img[class*='ProductImage']",    # Myntra Product images
                        "img[class*='product']",         # Product images
                        "img[class*='thumbnail']",       # Thumbnail images
                        "img[class*='main']",            # Main images
                        "img[class*='primary']",         # Primary images
                        "img[class*='hero']",            # Hero images
                        "img[class*='gallery']",         # Gallery images
                        "img[class*='carousel']",        # Carousel images
                        "img[alt*='product']",          # Images with product alt text
                        "img[alt*='Product']",           # Images with Product alt text
                        "img"                            # Any image as fallback
                    ]
                    
                    for selector in image_selectors:
                        try:
                            img_elem = card.find_element(By.CSS_SELECTOR, selector)
                            img_src = img_elem.get_attribute('src') or img_elem.get_attribute('data-src') or ''
                            img_alt = img_elem.get_attribute('alt') or ''
                            
                            if img_src and ('myntra' in img_src.lower() or 'cdn.myntassets' in img_src.lower() or 'assets.myntassets' in img_src.lower()):
                                # Filter out placeholder images
                                if not any(word in img_src.lower() for word in ['placeholder', 'loading', 'spinner', 'default']):
                                    product_info['image_url'] = img_src
                                    product_info['image_alt'] = img_alt
                                    break
                        except:
                            continue
                    
                    # If we found any meaningful information, add it
                    if product_info.get('name') or product_info.get('price'):
                        product_info['site'] = 'Myntra'
                        products_info.append(product_info)
                        
                except Exception as e:
                    logger.error(f"Error extracting info from Myntra product {i+1}: {e}")
                    continue
            
            # Extract detailed product information for first few products
            detailed_products = []
            for i, product in enumerate(products_info[:2]):  # Limit to first 2 products
                try:
                    if product.get('link'):
                        logger.info(f"Myntra: Extracting details for product {i+1}: {product.get('title', 'Unknown')}")
                        
                        # Navigate to product page
                        driver.get(product['link'])
                        time.sleep(3)
                        
                        # Extract detailed information
                        detailed_product = self.extract_product_details(driver)
                        detailed_product.update(product)  # Merge with basic info
                        detailed_products.append(detailed_product)
                        
                except Exception as e:
                    logger.error(f"Myntra: Error extracting details for product {i+1}: {e}")
                    continue
            
            # Combine basic and detailed products
            all_products = products_info.copy()
            if detailed_products:
                # Replace basic products with detailed ones where available
                for i, detailed in enumerate(detailed_products):
                    if i < len(all_products):
                        all_products[i].update(detailed)
            
            return {
                "site": "Myntra",
                "query": query,
                "total_products": len(all_products),
                "products": all_products
            }
            
        except Exception as e:
            logger.error(f"Myntra search error: {e}")
            logger.error(f"Myntra error details - URL: {driver.current_url if driver else 'No driver'}")
            logger.error(f"Myntra error details - Title: {driver.title if driver else 'No driver'}")
            return {"error": str(e), "products": []}
        finally:
            return_driver(driver)

# Initialize scrapers
scrapers = {
    'amazon': AmazonScraper(),
    'flipkart': FlipkartScraper(),
    'meesho': MeeshoScraper(),
    'myntra': MyntraScraper()
}

@app.route('/')
def home():
    """API info page - no UI, just JSON endpoints"""
    return jsonify({
        "message": "E-commerce Scraper API - JSON Only",
        "description": "No UI - All search results are automatically saved as JSON files and MongoDB",
        "endpoints": {
            "search_all": "GET /search?query=shoes&max_results=5",
            "search_amazon": "GET /search/amazon?query=shoes&max_results=5", 
            "search_flipkart": "GET /search/flipkart?query=shoes&max_results=5",
            "search_meesho": "GET /search/meesho?query=shoes&max_results=5",
            "search_myntra": "GET /search/myntra?query=shoes&max_results=5",
            "detailed_search": "GET /search/amazon/detailed?query=shoes&max_results=3",
            "mongodb_results": "GET /mongodb/results",
            "mongodb_result": "GET /mongodb/results/<result_id>",
            "health": "GET /health",
            "cleanup": "POST /cleanup"
        },
        "note": "All search results are automatically saved as JSON files and MongoDB database",
        "example": "curl 'http://localhost:5000/search?query=shoes&max_results=3'"
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    # Check disk space
    try:
        import shutil
        total, used, free = shutil.disk_usage(".")
        free_gb = free // (1024**3)
        total_gb = total // (1024**3)
        
        # Count JSON files
        import glob
        json_count = len(glob.glob("*.json"))
        
        # Check MongoDB connection
        mongodb_status = "connected" if mongodb_collection else "disconnected"
        mongodb_count = 0
        if mongodb_collection:
            try:
                mongodb_count = mongodb_collection.count_documents({})
            except:
                mongodb_status = "error"
        
        return jsonify({
            "status": "healthy",
            "message": "E-commerce Scraper API is running",
            "available_scrapers": list(scrapers.keys()),
            "driver_pool_size": len(driver_pool),
            "disk_space": {
                "free_gb": free_gb,
                "total_gb": total_gb,
                "usage_percent": round((used / total) * 100, 2)
            },
            "json_files_count": json_count,
            "temp_dirs_count": len(temp_dirs),
            "mongodb": {
                "status": mongodb_status,
                "total_records": mongodb_count
            }
        })
    except Exception as e:
        return jsonify({
            "status": "healthy",
            "message": "E-commerce Scraper API is running",
            "available_scrapers": list(scrapers.keys()),
            "driver_pool_size": len(driver_pool),
            "error": f"Could not check disk space: {e}"
    })

@app.route('/search')
def search_all():
    """Search all e-commerce platforms"""
    query = request.args.get('query')
    max_results = int(request.args.get('max_results', 8))
    
    if not query:
        return jsonify({
            "success": False,
            "error": "Query parameter is required"
        }), 400
    
    try:
        results = []
        
        # Search all platforms concurrently with retry logic
        def search_platform(site_name, scraper):
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.info(f"🔄 Searching {site_name} (attempt {attempt + 1}/{max_retries})")
                    result = scraper.search(query, max_results)
                    if result and (result.get('products') or result.get('basic_products')):
                        logger.info(f"✅ {site_name} search successful - found {len(result.get('products', result.get('basic_products', [])))} products")
                        results.append(result)
                        return
                    else:
                        logger.warning(f"⚠️ {site_name} returned no products, retrying...")
                except Exception as e:
                    logger.error(f"❌ Error searching {site_name} (attempt {attempt + 1}): {e}")
                    if attempt == max_retries - 1:
                        logger.error(f"💥 {site_name} failed after {max_retries} attempts")
                        results.append({
                            "site": site_name,
                            "error": str(e),
                            "products": []
                        })
                    else:
                        time.sleep(2)  # Wait before retry
        
        # Search platforms sequentially to prevent Chrome conflicts
        for site_name, scraper in scrapers.items():
            search_platform(site_name, scraper)
            time.sleep(2)  # Add delay between searches
        
        # Calculate total results
        total_results = sum(len(result.get('products', [])) for result in results)
        
        # Prepare response data
        response_data = {
            "success": True,
            "query": query,
            "total_results": total_results,
            "results": results
        }
        
        # Save results to JSON file
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = query.replace(' ', '_').replace('/', '_').replace('\\', '_')
        filename = f"unified_search_{safe_query}_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Search results saved to: {filename}")
        except Exception as e:
            logger.error(f"Failed to save results to file: {e}")
        
        # Save to MongoDB
        save_to_mongodb(response_data, "unified_search", query)
        
        # Immediately clean up temporary directories to free disk space
        try:
            shared_temp_dir = os.path.join(tempfile.gettempdir(), "chrome_scraper_shared")
            if os.path.exists(shared_temp_dir):
                shutil.rmtree(shared_temp_dir, ignore_errors=True)
                logger.info(f"🧹 Immediate cleanup: freed disk space from {shared_temp_dir}")
                # Recreate empty directory for next use
                os.makedirs(shared_temp_dir, exist_ok=True)
        except Exception as e:
            logger.warning(f"⚠️ Immediate cleanup failed: {e}")
        
        # Clean up old JSON files to prevent accumulation
        cleanup_old_json_files()
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Search all error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/search/<site>')
def search_specific(site):
    """Search specific e-commerce platform"""
    if site not in scrapers:
        return jsonify({
            "success": False,
            "error": f"Unsupported site. Available sites: {list(scrapers.keys())}"
        }), 400
    
    query = request.args.get('query')
    max_results = int(request.args.get('max_results', 8))
    
    if not query:
        return jsonify({
            "success": False,
            "error": "Query parameter is required"
        }), 400
    
    try:
        scraper = scrapers[site]
        result = scraper.search(query, max_results)
        
        # Check if result has an error
        if "error" in result:
            return jsonify({
                "success": False,
                "query": query,
                "error": result["error"],
                "products": []
            })
        
        # Prepare response data
        response_data = {
            "success": True,
            "query": query,
            "site": result.get("site", site),
            "total_products": result.get("total_products", 0),
            "products": result.get("products", [])
        }
        
        # Save results to JSON file
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = query.replace(' ', '_').replace('/', '_').replace('\\', '_')
        filename = f"{site}_search_{safe_query}_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Search results saved to: {filename}")
        except Exception as e:
            logger.error(f"Failed to save results to file: {e}")
        
        # Save to MongoDB
        save_to_mongodb(response_data, "specific_search", query, site)
        
        # Immediately clean up temporary directories to free disk space
        try:
            shared_temp_dir = os.path.join(tempfile.gettempdir(), "chrome_scraper_shared")
            if os.path.exists(shared_temp_dir):
                shutil.rmtree(shared_temp_dir, ignore_errors=True)
                logger.info(f"🧹 Immediate cleanup: freed disk space from {shared_temp_dir}")
                # Recreate empty directory for next use
                os.makedirs(shared_temp_dir, exist_ok=True)
        except Exception as e:
            logger.warning(f"⚠️ Immediate cleanup failed: {e}")
        
        # Clean up old JSON files to prevent accumulation
        cleanup_old_json_files()
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Search {site} error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/search/<site>/detailed')
def search_detailed(site):
    """Search specific e-commerce platform with detailed product information"""
    if site not in scrapers:
        return jsonify({
            "success": False,
            "error": f"Unsupported site. Available sites: {list(scrapers.keys())}"
        }), 400
    
    query = request.args.get('query')
    max_results = int(request.args.get('max_results', 3))  # Limit to 3 for detailed search
    
    if not query:
        return jsonify({
            "success": False,
            "error": "Query parameter is required"
        }), 400
    
    try:
        scraper = scrapers[site]
        # Set flag for detailed search
        scraper._detailed_search = True
        result = scraper.search(query, max_results)
        # Clear flag
        if hasattr(scraper, '_detailed_search'):
            delattr(scraper, '_detailed_search')
        
        # Prepare response data
        response_data = {
            "success": True,
            "query": query,
            "result": result
        }
        
        # Save results to JSON file
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = query.replace(' ', '_').replace('/', '_').replace('\\', '_')
        filename = f"{site}_detailed_{safe_query}_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Detailed search results saved to: {filename}")
        except Exception as e:
            logger.error(f"Failed to save detailed results to file: {e}")
        
        # Save to MongoDB
        save_to_mongodb(response_data, "detailed_search", query, site)
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Detailed search {site} error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/mongodb/results')
def get_mongodb_results():
    """Get all search results from MongoDB"""
    try:
        if not mongodb_collection:
            if not connect_mongodb():
                return jsonify({
                    "success": False,
                    "error": "Failed to connect to MongoDB"
                }), 500
        
        # Get all results, sorted by timestamp (newest first)
        results = list(mongodb_collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(100))
        
        return jsonify({
            "success": True,
            "total_results": len(results),
            "results": results
        })
        
    except Exception as e:
        logger.error(f"MongoDB results error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/mongodb/results/<result_id>')
def get_mongodb_result(result_id):
    """Get specific search result from MongoDB by ID"""
    try:
        if not mongodb_collection:
            if not connect_mongodb():
                return jsonify({
                    "success": False,
                    "error": "Failed to connect to MongoDB"
                }), 500
        
        from pymongo import ObjectId
        result = mongodb_collection.find_one({"_id": ObjectId(result_id)}, {"_id": 0})
        
        if not result:
            return jsonify({
                "success": False,
                "error": "Result not found"
            }), 404
        
        return jsonify({
            "success": True,
            "result": result
        })
        
    except Exception as e:
        logger.error(f"MongoDB result error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/cleanup', methods=['POST'])
def manual_cleanup():
    """Manual cleanup endpoint to free memory and disk space"""
    try:
        cleanup_all()
        return jsonify({"success": True, "message": "All drivers and temporary directories cleaned up successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "available_endpoints": [
            "/",
            "/health",
            "/search",
            "/search/amazon",
            "/search/flipkart", 
            "/search/meesho",
            "/search/myntra"
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500

if __name__ == '__main__':
    logger.info("🚀 Starting Flask API server...")
    logger.info("💡 Memory-optimized mode: Drivers created on-demand")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
