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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global driver pool for concurrent requests
driver_pool = []
driver_lock = threading.Lock()

def create_driver(headless: bool = True) -> webdriver.Chrome:
    """Create a Chrome WebDriver with optimized settings"""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--enable-unsafe-swiftshader")
    
    # Enhanced anti-detection measures
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Additional stealth options
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-client-side-phishing-detection")
    chrome_options.add_argument("--disable-sync")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--disable-hang-monitor")
    chrome_options.add_argument("--disable-prompt-on-repost")
    chrome_options.add_argument("--disable-domain-reliability")
    chrome_options.add_argument("--disable-features=TranslateUI")
    chrome_options.add_argument("--disable-component-extensions-with-background-pages")
    
    # User agent
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("✅ WebDriver initialized successfully")
    except Exception as e:
        logger.warning(f"⚠️ ChromeDriverManager failed: {e}")
        try:
            driver = webdriver.Chrome(options=chrome_options)
            logger.info("✅ WebDriver initialized with system ChromeDriver")
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
            return create_driver()

def return_driver(driver):
    """Return a driver to the pool"""
    with driver_lock:
        if len(driver_pool) < 5:  # Limit pool size
            driver_pool.append(driver)
        else:
            driver.quit()

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
            driver.get("https://www.amazon.in")
            wait = WebDriverWait(driver, 10)

            # Search input
            search_input = wait.until(EC.presence_of_element_located((By.ID, "twotabsearchtextbox")))
            search_input.clear()
            search_input.send_keys(query)
            search_input.send_keys(Keys.ENTER)

            # Wait for search results to load
            time.sleep(8)  # Increased wait time for better element detection
            
            # Extract product information
            products_info = []
            
            # Try different selectors for product cards
            product_selectors = [
                "div[data-component-type='s-search-result']",
                "div.s-result-item",
                "div[data-asin]",
                "div.s-card-container",
            ]
            
            product_cards = []
            for selector in product_selectors:
                try:
                    cards = driver.find_elements(By.CSS_SELECTOR, selector)
                    if cards:
                        product_cards = cards
                        break
                except Exception:
                    continue
            
            if not product_cards:
                return {"error": "No product cards found", "products": []}
            
            # Extract information from each product card
            for i, card in enumerate(product_cards[:max_results]):
                try:
                    product_info = {}
                    
                    # Simplified approach - extract all links and find the best one
                    logger.info(f"Amazon: Starting simplified link extraction for card {i+1}")
                    
                    # Get all links in the card
                    all_links = card.find_elements(By.TAG_NAME, "a")
                    logger.info(f"Amazon: Found {len(all_links)} total links in card")
                    
                    product_link = ""
                    product_title = ""
                    
                    for j, link_elem in enumerate(all_links):
                        try:
                            link = link_elem.get_attribute('href') or ''
                            text = link_elem.text.strip()
                            
                            logger.info(f"Amazon: Link {j+1}: {link[:100]}... (text: '{text[:50]}...')")
                            
                            # Check if this is an Amazon product link
                            if link and ('/dp/' in link or '/gp/product/' in link) and 'amazon.in' in link:
                                if not product_link:
                                    product_link = link
                                    logger.info(f"Amazon: Found product link: {link[:80]}...")
                                
                                # Check if this link has meaningful text (likely the title)
                                if (text and len(text) > 10 and len(text) < 200 and 
                                    not text.startswith('₹') and 
                                    not text.startswith('Rs') and
                                    not text.endswith('%') and
                                    'off' not in text.lower() and 
                                    'delivery' not in text.lower() and 
                                    'reviews' not in text.lower() and
                                    'rating' not in text.lower() and
                                    'M.R.P:' not in text and
                                    not text.startswith('Best seller') and
                                    not text.startswith('5,109') and
                                    not text.startswith('₹47,999')):
                                    product_title = text
                                    logger.info(f"Amazon: Found title '{product_title}'")
                                    break
                        except:
                            continue
                    
                    # Set the results
                    if product_link:
                        product_info['link'] = product_link
                    if product_title:
                        product_info['title'] = product_title
                        
                        # Try alternative title selectors
                        title_selectors = [
                            "h2.a-size-mini a span",
                            "h2.a-size-mini a",
                            "h2 a span",
                            "h2 a",
                            "a[data-automation-id='product-title']",
                            "span[data-automation-id='product-title']",
                            "div[data-automation-id='product-title'] a"
                        ]
                        
                        for selector in title_selectors:
                            try:
                                title_elem = card.find_element(By.CSS_SELECTOR, selector)
                                title_text = title_elem.text.strip()
                                if title_text and len(title_text) > 5:
                                    product_info['title'] = title_text
                                    break
                            except:
                                continue
                    
                    # If no title found, try to extract from card text
                    if not product_info.get('title'):
                        try:
                            card_text = card.text.strip()
                            lines = card_text.split('\n')
                            for line in lines:
                                line = line.strip()
                                if (line and len(line) > 10 and len(line) < 200 and 
                                    not line.startswith('₹') and 
                                    not line.startswith('Rs') and
                                    not line.endswith('%') and
                                    'off' not in line.lower() and 
                                    'delivery' not in line.lower() and 
                                    'reviews' not in line.lower() and
                                    'rating' not in line.lower()):
                                    product_info['title'] = line
                                    break
                        except:
                            pass
                    
                    # If no link found, try to find any product link in the card
                    if not product_info.get('link'):
                        try:
                            link_selectors = [
                                "a[href*='/dp/']",
                                "a[href*='/gp/product/']",
                                "a[href*='amazon.in']",
                                "a[href*='amazon.com']",
                                "a[data-component-type='s-product-image']",
                                "span[data-component-type='s-product-image'] a",
                                "div[data-component-type='s-product-image'] a",
                                "a[data-component-type='s-search-result']",
                                "div[data-component-type='s-search-result'] a",
                                "h2 a",
                                "div[data-asin] a"
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
                        except:
                            pass
                    
                    # If still no link, try to extract from the entire card
                    if not product_info.get('link'):
                        try:
                            all_links = card.find_elements(By.TAG_NAME, "a")
                            for link in all_links:
                                href = link.get_attribute('href')
                                if href and ('/dp/' in href or '/gp/product/' in href):
                                    product_info['link'] = href
                                    break
                        except:
                            pass
                    
                    # Extract price
                    price_selectors = [
                        "span.a-price-whole",
                        "span.a-price.a-text-price",
                        "span.a-offscreen",
                        "span[data-automation-id='product-price']",
                        "div[data-automation-id='product-price']",
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
                    
                    # Extract rating
                    rating_selectors = [
                        "span.a-icon-alt",
                        "span[data-automation-id='product-rating']",
                        "div[data-automation-id='product-rating']",
                        "span.a-icon-star",
                        "span[aria-label*='star']",
                        "span[aria-label*='out of']",
                    ]
                    
                    for selector in rating_selectors:
                        try:
                            rating_elem = card.find_element(By.CSS_SELECTOR, selector)
                            rating_text = rating_elem.text.strip()
                            aria_label = rating_elem.get_attribute('aria-label') or ''
                            title_attr = rating_elem.get_attribute('title') or ''
                            
                            if rating_text and ('out of' in rating_text.lower() or rating_text.replace('.', '').replace(',', '').isdigit()):
                                product_info['rating'] = rating_text
                                break
                            elif aria_label and ('out of' in aria_label.lower() or 'star' in aria_label.lower()):
                                product_info['rating'] = aria_label
                                break
                            elif title_attr and ('out of' in title_attr.lower() or 'star' in title_attr.lower()):
                                product_info['rating'] = title_attr
                                break
                        except:
                            continue
                    
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
                    
                    # If we found any meaningful information, add it
                    if product_info.get('title') or product_info.get('price'):
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
            driver.get("https://www.flipkart.com")
            wait = WebDriverWait(driver, 10)

            # Close login popup if present
            self.close_login_popup(driver)

            # Search input
            search_input = wait.until(EC.presence_of_element_located((By.NAME, "q")))
            search_input.clear()
            search_input.send_keys(query)
            search_input.send_keys(Keys.ENTER)

            # Wait for search results to load
            time.sleep(5)
            
            # Extract product information
            products_info = []
            
            # Try different selectors for product cards
            product_selectors = [
                "div._1AtVbE",
                "div[data-id]",
                "div._2kHMtA",
                "div._13oc-S",
            ]
            
            product_cards = []
            for selector in product_selectors:
                try:
                    cards = driver.find_elements(By.CSS_SELECTOR, selector)
                    if cards:
                        product_cards = cards
                        break
                except Exception:
                    continue
            
            if not product_cards:
                return {"error": "No product cards found", "products": []}
            
            # Extract information from each product card
            for i, card in enumerate(product_cards[:max_results]):
                try:
                    product_info = {}
                    
                    # Extract title
                    title_selectors = [
                        "div._4rR01T",
                        "a.s1Q9rs",
                        "a[title]",
                        "div[class*='title']",
                        "span[class*='title']",
                        "a",
                    ]
                    
                    for selector in title_selectors:
                        try:
                            title_elem = card.find_element(By.CSS_SELECTOR, selector)
                            title_text = title_elem.text.strip()
                            if title_text and len(title_text) > 5:
                                product_info['title'] = title_text
                                product_info['link'] = title_elem.get_attribute('href') or ''
                                break
                        except:
                            continue
                    
                    # Extract price
                    price_selectors = [
                        "div._30jeq3",
                        "div[class*='_30jeq3']",
                        "span[class*='price']",
                        "div[class*='price']",
                        "span[class*='_30jeq3']",
                    ]
                    
                    for selector in price_selectors:
                        try:
                            price_elem = card.find_element(By.CSS_SELECTOR, selector)
                            price_text = price_elem.text.strip()
                            if price_text and ('₹' in price_text or 'Rs' in price_text):
                                product_info['price'] = price_text
                                break
                        except:
                            continue
                    
                    # Extract rating
                    rating_selectors = [
                        "div._3LWZlK",
                        "span[class*='rating']",
                        "div[class*='rating']",
                        "span[class*='_3LWZlK']",
                        "div[class*='_3LWZlK']",
                    ]
                    
                    for selector in rating_selectors:
                        try:
                            rating_elem = card.find_element(By.CSS_SELECTOR, selector)
                            rating_text = rating_elem.text.strip()
                            if rating_text and rating_text.replace('.', '').isdigit():
                                product_info['rating'] = rating_text
                                break
                        except:
                            continue
                    
                    # Extract reviews count
                    review_selectors = [
                        "span._2_R_DZ",
                        "span[class*='review']",
                        "div[class*='review']",
                        "span[class*='_2_R_DZ']",
                        "div[class*='_2_R_DZ']",
                    ]
                    
                    for selector in review_selectors:
                        try:
                            review_elem = card.find_element(By.CSS_SELECTOR, selector)
                            review_text = review_elem.text.strip()
                            if review_text and ('rating' in review_text.lower() or 'review' in review_text.lower()):
                                product_info['reviews'] = review_text
                                break
                        except:
                            continue
                    
                    # Extract discount
                    discount_selectors = [
                        "div._3Ay6Sb",
                        "span[class*='discount']",
                        "div[class*='discount']",
                        "span[class*='_3Ay6Sb']",
                        "div[class*='_3Ay6Sb']",
                    ]
                    
                    for selector in discount_selectors:
                        try:
                            discount_elem = card.find_element(By.CSS_SELECTOR, selector)
                            discount_text = discount_elem.text.strip()
                            if discount_text and ('%' in discount_text or 'off' in discount_text.lower()):
                                product_info['discount'] = discount_text
                                break
                        except:
                            continue
                    
                    # If we found any meaningful information, add it
                    if product_info.get('title') or product_info.get('price'):
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
                "basic_products": products_info,
                "detailed_products": detailed_products
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
                    product_info = {}
                    
                    # Extract title - improved selectors for Meesho
                    title_selectors = [
                        "h3", "h4", "h2", "h1",  # Heading tags
                        "a[title]",  # Title attribute
                        "div[class*='title']",  # Title divs
                        "span[class*='title']",  # Title spans
                        "div[class*='name']",  # Name divs
                        "span[class*='name']",  # Name spans
                        "div[class*='product-name']",  # Product name
                        "span[class*='product-name']",  # Product name span
                        "div[class*='product-title']",  # Product title
                        "span[class*='product-title']",  # Product title span
                        "a",  # Any link
                        "p",  # Paragraph tags
                        "div[class*='text']",  # Text divs
                        "span[class*='text']"  # Text spans
                    ]
                    
                    for selector in title_selectors:
                        try:
                            title_elem = card.find_element(By.CSS_SELECTOR, selector)
                            title_text = title_elem.text.strip()
                            if (title_text and len(title_text) > 3 and len(title_text) < 200 and
                                not title_text.endswith('%') and
                                not title_text.endswith('off') and
                                not title_text.startswith('%') and
                                'off' not in title_text.lower() and
                                not title_text.startswith('₹') and
                                not title_text.startswith('Rs') and
                                'delivery' not in title_text.lower() and
                                'free' not in title_text.lower()):
                                product_info['title'] = title_text
                                try:
                                    product_info['link'] = title_elem.get_attribute('href') or ''
                                except:
                                    pass
                                break
                        except:
                            continue
                    
                    # If no title found, try to extract from card text
                    if not product_info.get('title'):
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
                                    product_info['title'] = line
                                    break
                        except:
                            pass
                    
                    # Extract price
                    price_selectors = [
                        "span[class*='price']",
                        "div[class*='price']",
                        "span[class*='selling']",
                        "div[class*='selling']",
                        "span[class*='mrp']",
                        "div[class*='mrp']",
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
                    
                    # Extract rating
                    rating_selectors = [
                        "div[class*='rating']",
                        "span[class*='rating']",
                        "div[class*='star']",
                        "span[class*='star']",
                        "div[class*='review']",
                        "span[class*='review']",
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
                    if product_info.get('title') or product_info.get('price'):
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
                "div[class*='review']",
                "span[class*='pdp-rating']",
                "div[class*='pdp-rating']"
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
                    product_info = {}
                    
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
                                    product_info['title'] = title_text
                                    product_name_found = True
                                elif not product_info.get('title') and len(title_text) > 5:
                                    product_info['title'] = title_text
                                
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
                    
                    # Extract rating
                    rating_selectors = [
                        "span[class*='rating']",
                        "div[class*='rating'] span",
                        "span[class*='stars']",
                        "div[class*='stars'] span",
                        "span[class*='review']",
                        "div[class*='review'] span"
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
                    
                    # If we found any meaningful information, add it
                    if product_info.get('title') or product_info.get('price'):
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
            
            return {
                "site": "Myntra",
                "query": query,
                "total_products": len(products_info),
                "basic_products": products_info,
                "detailed_products": detailed_products
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
    """Home page with API documentation"""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>E-commerce Scraper API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; margin-bottom: 30px; }
            .api-section { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; background-color: #f9f9f9; }
            .endpoint { background-color: #e8f4f8; padding: 10px; border-radius: 3px; margin: 10px 0; font-family: monospace; }
            .method { background-color: #4CAF50; color: white; padding: 2px 8px; border-radius: 3px; font-size: 12px; }
            .method.post { background-color: #2196F3; }
            .example { background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin: 10px 0; font-family: monospace; font-size: 14px; }
            .test-section { margin-top: 30px; padding: 20px; background-color: #fff3cd; border-radius: 5px; }
            input[type="text"] { padding: 10px; width: 300px; border: 1px solid #ddd; border-radius: 3px; }
            button { padding: 10px 20px; background-color: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer; margin-left: 10px; }
            button:hover { background-color: #0056b3; }
            .result { margin-top: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 5px; border-left: 4px solid #007bff; }
            .error { border-left-color: #dc3545; background-color: #f8d7da; }
            .success { border-left-color: #28a745; background-color: #d4edda; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛍️ E-commerce Scraper API</h1>
            <p style="text-align: center; color: #666; font-size: 18px;">
                Unified API for scraping products from Amazon, Flipkart, Meesho, and Myntra
            </p>
            
            <div class="api-section">
                <h2>📋 Available Endpoints</h2>
                
                <div class="endpoint">
                    <span class="method">GET</span> <strong>/search</strong> - Search products from all platforms
                    <br><small>Parameters: query (required), max_results (optional, default: 8)</small>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <strong>/search/amazon</strong> - Search Amazon only
                    <br><small>Parameters: query (required), max_results (optional, default: 8)</small>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <strong>/search/flipkart</strong> - Search Flipkart only
                    <br><small>Parameters: query (required), max_results (optional, default: 8)</small>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <strong>/search/meesho</strong> - Search Meesho only
                    <br><small>Parameters: query (required), max_results (optional, default: 8)</small>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <strong>/search/myntra</strong> - Search Myntra only
                    <br><small>Parameters: query (required), max_results (optional, default: 8)</small>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <strong>/search/amazon/detailed</strong> - Search Amazon with detailed product info
                    <br><small>Parameters: query (required), max_results (optional, default: 3)</small>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <strong>/search/flipkart/detailed</strong> - Search Flipkart with detailed product info
                    <br><small>Parameters: query (required), max_results (optional, default: 3)</small>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <strong>/search/meesho/detailed</strong> - Search Meesho with detailed product info
                    <br><small>Parameters: query (required), max_results (optional, default: 3)</small>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <strong>/search/myntra/detailed</strong> - Search Myntra with detailed product info
                    <br><small>Parameters: query (required), max_results (optional, default: 3)</small>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span> <strong>/health</strong> - Health check endpoint
                </div>
            </div>
            
            <div class="api-section">
                <h2>📝 Example Usage</h2>
                
                <h3>Search all platforms:</h3>
                <div class="example">
GET /search?query=iphone%2014&max_results=5
                </div>
                
                <h3>Search specific platform:</h3>
                <div class="example">
GET /search/amazon?query=laptop&max_results=10
                </div>
                
                <h3>Response format:</h3>
                <div class="example">
{
  "success": true,
  "total_results": 20,
  "results": [
    {
      "site": "Amazon",
      "query": "iphone 14",
      "total_products": 5,
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
                </div>
            </div>
            
            <div class="test-section">
                <h2>🧪 Test the API</h2>
                <p>Try searching for products:</p>
                <input type="text" id="searchQuery" placeholder="Enter product name (e.g., iphone 14)" value="iphone 14">
                <button onclick="searchAll()">Search All Platforms</button>
                <button onclick="searchAmazon()">Search Amazon</button>
                <button onclick="searchFlipkart()">Search Flipkart</button>
                <button onclick="searchMeesho()">Search Meesho</button>
                <button onclick="searchMyntra()">Search Myntra</button>
                <br><br>
                <button onclick="searchAmazonDetailed()" style="background-color: #28a745;">🔍 Amazon Detailed</button>
                <button onclick="searchFlipkartDetailed()" style="background-color: #28a745;">🔍 Flipkart Detailed</button>
                <button onclick="searchMeeshoDetailed()" style="background-color: #28a745;">🔍 Meesho Detailed</button>
                <button onclick="searchMyntraDetailed()" style="background-color: #28a745;">🔍 Myntra Detailed</button>
                
                <div id="result"></div>
            </div>
        </div>
        
        <script>
            function getQuery() {
                return document.getElementById('searchQuery').value;
            }
            
            function showResult(data, isError = false) {
                const resultDiv = document.getElementById('result');
                resultDiv.className = 'result ' + (isError ? 'error' : 'success');
                
                // Check if this is a detailed search result
                if (!isError && data.success && data.result && data.result.detailed_products) {
                    displayDetailedResults(data);
                } else {
                    resultDiv.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                }
            }
            
            function displayDetailedResults(data) {
                const resultDiv = document.getElementById('result');
                
                const detailedProducts = data.result.detailed_products;
                let html = '<div class="detailed-results">';
                html += '<h3>🔍 Detailed Product Results</h3>';
                html += `<p><strong>Site:</strong> ${data.result.site}</p>`;
                html += `<p><strong>Query:</strong> ${data.result.query}</p>`;
                html += `<p><strong>Total Products Found:</strong> ${data.result.total_products}</p>`;
                html += `<p><strong>Detailed Products:</strong> ${detailedProducts.length}</p><br>`;
                
                detailedProducts.forEach((product, index) => {
                    html += `<div class="product-card" style="border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 8px; background: #f9f9f9;">`;
                    html += `<h4 style="color: #333; margin-top: 0;">${index + 1}. ${product.name || product.title || 'Product Name'}</h4>`;
                    
                    if (product.price) {
                        html += `<p><strong>Price:</strong> <span style="color: #e74c3c; font-size: 1.2em;">${product.price}</span></p>`;
                    }
                    
                    if (product.brand) {
                        html += `<p><strong>Brand:</strong> ${product.brand}</p>`;
                    }
                    
                    if (product.category) {
                        html += `<p><strong>Category:</strong> ${product.category}</p>`;
                    }
                    
                    if (product.rating) {
                        html += `<p><strong>Rating:</strong> ⭐ ${product.rating}</p>`;
                    }
                    
                    if (product.reviews_count) {
                        html += `<p><strong>Reviews:</strong> ${product.reviews_count}</p>`;
                    }
                    
                    if (product.availability) {
                        html += `<p><strong>Availability:</strong> <span style="color: #27ae60;">${product.availability}</span></p>`;
                    }
                    
                    if (product.link) {
                        html += `<p><strong>Link:</strong> <a href="${product.link}" target="_blank" style="color: #3498db;">View Product →</a></p>`;
                    }
                    
                    if (product.images && product.images.length > 0) {
                        html += `<p><strong>Images:</strong></p>`;
                        html += `<div class="image-gallery" style="display: flex; flex-wrap: wrap; gap: 10px;">`;
                        product.images.forEach(img => {
                            html += `<img src="${img.url}" alt="${img.alt}" style="max-width: 200px; height: auto; border: 1px solid #ddd; border-radius: 5px; cursor: pointer;" onclick="window.open('${img.url}', '_blank')">`;
                        });
                        html += `</div>`;
                    }
                    
                    if (product.specifications && Object.keys(product.specifications).length > 0) {
                        html += `<p><strong>Specifications:</strong></p>`;
                        html += `<ul style="margin-left: 20px;">`;
                        Object.entries(product.specifications).forEach(([key, value]) => {
                            html += `<li><strong>${key}:</strong> ${value}</li>`;
                        });
                        html += `</ul>`;
                    }
                    
                    html += `</div>`;
                });
                
                html += '</div>';
                resultDiv.innerHTML = html;
            }
            
            async function makeRequest(url) {
                try {
                    const response = await fetch(url);
                    const data = await response.json();
                    showResult(data, !data.success);
                } catch (error) {
                    showResult({error: error.message}, true);
                }
            }
            
            function searchAll() {
                const query = encodeURIComponent(getQuery());
                makeRequest(`/search?query=${query}&max_results=3`);
            }
            
            function searchAmazon() {
                const query = encodeURIComponent(getQuery());
                makeRequest(`/search/amazon?query=${query}&max_results=3`);
            }
            
            function searchFlipkart() {
                const query = encodeURIComponent(getQuery());
                makeRequest(`/search/flipkart?query=${query}&max_results=3`);
            }
            
            function searchMeesho() {
                const query = encodeURIComponent(getQuery());
                makeRequest(`/search/meesho?query=${query}&max_results=3`);
            }
            
            function searchMyntra() {
                const query = encodeURIComponent(getQuery());
                makeRequest(`/search/myntra?query=${query}&max_results=3`);
            }
            
            function searchAmazonDetailed() {
                const query = encodeURIComponent(getQuery());
                makeRequest(`/search/amazon/detailed?query=${query}&max_results=2`);
            }
            
            function searchFlipkartDetailed() {
                const query = encodeURIComponent(getQuery());
                makeRequest(`/search/flipkart/detailed?query=${query}&max_results=2`);
            }
            
            function searchMeeshoDetailed() {
                const query = encodeURIComponent(getQuery());
                makeRequest(`/search/meesho/detailed?query=${query}&max_results=2`);
            }
            
            function searchMyntraDetailed() {
                const query = encodeURIComponent(getQuery());
                makeRequest(`/search/myntra/detailed?query=${query}&max_results=2`);
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template)

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "E-commerce Scraper API is running",
        "available_scrapers": list(scrapers.keys()),
        "driver_pool_size": len(driver_pool)
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
        
        # Search all platforms concurrently
        def search_platform(site_name, scraper):
            try:
                result = scraper.search(query, max_results)
                results.append(result)
            except Exception as e:
                logger.error(f"Error searching {site_name}: {e}")
                results.append({
                    "site": site_name,
                    "error": str(e),
                    "products": []
                })
        
        # Create threads for concurrent searching
        threads = []
        for site_name, scraper in scrapers.items():
            thread = threading.Thread(target=search_platform, args=(site_name, scraper))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Calculate total results
        total_results = sum(len(result.get('products', [])) for result in results)
        
        return jsonify({
            "success": True,
            "query": query,
            "total_results": total_results,
            "results": results
        })
        
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
        
        return jsonify({
            "success": True,
            "query": query,
            "result": result
        })
        
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
        
        return jsonify({
            "success": True,
            "query": query,
            "result": result
        })
        
    except Exception as e:
        logger.error(f"Detailed search {site} error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

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
    # Initialize driver pool
    logger.info("Initializing driver pool...")
    for _ in range(2):  # Start with 2 drivers
        try:
            driver = create_driver()
            driver_pool.append(driver)
        except Exception as e:
            logger.error(f"Failed to create initial driver: {e}")
    
    logger.info(f"Driver pool initialized with {len(driver_pool)} drivers")
    logger.info("Starting Flask API server...")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
