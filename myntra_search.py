#!/usr/bin/env python3
"""
myntra_search.py
Usage:
  python myntra_search.py "nike shoes"
or
  python myntra_search.py   # then type query when prompted
"""

import sys
import time
import json
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def create_driver(headless: bool = False) -> webdriver.Chrome:
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
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        # Try with ChromeDriverManager first
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✅ Myntra WebDriver initialized with ChromeDriverManager")
    except Exception as e:
        print(f"⚠️ ChromeDriverManager failed: {e}")
        try:
            # Fallback to system ChromeDriver
            driver = webdriver.Chrome(options=chrome_options)
            print("✅ Myntra WebDriver initialized with system ChromeDriver")
        except Exception as e2:
            print(f"❌ All ChromeDriver methods failed: {e2}")
            raise e2
    
    # Execute JavaScript to remove webdriver properties
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_script("delete navigator.__proto__.webdriver")
    
    return driver

def extract_product_details(driver: webdriver.Chrome) -> dict:
    """Extract detailed product information from a Myntra product page"""
    product_details = {
        "name": "",
        "price": "",
        "original_price": "",
        "discount": "",
        "brand": "",
        "category": "",
        "rating": "",
        "reviews_count": "",
        "size_options": [],
        "color_options": [],
        "availability": "",
        "link": driver.current_url,
        "images": [],
        "description": "",
        "specifications": {}
    }
    
    try:
        # Wait for page to fully load
        time.sleep(3)
        
        # Extract product name - try multiple selectors for Myntra
        name_selectors = [
            "h1.pdp-product-name",  # Main product title
            "h1[class*='pdp-product-name']",
            "h1[class*='product-name']",
            "div[class*='product-name'] h1",
            "div[class*='product-name'] span",
            "h1[data-testid='product-name']",
            "span[data-testid='product-name']",
            "div[class*='pdp-name'] h1",  # Myntra specific
            "div[class*='pdp-name'] span",  # Myntra specific
            "div[class*='pdp-name'] div",  # Myntra specific
            "h1",  # Generic h1
            "div[class*='title'] h1",
            "div[class*='title'] span"
        ]
        
        for selector in name_selectors:
            try:
                name_elem = driver.find_element(By.CSS_SELECTOR, selector)
                name_text = name_elem.text.strip()
                if name_text and len(name_text) > 5:
                    product_details["name"] = name_text
                    print(f"    Found name: {name_text}")
                    break
            except:
                continue
        
        # Extract price - comprehensive selectors
        price_selectors = [
            "span.pdp-price",  # Main price
            "span[class*='pdp-price']",
            "div[class*='pdp-price'] span",
            "span[class*='price']",
            "div[class*='price'] span",
            "span[data-testid='price']",
            "div[data-testid='price'] span",
            "span[class*='selling-price']",
            "div[class*='selling-price'] span",
            "span[class*='final-price']",
            "div[class*='final-price'] span"
        ]
        
        for selector in price_selectors:
            try:
                price_elem = driver.find_element(By.CSS_SELECTOR, selector)
                price_text = price_elem.text.strip()
                if price_text and ('₹' in price_text or 'Rs' in price_text or price_text.replace(',', '').replace('.', '').isdigit()):
                    product_details["price"] = price_text
                    print(f"    Found price: {price_text}")
                    break
            except:
                continue
        
        # Extract original price (MRP)
        original_price_selectors = [
            "span.pdp-mrp",  # MRP price
            "span[class*='pdp-mrp']",
            "div[class*='pdp-mrp'] span",
            "span[class*='mrp']",
            "div[class*='mrp'] span",
            "span[class*='original-price']",
            "div[class*='original-price'] span",
            "span[class*='strike']",
            "div[class*='strike'] span"
        ]
        
        for selector in original_price_selectors:
            try:
                price_elem = driver.find_element(By.CSS_SELECTOR, selector)
                price_text = price_elem.text.strip()
                if price_text and ('₹' in price_text or 'Rs' in price_text):
                    product_details["original_price"] = price_text
                    print(f"    Found original price: {price_text}")
                    break
            except:
                continue
        
        # Extract discount percentage
        discount_selectors = [
            "span.pdp-discount",  # Discount percentage
            "span[class*='pdp-discount']",
            "div[class*='pdp-discount'] span",
            "span[class*='discount']",
            "div[class*='discount'] span",
            "span[class*='off']",
            "div[class*='off'] span",
            "span[class*='save']",
            "div[class*='save'] span"
        ]
        
        for selector in discount_selectors:
            try:
                discount_elem = driver.find_element(By.CSS_SELECTOR, selector)
                discount_text = discount_elem.text.strip()
                if discount_text and ('%' in discount_text or 'off' in discount_text.lower() or 'save' in discount_text.lower()):
                    product_details["discount"] = discount_text
                    print(f"    Found discount: {discount_text}")
                    break
            except:
                continue
        
        # Extract brand
        brand_selectors = [
            "span.pdp-brand-name",  # Brand name
            "span[class*='pdp-brand-name']",
            "div[class*='pdp-brand-name'] span",
            "div[class*='pdp-brand-name'] div",  # Myntra specific
            "span[class*='brand-name']",
            "div[class*='brand-name'] span",
            "span[class*='brand']",
            "div[class*='brand'] span",
            "a[class*='brand']",
            "div[class*='brand'] a",
            "div[class*='pdp-brand'] span",  # Myntra specific
            "div[class*='pdp-brand'] div"  # Myntra specific
        ]
        
        for selector in brand_selectors:
            try:
                brand_elem = driver.find_element(By.CSS_SELECTOR, selector)
                brand_text = brand_elem.text.strip()
                if brand_text and len(brand_text) < 50:
                    product_details["brand"] = brand_text
                    print(f"    Found brand: {brand_text}")
                    break
            except:
                continue
        
        # If brand not found, try to extract from product name
        if not product_details["brand"] and product_details["name"]:
            name_parts = product_details["name"].split()
            if name_parts:
                # Common fashion brands
                common_brands = ["Nike", "Adidas", "Puma", "Reebok", "Under Armour", "New Balance", "Converse", "Vans", "Levi's", "Wrangler", "Lee", "Calvin Klein", "Tommy Hilfiger", "H&M", "Zara", "Forever 21", "Gap", "Uniqlo", "Hollister", "Abercrombie", "American Eagle", "Guess", "Diesel", "Armani", "Hugo Boss", "Ralph Lauren", "Lacoste", "Polo", "Champion", "Fila", "Skechers", "Woodland", "Red Tape", "Allen Solly", "Van Heusen", "Peter England", "Raymond", "Arrow", "Louis Philippe", "Park Avenue", "ColorPlus", "John Players", "UCB", "Roadster", "HRX", "Puma", "Adidas", "Nike", "Reebok", "Under Armour"]
                for brand in common_brands:
                    if brand.lower() in product_details["name"].lower():
                        product_details["brand"] = brand
                        print(f"    Found brand from name: {brand}")
                        break
        
        # Extract category (from breadcrumbs or navigation)
        try:
            breadcrumb_selectors = [
                "nav[class*='breadcrumb'] a",  # Breadcrumb links
                "div[class*='breadcrumb'] a",  # Breadcrumb divs
                "ol[class*='breadcrumb'] a",  # Breadcrumb ol
                "ul[class*='breadcrumb'] a",  # Breadcrumb ul
                "nav a[class*='breadcrumb']",  # Breadcrumb nav
                "div[class*='navigation'] a",  # Navigation links
                "nav[class*='navigation'] a"  # Navigation nav
            ]
            
            breadcrumbs = []
            for selector in breadcrumb_selectors:
                try:
                    breadcrumbs = driver.find_elements(By.CSS_SELECTOR, selector)
                    if breadcrumbs:
                        break
                except:
                    continue
            
            if breadcrumbs:
                # Category is usually the last breadcrumb
                category_text = breadcrumbs[-1].text.strip()
                if category_text:
                    product_details["category"] = category_text
                    print(f"    Found category: {category_text}")
        except:
            pass
        
        # Extract rating - improved selectors for Myntra
        rating_selectors = [
            "span[class*='rating-number']",  # Rating number spans
            "div[class*='rating-number'] span",  # Rating number divs
            "div[class*='pdp-rating'] span",  # Myntra specific PDP rating
            "div[class*='pdp-rating'] div",  # Myntra specific PDP rating div
            "span[data-testid='rating']",  # Test ID rating
            "div[data-testid='rating'] span",  # Test ID rating div
            "span[class*='rating']",  # Rating spans
            "div[class*='rating'] span",  # Rating divs
            "span[class*='stars']",  # Star rating
            "div[class*='stars'] span",  # Star rating divs
            "span[class*='review']",  # Review rating
            "div[class*='review'] span"  # Review rating divs
        ]
        
        for selector in rating_selectors:
            try:
                rating_elem = driver.find_element(By.CSS_SELECTOR, selector)
                rating_text = rating_elem.text.strip()
                # Check for decimal ratings (like 4.4, 4.3) and whole numbers
                if rating_text and (rating_text.replace('.', '').replace(',', '').isdigit() or rating_text.count('.') == 1):
                    # Validate it's a reasonable rating (0-5)
                    try:
                        rating_value = float(rating_text)
                        if 0 <= rating_value <= 5:
                            product_details["rating"] = rating_text
                            print(f"    Found rating: {rating_text}")
                            break
                    except ValueError:
                        continue
            except:
                continue
        
        # Fallback: Always try to extract rating from description text for better accuracy
        # This will override the previous rating if we find a better match
        try:
            # Look for rating patterns in the page text
            page_text = driver.page_source
            import re
            # Look for patterns like "4.4", "4.3" etc. in the page
            rating_patterns = [
                r'(\d+\.\d+)\s*\|\s*\d+\s*Ratings',  # Pattern like "3.5 | 82 Ratings"
                r'(\d+\.\d+)\s*\|\s*\d+\s*Verified Buyers',  # Pattern like "4.4 | 29 Verified Buyers"
                r'(\d+\.\d+)\s*\|',  # Pattern like "4.4 |"
                r'(\d+\.\d+)\s*\n',  # Pattern like "4.4\n"
                r'(\d+\.\d+)\s*Ratings',  # Pattern like "4.4 Ratings"
                r'(\d+\.\d+)\s*Verified Buyers',  # Pattern like "4.4 Verified Buyers"
            ]
            
            for pattern in rating_patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    try:
                        rating_value = float(match)
                        if 0 <= rating_value <= 5:
                            product_details["rating"] = match
                            print(f"    Found rating from text pattern: {match}")
                            break
                    except ValueError:
                        continue
                if product_details["rating"]:
                    break
        except:
            pass
        
        # Extract reviews count
        review_count_selectors = [
            "span[class*='review-count']",  # Review count spans
            "div[class*='review-count'] span",  # Review count divs
            "span[class*='reviews']",  # Reviews spans
            "div[class*='reviews'] span",  # Reviews divs
            "span[class*='rating-count']",  # Rating count spans
            "div[class*='rating-count'] span",  # Rating count divs
            "span[data-testid='review-count']",  # Test ID review count
            "div[data-testid='review-count'] span"  # Test ID review count div
        ]
        
        for selector in review_count_selectors:
            try:
                review_elem = driver.find_element(By.CSS_SELECTOR, selector)
                review_text = review_elem.text.strip()
                if review_text and ('rating' in review_text.lower() or 'review' in review_text.lower() or ',' in review_text):
                    product_details["reviews_count"] = review_text
                    print(f"    Found reviews count: {review_text}")
                    break
            except:
                continue
        
        # Extract size options
        try:
            size_selectors = [
                "div[class*='size'] button",  # Size buttons
                "div[class*='size'] span",  # Size spans
                "button[class*='size']",  # Size buttons
                "span[class*='size']",  # Size spans
                "div[class*='size-chart'] button",  # Size chart buttons
                "div[class*='size-chart'] span"  # Size chart spans
            ]
            
            sizes = []
            for selector in size_selectors:
                try:
                    size_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in size_elements:
                        size_text = elem.text.strip()
                        if size_text and len(size_text) < 10:  # Size should be short
                            sizes.append(size_text)
                    if sizes:
                        break
                except:
                    continue
            
            product_details["size_options"] = list(set(sizes))  # Remove duplicates
            print(f"    Found {len(product_details['size_options'])} size options")
        except:
            pass
        
        # Extract color options
        try:
            color_selectors = [
                "div[class*='color'] button",  # Color buttons
                "div[class*='color'] span",  # Color spans
                "button[class*='color']",  # Color buttons
                "span[class*='color']",  # Color spans
                "div[class*='color-option'] button",  # Color option buttons
                "div[class*='color-option'] span"  # Color option spans
            ]
            
            colors = []
            for selector in color_selectors:
                try:
                    color_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in color_elements:
                        color_text = elem.text.strip()
                        if color_text and len(color_text) < 20:  # Color name should be reasonable length
                            colors.append(color_text)
                    if colors:
                        break
                except:
                    continue
            
            product_details["color_options"] = list(set(colors))  # Remove duplicates
            print(f"    Found {len(product_details['color_options'])} color options")
        except:
            pass
        
        # Extract availability
        availability_selectors = [
            "span[class*='availability']",  # Availability spans
            "div[class*='availability'] span",  # Availability divs
            "span[class*='stock']",  # Stock spans
            "div[class*='stock'] span",  # Stock divs
            "span[class*='in-stock']",  # In stock spans
            "div[class*='in-stock'] span",  # In stock divs
            "span[class*='out-of-stock']",  # Out of stock spans
            "div[class*='out-of-stock'] span"  # Out of stock divs
        ]
        
        for selector in availability_selectors:
            try:
                avail_elem = driver.find_element(By.CSS_SELECTOR, selector)
                avail_text = avail_elem.text.strip()
                if avail_text and ('stock' in avail_text.lower() or 'available' in avail_text.lower() or 'delivery' in avail_text.lower()):
                    product_details["availability"] = avail_text
                    print(f"    Found availability: {avail_text}")
                    break
            except:
                continue
        
        # Extract product images
        try:
            print(f"    Starting image extraction...")
            
            # Wait a bit more for images to load
            time.sleep(2)
            
            image_selectors = [
                "img[class*='pdp-image']",  # Main product image
                "img[class*='product-image']",  # Product image
                "img[class*='main-image']",  # Main image
                "img[class*='thumbnail']",  # Thumbnail images
                "img[class*='gallery']",  # Gallery images
                "div[class*='image'] img",  # Images in divs
                "div[class*='gallery'] img",  # Gallery images
                "div[class*='carousel'] img",  # Carousel images
                "img[data-testid='product-image']",  # Test ID images
                "div[data-testid='product-image'] img",  # Test ID image divs
                "div[class*='imageSliderContainer'] img",  # Myntra specific
                "div[class*='sliderContainer'] img",  # Myntra specific
                "div[class*='pdp-image'] img",  # Myntra specific
                "div[class*='product-slider'] img",  # Myntra specific
                "picture img",  # Picture elements
                "img[src*='assets/images']"  # Myntra asset images
            ]
            
            all_images = []
            found_images = set()  # To track unique images
            
            for selector in image_selectors:
                try:
                    images = driver.find_elements(By.CSS_SELECTOR, selector)
                    print(f"    Found {len(images)} images with selector: {selector}")
                    
                    for img in images:
                        try:
                            img_src = img.get_attribute('src')
                            img_alt = img.get_attribute('alt') or ''
                            
                            # Debug: print image source
                            if img_src:
                                print(f"      Image src: {img_src[:100]}...")
                            
                            # Filter out placeholder images and get only product images
                            if img_src and ('myntra' in img_src.lower() or 'assets' in img_src.lower()) and 'placeholder' not in img_src.lower() and 'logo' not in img_src.lower() and 'icon' not in img_src.lower() and 'banner' not in img_src.lower() and 'sprite' not in img_src.lower():
                                # Get high-resolution image URL
                                if 'image' in img_src and 'q=' in img_src:
                                    # Replace quality parameter to get higher resolution
                                    high_res_src = img_src.replace('q=70', 'q=100').replace('q=50', 'q=100').replace('q=60', 'q=100')
                                else:
                                    high_res_src = img_src
                                
                                # Avoid duplicates
                                if high_res_src not in found_images:
                                    found_images.add(high_res_src)
                                    
                                    image_info = {
                                        "url": high_res_src,
                                        "alt": img_alt,
                                        "thumbnail": img_src
                                    }
                                    
                                    all_images.append(image_info)
                                    print(f"      Added image: {img_alt[:50]}...")
                                    
                        except Exception as img_error:
                            print(f"      Error processing image: {img_error}")
                            continue
                                
                except Exception as e:
                    print(f"    Error with selector {selector}: {e}")
                    continue
            
            # Also try to find images using XPath
            try:
                print(f"    Trying XPath image extraction...")
                xpath_images = driver.find_elements(By.XPATH, "//img[contains(@src, 'myntra') or contains(@src, 'assets')]")
                print(f"    Found {len(xpath_images)} images via XPath")
                
                for img in xpath_images:
                    try:
                        img_src = img.get_attribute('src')
                        img_alt = img.get_attribute('alt') or ''
                        
                        if img_src and 'placeholder' not in img_src.lower() and 'logo' not in img_src.lower() and 'icon' not in img_src.lower() and 'banner' not in img_src.lower() and 'sprite' not in img_src.lower():
                            high_res_src = img_src.replace('q=70', 'q=100').replace('q=50', 'q=100')
                            
                            if high_res_src not in found_images:
                                found_images.add(high_res_src)
                                
                                image_info = {
                                    "url": high_res_src,
                                    "alt": img_alt,
                                    "thumbnail": img_src
                                }
                                
                                all_images.append(image_info)
                                print(f"      Added XPath image: {img_alt[:50]}...")
                    except:
                        continue
            except Exception as xpath_error:
                print(f"    XPath image extraction error: {xpath_error}")
            
            # Limit to first 8 images to avoid too much data
            product_details["images"] = all_images[:8]
            print(f"    Final result: Found {len(product_details['images'])} product images")
            
            # Debug: print first image URL if available
            if product_details["images"]:
                print(f"    First image URL: {product_details['images'][0]['url']}")
            
        except Exception as e:
            print(f"    Error extracting images: {e}")
            product_details["images"] = []
        
        # Extract product description
        try:
            description_selectors = [
                "div[class*='description']",  # Description divs
                "div[class*='product-description']",  # Product description divs
                "div[class*='pdp-description']",  # PDP description divs
                "div[class*='details']",  # Details divs
                "div[class*='product-details']",  # Product details divs
                "div[class*='about']",  # About divs
                "div[class*='product-about']"  # Product about divs
            ]
            
            for selector in description_selectors:
                try:
                    desc_elem = driver.find_element(By.CSS_SELECTOR, selector)
                    desc_text = desc_elem.text.strip()
                    if desc_text and len(desc_text) > 20:  # Meaningful description
                        product_details["description"] = desc_text
                        print(f"    Found description: {desc_text[:100]}...")
                        break
                except:
                    continue
        except:
            pass
        
        # Extract specifications
        try:
            print(f"    Extracting specifications...")
            
            spec_selectors = [
                "div[class*='specification'] table tr",  # Specification table rows
                "div[class*='specification'] div",  # Specification divs
                "div[class*='details'] table tr",  # Details table rows
                "div[class*='details'] div",  # Details divs
                "div[class*='features'] div",  # Features divs
                "div[class*='product-features'] div"  # Product features divs
            ]
            
            specifications = {}
            
            for selector in spec_selectors:
                try:
                    spec_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in spec_elements:
                        text = elem.text.strip()
                        if text and len(text) > 10 and ':' in text:
                            # Try to parse key-value pairs
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
            print(f"    Found {len(specifications)} specifications")
            
        except Exception as e:
            print(f"    Error extracting specifications: {e}")
            product_details["specifications"] = {}
        
        # Debug: Print what we found
        print(f"    Final extracted data: {product_details}")
        
    except Exception as e:
        print(f"    Error extracting product details: {e}")
    
    return product_details

def search_myntra(query: str, headless: bool = False, max_results: int = 8):
    driver = create_driver(headless=headless)
    try:
        driver.get("https://www.myntra.com")
        wait = WebDriverWait(driver, 10)

        # Search input - try multiple selectors for Myntra
        search_input_selectors = [
            "input[class*='search']",  # Generic search input
            "input[placeholder*='Search']",  # Search placeholder
            "input[placeholder*='search']",  # Lowercase search placeholder
            "input[type='search']",  # Search type input
            "input[name='search']",  # Search name input
            "input[data-reactid*='search']",  # React search input
            "input[class*='desktop-searchBar']",  # Myntra specific
            "input[class*='search-bar']",  # Search bar
            "input[class*='desktop-search']",  # Desktop search
            "input"  # Any input as fallback
        ]
        
        search_input = None
        for selector in search_input_selectors:
            try:
                search_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                print(f"Found search input with selector: {selector}")
                break
            except:
                continue
        
        if not search_input:
            print("Could not find search input. Trying to navigate directly to search URL...")
            # Try direct URL navigation instead
            search_url = f"https://www.myntra.com/{query.replace(' ', '-')}"
            driver.get(search_url)
            time.sleep(5)
        else:
            search_input.clear()
            search_input.send_keys(query)
            search_input.send_keys(Keys.ENTER)

        # Wait for search results to load
        print("Waiting for search results to load...")
        time.sleep(5)  # Give more time for results to load
        
        # Save the HTML content of the search results page
        html_content = driver.page_source
        filename = f"myntra_search_{query.replace(' ', '_')}.html"
        
        # Write HTML to file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\nSearch results saved as: {filename}")
        print(f"Current URL: {driver.current_url}")
        print(f"Page title: {driver.title}")
        
        # Extract detailed product information
        products_info = []
        
        # Try different selectors for product cards - updated for Myntra structure
        product_selectors = [
            "a[href*='/sports-shoes/']",  # Sports shoes links
            "a[href*='/casual-shoes/']",  # Casual shoes links
            "a[href*='/footwear/']",  # Footwear product links
            "a[href*='/nike/']",  # Nike product links
            "a[href*='/shoes/']",  # Shoe product links
            "div[class*='product-productMetaInfo']",  # Myntra specific product info
            "a[class*='product']",  # Product links
            "div[class*='product-base']",  # Main product card container
            "div[class*='product-card']",  # Alternative card selector
            "div[class*='product-item']",  # Another card selector
            "div[class*='product']"  # Generic product selector
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
            return
        
        # Debug: Let's see what's actually in the first card
        if product_cards:
            print(f"\nDebugging first product card:")
            first_card = product_cards[0]
            print(f"Card HTML snippet: {first_card.get_attribute('outerHTML')[:500]}...")
            
            # Try to find any text content in the card
            all_text = first_card.text.strip()
            print(f"All text in first card: {all_text[:200]}...")
            
            # Try to find any links
            links = first_card.find_elements(By.TAG_NAME, "a")
            print(f"Found {len(links)} links in first card")
            for i, link in enumerate(links[:3]):
                print(f"  Link {i+1}: {link.get_attribute('href')} - Text: {link.text.strip()[:50]}")
        
        # Extract information from each product card
        for i, card in enumerate(product_cards[:max_results]):
            try:
                product_info = {}
                
                # Handle different card types - if it's a product-productMetaInfo div, find the parent link
                if card.tag_name == 'div' and 'product-productMetaInfo' in card.get_attribute('class'):
                    # Find the parent anchor element
                    try:
                        parent_link = card.find_element(By.XPATH, "./ancestor::a")
                        product_info['link'] = parent_link.get_attribute('href') or ''
                        # Use the parent link as the main card for extraction
                        card = parent_link
                    except:
                        pass
                
                # If the card itself is a link, get the link directly
                if card.tag_name == 'a':
                    product_info['link'] = card.get_attribute('href') or ''
                
                # More comprehensive title selectors - updated for Myntra structure
                title_selectors = [
                    "h3.product-brand",  # Product brand (exact class)
                    "h4.product-product",  # Product name (exact class)
                    "h3[class*='product-brand']",  # Product brand
                    "h4[class*='product-brand']",  # Alternative product brand
                    "span[class*='product-brand']",  # Product brand span
                    "div[class*='product-brand']",  # Product brand div
                    "h3[class*='product-product']",  # Product name
                    "h4[class*='product-product']",  # Alternative product name
                    "span[class*='product-product']",  # Product name span
                    "div[class*='product-product']",  # Product name div
                    "a[class*='product']",  # Product link
                    "h3",  # Generic h3
                    "h4",  # Generic h4
                    "span[class*='title']",  # Title span
                    "div[class*='title']"  # Title div
                ]
                
                # Extract brand and product name separately
                brand_found = False
                product_name_found = False
                
                for selector in title_selectors:
                    try:
                        title_elem = card.find_element(By.CSS_SELECTOR, selector)
                        title_text = title_elem.text.strip()
                        if title_text and len(title_text) > 2:  # Only use if meaningful text
                            # Check if this is a brand or product name
                            if 'brand' in selector.lower():
                                product_info['brand'] = title_text
                                brand_found = True
                            elif 'product' in selector.lower() and not product_name_found:
                                product_info['title'] = title_text
                                product_name_found = True
                            elif not product_info.get('title') and len(title_text) > 5:
                                product_info['title'] = title_text
                            
                            # If we don't already have a link, try to find it
                            if not product_info.get('link'):
                                # Try to find the parent link element
                                try:
                                    # Look for parent anchor element
                                    parent_link = title_elem.find_element(By.XPATH, "./ancestor::a")
                                    product_info['link'] = parent_link.get_attribute('href') or ''
                                except:
                                    # If no parent anchor, try to find any link in the card
                                    try:
                                        link_elem = card.find_element(By.TAG_NAME, "a")
                                        product_info['link'] = link_elem.get_attribute('href') or ''
                                    except:
                                        product_info['link'] = ''
                    except:
                        continue
                
                # If still no link found, try to find any link in the card
                if not product_info.get('link'):
                    try:
                        link_elem = card.find_element(By.TAG_NAME, "a")
                        product_info['link'] = link_elem.get_attribute('href') or ''
                    except:
                        pass
                
                # If still no title found, try to get it from the card's text content
                if not product_info.get('title'):
                    try:
                        card_text = card.text.strip()
                        if card_text and len(card_text) > 5:
                            # Extract the first meaningful line
                            lines = card_text.split('\n')
                            for line in lines:
                                line = line.strip()
                                if line and len(line) > 5 and not line.startswith('Rs.'):
                                    product_info['title'] = line
                                    break
                    except:
                        pass
                
                # More comprehensive price selectors - updated for Myntra structure
                price_selectors = [
                    "span.product-discountedPrice",  # Discounted price (exact class)
                    "span[class*='product-discountedPrice']",  # Discounted price
                    "div.product-price span",  # Product price div span
                    "span[class*='product-price']",  # Product price
                    "div[class*='product-price'] span",  # Product price div
                    "span[class*='price']",  # Generic price
                    "div[class*='price'] span",  # Generic price div
                    "span[class*='selling-price']",  # Selling price
                    "div[class*='selling-price'] span",  # Selling price div
                    "span[class*='final-price']",  # Final price
                    "div[class*='final-price'] span"  # Final price div
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
                
                # More comprehensive original price selectors - updated for Myntra structure
                original_price_selectors = [
                    "span.product-strike",  # Strike price (exact class)
                    "span[class*='product-strike']",  # Strike price
                    "span[class*='product-mrp']",  # MRP price
                    "div[class*='product-mrp'] span",  # MRP price div
                    "span[class*='mrp']",  # Generic MRP
                    "div[class*='mrp'] span",  # Generic MRP div
                    "span[class*='original-price']",  # Original price
                    "div[class*='original-price'] span"  # Original price div
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
                
                # More comprehensive discount selectors - updated for Myntra structure
                discount_selectors = [
                    "span.product-discountPercentage",  # Discount percentage (exact class)
                    "span[class*='product-discountPercentage']",  # Discount percentage
                    "span[class*='discount']",  # Generic discount
                    "div[class*='discount'] span",  # Generic discount div
                    "span[class*='off']",  # Off discount
                    "div[class*='off'] span",  # Off discount div
                    "span[class*='save']",  # Save discount
                    "div[class*='save'] span"  # Save discount div
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
                
                # More comprehensive rating selectors
                rating_selectors = [
                    "span[class*='rating']",  # Rating spans
                    "div[class*='rating'] span",  # Rating divs
                    "span[class*='stars']",  # Star rating
                    "div[class*='stars'] span",  # Star rating divs
                    "span[class*='review']",  # Review rating
                    "div[class*='review'] span"  # Review rating divs
                ]
                
                for selector in rating_selectors:
                    try:
                        rating_elem = card.find_element(By.CSS_SELECTOR, selector)
                        rating_text = rating_elem.text.strip()
                        # Check for decimal ratings and validate range
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
                    products_info.append(product_info)
                    
            except Exception as e:
                print(f"Error extracting info from product {i+1}: {e}")
                continue
        
        # Display extracted information
        if products_info:
            print(f"\n{'='*60}")
            print(f"EXTRACTED PRODUCT INFORMATION")
            print(f"{'='*60}")
            
            for i, product in enumerate(products_info, 1):
                print(f"\n{i}. {product.get('title', 'Title not found')}")
                print(f"   Price: {product.get('price', 'Price not found')}")
                if product.get('original_price'):
                    print(f"   Original Price: {product['original_price']}")
                if product.get('discount'):
                    print(f"   Discount: {product['discount']}")
                if product.get('rating'):
                    print(f"   Rating: {product['rating']}")
                if product.get('link'):
                    print(f"   Link: {product['link']}")
                print("-" * 50)
        else:
            print("No product information could be extracted.")

        # Save extracted data to JSON file
        if products_info:
            json_filename = f"myntra_products_{query.replace(' ', '_')}.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'query': query,
                    'search_url': driver.current_url,
                    'total_products': len(products_info),
                    'products': products_info
                }, f, indent=2, ensure_ascii=False)
            print(f"\nProduct data also saved as: {json_filename}")
            
            # Extract detailed product information by visiting each product page
            detailed_products = []
            
            for i, product in enumerate(products_info[:3]):  # Limit to first 3 products
                try:
                    print(f"\nExtracting details for product {i+1}: {product.get('title', 'Unknown')}")
                    
                    # Get the product link directly from the product info
                    product_url = product.get('link', '')
                    if not product_url:
                        print(f"  No product URL found for product {i+1}")
                        continue
                    
                    # Navigate directly to the product URL
                    print(f"  Navigating to: {product_url}")
                    driver.get(product_url)
                    
                    # Wait for page to load
                    time.sleep(5)
                    
                    print(f"  Current URL: {driver.current_url}")
                    
                    # Extract detailed product information
                    detailed_product = extract_product_details(driver)
                    detailed_products.append(detailed_product)
                    
                    # Go back to search results for next product
                    driver.back()
                    time.sleep(2)
                                
                except Exception as e:
                    print(f"  Error extracting details for product {i+1}: {e}")
                    continue
            
            # Display detailed product information
            if detailed_products:
                print(f"\n{'='*80}")
                print(f"DETAILED PRODUCT INFORMATION")
                print(f"{'='*80}")
                
                for i, product in enumerate(detailed_products, 1):
                    print(f"\n{i}. {product.get('name', 'Name not found')}")
                    print(f"   Price: {product.get('price', 'Price not found')}")
                    if product.get('original_price'):
                        print(f"   Original Price: {product['original_price']}")
                    if product.get('discount'):
                        print(f"   Discount: {product['discount']}")
                    print(f"   Brand: {product.get('brand', 'Brand not found')}")
                    print(f"   Category: {product.get('category', 'Category not found')}")
                    print(f"   Rating: {product.get('rating', 'Rating not found')}")
                    print(f"   Reviews: {product.get('reviews_count', 'Reviews not found')}")
                    print(f"   Sizes: {', '.join(product.get('size_options', []))}")
                    print(f"   Colors: {', '.join(product.get('color_options', []))}")
                    print(f"   Availability: {product.get('availability', 'Availability not found')}")
                    print(f"   Images: {len(product.get('images', []))} images found")
                    if product.get('images'):
                        print(f"   Main Image: {product['images'][0]['url']}")
                    print(f"   Specifications: {len(product.get('specifications', {}))} specs found")
                    print(f"   Link: {product.get('link', 'Link not found')}")
                    print("-" * 80)
                
                # Save detailed products to JSON
                detailed_json_filename = f"myntra_detailed_products_{query.replace(' ', '_')}.json"
                with open(detailed_json_filename, 'w', encoding='utf-8') as f:
                    json.dump({
                        'query': query,
                        'search_url': driver.current_url,
                        'total_products': len(detailed_products),
                        'products': detailed_products
                    }, f, indent=2, ensure_ascii=False)
                print(f"\nDetailed product data saved as: {detailed_json_filename}")
            else:
                print("\nNo detailed product information could be extracted.")

        print(f"\nYou can now open '{filename}' in your browser to view the full search results page.")
        print("The browser will stay open for 10 seconds so you can see the page...")
        
        # Keep browser open for a bit so user can see the page
        time.sleep(10)

    finally:
        driver.quit()

if __name__ == "__main__":
    # get query from CLI arg or input
    query: Optional[str] = None
    headless_flag = False

    if len(sys.argv) >= 2:
        # allow e.g. python myntra_search.py "nike shoes"
        query = " ".join(sys.argv[1:])
    else:
        query = input("Enter product to search on Myntra: ").strip()

    # If user included --headless keyword, detect it (optional)
    if query and "--headless" in query:
        headless_flag = True
        query = query.replace("--headless", "").strip()

    if not query:
        print("No query provided. Exiting.")
        sys.exit(1)

    search_myntra(query, headless=headless_flag)
