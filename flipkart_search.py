#!/usr/bin/env python3
"""
flipkart_search.py
Usage:
  python flipkart_search.py "iphone 14"
or
  python flipkart_search.py   # then type query when prompted
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
        print("Flipkart WebDriver initialized with ChromeDriverManager")
    except Exception as e:
        print(f"ChromeDriverManager failed: {e}")
        try:
            # Fallback to system ChromeDriver
            driver = webdriver.Chrome(options=chrome_options)
            print("Flipkart WebDriver initialized with system ChromeDriver")
        except Exception as e2:
            print(f"All ChromeDriver methods failed: {e2}")
            raise e2
    
    # Execute JavaScript to remove webdriver properties
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_script("delete navigator.__proto__.webdriver")
    
    return driver

def extract_product_details(driver: webdriver.Chrome) -> dict:
    """Extract detailed product information from a product page"""
    product_details = {
        "name": "",
        "price": "",
        "mrp": "",
        "discount_percentage": "",
        "discount_amount": "",
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
        # Wait for page to fully load
        time.sleep(2)
        
        # Extract product name - try multiple selectors
        name_selectors = [
            "span.B_NuCI",  # Main product title
            "h1[class*='B_NuCI']",
            "h1",
            "span[class*='B_NuCI']",
            "div[class*='B_NuCI']",
            "div[data-automation-id='product-title']",
            "h1[data-automation-id='product-title']",
            "span[data-automation-id='product-title']"
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
        
        # Extract price - comprehensive selectors with MRP and discount handling
        price_selectors = [
            "div._30jeq3",  # Main price
            "div[class*='_30jeq3']",
            "span[class*='_30jeq3']",
            "div[class*='_25b18c']",
            "span[class*='_25b18c']",
            "div[class*='_16Jk6d']",  # Alternative price selector
            "span[class*='_16Jk6d']",
            "div[class*='_1vC4OE']",  # Another price selector
            "span[class*='_1vC4OE']",
            "div[data-automation-id='product-price']",
            "span[data-automation-id='product-price']",
            "div[class*='price']",
            "span[class*='price']"
        ]
        
        # Extract current price and MRP separately
        current_price = ""
        mrp_price = ""
        
        for selector in price_selectors:
            try:
                price_elem = driver.find_element(By.CSS_SELECTOR, selector)
                price_text = price_elem.text.strip()
                if price_text and ('₹' in price_text or 'Rs' in price_text or 'INR' in price_text):
                    # Check if this is likely the current price (not struck through)
                    try:
                        parent_elem = price_elem.find_element(By.XPATH, "./..")
                        parent_classes = parent_elem.get_attribute('class') or ''
                        
                        # If parent has strikethrough, it's likely MRP
                        if 'strike' in parent_classes.lower() or 'mrp' in parent_classes.lower():
                            if not mrp_price:
                                mrp_price = price_text
                                print(f"    Found MRP: {price_text}")
                        else:
                            if not current_price:
                                current_price = price_text
                                print(f"    Found current price: {price_text}")
                    except:
                        # If we can't determine, assume it's current price
                        if not current_price:
                            current_price = price_text
                            
            except:
                continue
        
        # Set the final price - prioritize current price over MRP
        if current_price:
            product_details["price"] = current_price
            if mrp_price:
                product_details["mrp"] = mrp_price
                # Calculate discount percentage
                try:
                    current_num = float(current_price.replace('₹', '').replace(',', '').replace('Rs', '').strip())
                    mrp_num = float(mrp_price.replace('₹', '').replace(',', '').replace('Rs', '').strip())
                    if mrp_num > current_num:
                        discount_percent = ((mrp_num - current_num) / mrp_num) * 100
                        product_details["discount_percentage"] = f"{discount_percent:.0f}% off"
                        product_details["discount_amount"] = f"₹{mrp_num - current_num:,.0f}"
                        print(f"    Calculated discount: {product_details['discount_percentage']} (₹{product_details['discount_amount']} off)")
                except:
                    pass
        elif mrp_price:
            product_details["price"] = mrp_price
            print(f"    Warning: Only MRP found, no current price detected")
        
        # Extract brand (from breadcrumbs or product name)
        try:
            breadcrumb_selectors = [
                "a._2whKao",  # Original breadcrumb selector
                "a[class*='_2whKao']",
                "nav a",  # Any nav link
                "div[class*='breadcrumb'] a",
                "ol[class*='breadcrumb'] a"
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
                # Look for brand in breadcrumbs (usually second or third item)
                for crumb in breadcrumbs[1:3]:
                    crumb_text = crumb.text.strip()
                    if crumb_text and len(crumb_text) < 20:  # Brand names are usually short
                        product_details["brand"] = crumb_text
                        print(f"    Found brand from breadcrumb: {crumb_text}")
                        break
        except:
            pass
        
        # Extract category (from breadcrumbs)
        try:
            if breadcrumbs:
                # Category is usually the first breadcrumb
                category_text = breadcrumbs[0].text.strip()
                if category_text:
                    product_details["category"] = category_text
                    print(f"    Found category: {category_text}")
        except:
            pass
        
        # Extract reviews count
        try:
            review_count_selectors = [
                "span._2_R_DZ",  # Reviews count
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
                        print(f"    Found reviews count: {review_text}")
                        break
                except:
                    continue
        except:
            pass
        
        # Extract availability
        try:
            availability_selectors = [
                "span[class*='availability']",
                "div[class*='availability']",
                "span[class*='stock']",
                "div[class*='stock']",
                "span[class*='delivery']",
                "div[class*='delivery']"
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
        except:
            pass
        
        # Extract rating - enhanced selectors for better accuracy
        rating_selectors = [
            "div._3LWZlK",  # Main rating stars
            "span._3LWZlK",  # Rating text
            "div[class*='_3LWZlK']",
            "span[class*='_3LWZlK']",
            "div[class*='_2d4LTz']",  # Alternative rating selector
            "span[class*='_2d4LTz']",
            "div[class*='_3uSWvM']",  # Another rating selector
            "span[class*='_3uSWvM']",
            "div[class*='rating']",
            "span[class*='rating']",
            "div[data-automation-id='product-rating']",
            "span[data-automation-id='product-rating']",
            "div[class*='_1i0wkb']",  # New Flipkart rating selector
            "span[class*='_1i0wkb']"
        ]
        
        for selector in rating_selectors:
            try:
                rating_elem = driver.find_element(By.CSS_SELECTOR, selector)
                rating_text = rating_elem.text.strip()
                # More lenient validation for ratings
                if rating_text and len(rating_text) > 0:
                    # Check if it looks like a rating (number with optional decimal)
                    import re
                    if re.match(r'^\d+(\.\d+)?$', rating_text) and float(rating_text) <= 5.0:
                        product_details["rating"] = rating_text
                        print(f"    Found rating: {rating_text}")
                        break
            except:
                continue
        
        # If brand not found in breadcrumbs, try to extract from product name
        if not product_details["brand"] and product_details["name"]:
            name_parts = product_details["name"].split()
            if name_parts:
                # Enhanced brand extraction for clothing and general products
                common_brands = [
                    # International clothing brands
                    "Nike", "Adidas", "Puma", "Reebok", "Converse", "Vans", "New Balance", "Under Armour", "Skechers", "Fila", "Jordan", "Champion", 
                    "Levi's", "Tommy Hilfiger", "Calvin Klein", "H&M", "Zara", "Forever 21", "Uniqlo", "Gap", "American Eagle", "Hollister", "Abercrombie", 
                    "Ralph Lauren", "Lacoste", "Polo", "Gucci", "Prada", "Versace", "Armani", "Hugo Boss", "Diesel", "Guess", "Michael Kors", "Coach", 
                    "Kate Spade", "Tory Burch", "Ray-Ban", "Oakley", "Asics", "Mizuno", "Brooks", "Saucony",
                    # Indian clothing brands
                    "Allen Solly", "Van Heusen", "Peter England", "Louis Philippe", "Arrow", "Park Avenue", "Blackberrys", "Red Tape", "Campus Sutra",
                    "The Bear House", "The Indian Garage Co", "Hellcat", "Turtle", "Glitchez", "Vebnor", "Dhaduk", "Stoneberg", "STI", "Rare Rabbit",
                    # Tech brands
                    "Apple", "Samsung", "OnePlus", "Xiaomi", "Realme", "Vivo", "Oppo", "Motorola", "Nokia", "Sony", "LG", "HP", "Dell", "Lenovo", "Asus", "Acer", "MSI", "Google", "Nothing", "Honor", "POCO"
                ]
                for brand in common_brands:
                    if brand.lower() in product_details["name"].lower():
                        product_details["brand"] = brand
                        print(f"    Found brand from name: {brand}")
                        break
                
                # If still no brand found, try to extract from URL or first word
                if not product_details["brand"]:
                    # Try to extract brand from URL
                    url_parts = driver.current_url.split('/')
                    for part in url_parts:
                        if part and len(part) > 2 and not part.isdigit() and part not in ['www.flipkart.com', 'search', 'q', 'store', 'clo', 'ash', 'axc']:
                            # Check if it looks like a brand name
                            if not any(word in part.lower() for word in ['men', 'women', 'boys', 'girls', 'kids', 'unisex', 'shirt', 'shirts']):
                                product_details["brand"] = part.replace('-', ' ').replace('+', ' ').title()
                                print(f"    Extracted brand from URL: {product_details['brand']}")
                                break
                    
                    # If still no brand, try first word of product name
                    if not product_details["brand"] and name_parts:
                        first_word = name_parts[0]
                        if len(first_word) > 2 and not first_word.lower() in ['men', 'women', 'boys', 'girls', 'kids', 'unisex']:
                            product_details["brand"] = first_word.title()
                            print(f"    Extracted brand from first word: {product_details['brand']}")
        
        # Extract product images
        try:
            print(f"    Starting image extraction...")
            
            # Wait a bit more for images to load
            time.sleep(1)
            
            image_selectors = [
                "img._396cs4",  # Main product image
                "img[class*='_396cs4']",  # Alternative main image
                "img._2r_T1I",  # Product gallery images
                "img[class*='_2r_T1I']",  # Alternative gallery images
                "img[class*='product-image']",  # Generic product image
                "img[class*='_1BweB8']",  # Another image selector
                "img[class*='_2d1DkJ']",  # Another image selector
                "img[class*='_3exPp9']",  # Another image selector
                "img[class*='_2QcJZg']",  # Another image selector
                "img[class*='_3n6B0X']",  # Another image selector
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
                            if img_src and ('flipkart' in img_src.lower() or 'rukminim' in img_src.lower()) and 'placeholder' not in img_src.lower():
                                # Get high-resolution image URL
                                if 'image' in img_src and 'q=' in img_src:
                                    # Replace quality parameter to get higher resolution
                                    high_res_src = img_src.replace('q=70', 'q=100').replace('q=50', 'q=100')
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
                xpath_images = driver.find_elements(By.XPATH, "//img[contains(@src, 'flipkart') or contains(@src, 'rukminim')]")
                print(f"    Found {len(xpath_images)} images via XPath")
                
                for img in xpath_images:
                    try:
                        img_src = img.get_attribute('src')
                        img_alt = img.get_attribute('alt') or ''
                        
                        if img_src and 'placeholder' not in img_src.lower():
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

def close_flipkart_login_popup(driver: webdriver.Chrome, timeout: int = 5):
    """Flipkart usually shows a login modal. This attempts to close it."""
    try:
        wait = WebDriverWait(driver, timeout)
        # The close button '✕' is usually a button or span near a modal; try a few common selectors:
        selectors = [
            "button._2KpZ6l._2doB4z",          # class-based close (common)
            "button._2KpZ6l._2doB4z",         # same fallback
            "button._2KpZ6l._2doB4z",         # repeated intentionally
            "button[aria-label='Close']",
            "button[title='Close']",
            "button:contains('✕')",           # not supported by selenium, kept for reference
        ]
        # A more robust approach: try to find any button inside modal container and click the first visible one.
        # We'll attempt some targeted selectors used on Flipkart:
        try:
            close_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button._2KpZ6l._2doB4z")))
            close_btn.click()
            return
        except Exception:
            # fallback: try to click the overlay close if present
            try:
                # a generic attempt: find close icon element by xpath for '✕' symbol
                el = driver.find_element(By.XPATH, "//button[contains(., '✕') or contains(., 'Close')]")
                el.click()
                return
            except Exception:
                # nothing to do; maybe popup not present
                return
    except TimeoutException:
        return

def search_flipkart(query: str, headless: bool = False, max_results: int = 8):
    """
    Search Flipkart and return structured product data (like Meesho approach)
    Returns: dict with products in the format expected by intelligent search system
    """
    driver = create_driver(headless=headless)
    try:
        print(f"Searching Flipkart for: {query}")
        
        # Navigate directly to search URL (like Meesho approach)
        search_url = f"https://www.flipkart.com/search?q={query.replace(' ', '+')}"
        driver.get(search_url)
        time.sleep(5)

        # Close login popup if present
        close_flipkart_login_popup(driver)

        # Wait for search results to load
        print("Waiting for search results to load...")
        time.sleep(5)
        
        # Save the HTML content of the search results page
        html_content = driver.page_source
        filename = f"flipkart_search_{query.replace(' ', '_')}.html"
        
        # Write HTML to file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\nSearch results saved as: {filename}")
        print(f"Current URL: {driver.current_url}")
        print(f"Page title: {driver.title}")
        
        # Extract product information from search results page (like Meesho)
        products_info = []
        
        # Try different selectors for product cards (simplified like Meesho)
        product_selectors = [
            "div._1AtVbE",  # Main product card container
            "div[data-id]",  # Generic product containers
            "div._2kHMtA",  # Alternative card selector
            "div._13oc-S",  # Another card selector
            "div[class*='product']",  # Generic product selector
            "div[class*='card']",  # Generic card selector
        ]
        
        product_cards = []
        for selector in product_selectors:
            try:
                cards = driver.find_elements(By.CSS_SELECTOR, selector)
                if cards and len(cards) > 1:  # More than 1 to avoid header/footer elements
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
        
        # Extract information from each product card (simplified like Meesho)
        for i, card in enumerate(product_cards[:max_results]):
            try:
                product_info = {}
                
                # Extract title from various possible elements (like Meesho approach)
                title_selectors = [
                    "div._4rR01T",  # Grid view title
                    "a.s1Q9rs",     # List view title
                    "h3.product-brand",  # Brand
                    "h4.product-product",  # Product name
                    "a[title]",     # Title attribute
                    "div[class*='title']",
                    "span[class*='title']",
                    "a",            # Any link
                    "div[class*='_4rR01T']",  # Alternative grid title
                    "span[class*='_4rR01T']", # Alternative grid title
                    "h3",           # Heading tags
                    "h2",           # Heading tags
                    "h1",           # Heading tags
                    "span._2mylT6", # Alternative title class
                    "div._2mylT6",  # Alternative title class
                    "span[class*='_2mylT6']", # Alternative title class
                    "div[class*='_2mylT6']",  # Alternative title class
                ]
                
                brand = ""
                product_name = ""
                full_title = ""
                
                for selector in title_selectors:
                    try:
                        title_elem = card.find_element(By.CSS_SELECTOR, selector)
                        title_text = title_elem.text.strip()
                        # Skip discount percentages and other non-product names (like Meesho)
                        if (title_text and len(title_text) > 5 and len(title_text) < 200 and
                            not title_text.endswith('%') and
                            not title_text.endswith('off') and
                            not title_text.startswith('%') and
                            'off' not in title_text.lower() and
                            not title_text.replace('%', '').replace('off', '').strip().isdigit()):
                            
                            if selector == "h3.product-brand":
                                brand = title_text
                            elif selector == "h4.product-product":
                                product_name = title_text
                            else:
                                if not full_title:
                                    full_title = title_text
                                    # Try to get link from the element or its parent
                                    try:
                                        if title_elem.tag_name == 'a':
                                            product_info['link'] = title_elem.get_attribute('href') or ''
                                        else:
                                            # Try to find a parent link
                                            parent_link = title_elem.find_element(By.XPATH, "./ancestor::a")
                                            if parent_link:
                                                product_info['link'] = parent_link.get_attribute('href') or ''
                                    except:
                                        pass
                    except:
                        continue
                
                # Smart title combination
                if brand and product_name:
                    product_info['title'] = f"{brand} {product_name}"
                elif brand and full_title:
                    # If we have brand and full title, combine them intelligently
                    if brand.lower() not in full_title.lower():
                        product_info['title'] = f"{brand} {full_title}"
                    else:
                        product_info['title'] = full_title
                elif product_name:
                    product_info['title'] = product_name
                elif full_title:
                    product_info['title'] = full_title
                
                # Store brand separately for easier access
                if brand:
                    product_info['brand'] = brand
                
                # If no title found, try to get it from the card's text content (like Meesho)
                if not product_info.get('title'):
                    try:
                        card_text = card.text.strip()
                        lines = card_text.split('\n')
                        for line in lines:
                            line = line.strip()
                            # Skip discount percentages, prices, delivery info, reviews, etc.
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
                                ':' not in line and  # Skip time formats
                                not line.replace(':', '').replace('h', '').replace('m', '').replace('s', '').replace(' ', '').isdigit()):
                                product_info['title'] = line
                                break
                    except:
                        pass
                
                # Extract price from various possible elements (simplified like Meesho)
                price_selectors = [
                    "div._30jeq3",  # Main price
                    "div[class*='_30jeq3']",
                    "span[class*='_30jeq3']",
                    "div[class*='_25b18c']",  # Alternative price selector
                    "span[class*='_25b18c']", # Alternative price selector
                    "div[class*='_16Jk6d']", # Another price selector
                    "span[class*='_16Jk6d']", # Another price selector
                    "div[class*='_1vC4OE']", # Another price selector
                    "span[class*='_1vC4OE']", # Another price selector
                    "div[class*='price']",
                    "span[class*='price']",
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
                
                # If no price found, try to extract from card text (like Meesho)
                if not product_info.get('price'):
                    try:
                        card_text = card.text.strip()
                        lines = card_text.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line.startswith('₹') and len(line) < 20:
                                product_info['price'] = line
                                break
                    except:
                        pass
                
                # Extract rating from various possible elements (simplified like Meesho)
                rating_selectors = [
                    "div._3LWZlK",  # Rating stars
                    "span[class*='rating']",
                    "div[class*='rating']",
                    "span[class*='_3LWZlK']",
                    "div[class*='_3LWZlK']",
                    "div[class*='_2d4LTz']", # Alternative rating selector
                    "span[class*='_2d4LTz']", # Alternative rating selector
                    "div[class*='_3uSWvM']", # Another rating selector
                    "span[class*='_3uSWvM']", # Another rating selector
                    "div[class*='_1i0wkb']", # New Flipkart rating selector
                    "span[class*='_1i0wkb']"
                ]
                
                for selector in rating_selectors:
                    try:
                        rating_elem = card.find_element(By.CSS_SELECTOR, selector)
                        rating_text = rating_elem.text.strip()
                        # Enhanced validation for ratings
                        if rating_text and len(rating_text) > 0:
                            import re
                            if re.match(r'^\d+(\.\d+)?$', rating_text) and float(rating_text) <= 5.0:
                                product_info['rating'] = rating_text
                                break
                    except:
                        continue
                
                # If no rating found, try to extract from card text (like Meesho)
                if not product_info.get('rating'):
                    try:
                        card_text = card.text.strip()
                        lines = card_text.split('\n')
                        for line in lines:
                            line = line.strip()
                            if line.replace('.', '').isdigit() and len(line) <= 4 and float(line) <= 5.0:
                                product_info['rating'] = line
                                break
                    except:
                        pass
                
                # Extract image URL (like Meesho)
                try:
                    img_elem = card.find_element(By.TAG_NAME, "img")
                    product_info['image_url'] = img_elem.get_attribute('src') or ''
                    product_info['image_alt'] = img_elem.get_attribute('alt') or ''
                except:
                    product_info['image_url'] = ''
                    product_info['image_alt'] = ''
                
                # Extract product link - the card itself might be the link (like Meesho)
                if not product_info.get('link'):
                    try:
                        # Check if the card element itself is an anchor tag
                        if card.tag_name.lower() == 'a':
                            href = card.get_attribute('href')
                            if href and '/p/' in href:
                                # Make sure it's a full URL
                                if href.startswith('/'):
                                    href = 'https://www.flipkart.com' + href
                                product_info['link'] = href
                    except:
                        pass
                
                # If still no link found, try to find anchor tags within the card (like Meesho)
                if not product_info.get('link'):
                    try:
                        # Look for any anchor tags within the card
                        link_elements = card.find_elements(By.TAG_NAME, "a")
                        for link_elem in link_elements:
                            href = link_elem.get_attribute('href')
                            if href and ('/p/' in href or 'flipkart.com' in href):
                                # Make sure it's a full URL
                                if href.startswith('/'):
                                    href = 'https://www.flipkart.com' + href
                                product_info['link'] = href
                                break
                    except:
                        pass
                
                # Extract brand (try to get from title or other elements) (like Meesho)
                try:
                    if product_info.get('title'):
                        # Enhanced brand list including clothing brands
                        common_brands = [
                            # Clothing brands
                            "SOPANI", "Arrow", "The Bear House", "STI", "Solstice", "Metronaut", "Rare Rabbit", "Park Avenue", "Allen Solly", 
                            "Van Heusen", "Peter England", "Louis Philippe", "Blackberrys", "Red Tape", "Campus Sutra", "The Indian Garage Co", 
                            "Hellcat", "Turtle", "Glitchez", "Vebnor", "Dhaduk", "Stoneberg", "Nike", "Adidas", "Puma", "Reebok", "Converse", 
                            "Vans", "New Balance", "Under Armour", "Skechers", "Fila", "Jordan", "Champion", "Levi's", "Tommy Hilfiger", 
                            "Calvin Klein", "H&M", "Zara", "Forever 21", "Uniqlo", "Gap", "American Eagle", "Hollister", "Abercrombie", 
                            "Ralph Lauren", "Lacoste", "Polo", "Gucci", "Prada", "Versace", "Armani", "Hugo Boss", "Diesel", "Guess", 
                            "Michael Kors", "Coach", "Kate Spade", "Tory Burch", "Ray-Ban", "Oakley", "Asics", "Mizuno", "Brooks", "Saucony",
                            # Tech brands
                            "Apple", "Samsung", "OnePlus", "Xiaomi", "Realme", "Vivo", "Oppo", "Motorola", "Nokia", "Sony", "LG", "HP", 
                            "Dell", "Lenovo", "Asus", "Acer", "MSI", "Google", "Nothing", "Honor", "POCO", "Redmi", "Mi", "JBL", "Boat", 
                            "Sennheiser", "Philips", "Panasonic", "Canon", "Nikon", "Flipkart"
                        ]
                        for brand in common_brands:
                            if brand.lower() in product_info['title'].lower():
                                product_info['brand'] = brand
                                break
                        
                        # If no brand found in common list, try to extract first word as brand
                        if not product_info.get('brand'):
                            title_words = product_info['title'].split()
                            if title_words:
                                # Take first word if it's not a common word or discount percentage
                                first_word = title_words[0].strip()
                                common_words = ["Modern", "Latest", "New", "Best", "Top", "Great", "Super", "Ultra", "Premium", "Quality", "Good", "Nice", "Cool", "Hot", "Trendy", "Stylish", "Fashionable", "Elegant", "Beautiful", "Amazing", "Wonderful", "Excellent", "Perfect", "Special", "Unique", "Exclusive", "Limited", "Classic", "Vintage", "Retro", "Contemporary", "Traditional", "Casual", "Formal", "Party", "Wedding", "Office", "Work", "Daily", "Everyday", "Weekend", "Holiday", "Summer", "Winter", "Spring", "Fall", "Seasonal", "Year", "Round"]
                                
                                # Skip discount percentages and numbers
                                if (first_word not in common_words and 
                                    len(first_word) > 2 and 
                                    not first_word.replace('%', '').replace('off', '').isdigit() and
                                    not first_word.endswith('%') and
                                    not first_word.endswith('off')):
                                    product_info['brand'] = first_word
                except:
                    pass
                
                # Extract category (try to infer from title) (like Meesho)
                try:
                    if product_info.get('title'):
                        title_lower = product_info['title'].lower()
                        if 'mobile' in title_lower or 'phone' in title_lower or 'smartphone' in title_lower or 'iphone' in title_lower or 'galaxy' in title_lower or 'android' in title_lower:
                            product_info['category'] = 'Mobile'
                        elif 'laptop' in title_lower or 'computer' in title_lower or 'notebook' in title_lower:
                            product_info['category'] = 'Laptop'
                        elif 'tablet' in title_lower or 'ipad' in title_lower:
                            product_info['category'] = 'Tablet'
                        elif 'headphone' in title_lower or 'earphone' in title_lower or 'speaker' in title_lower:
                            product_info['category'] = 'Audio'
                        elif 'watch' in title_lower or 'smartwatch' in title_lower:
                            product_info['category'] = 'Watch'
                        elif 'camera' in title_lower or 'dslr' in title_lower:
                            product_info['category'] = 'Camera'
                        elif 'saree' in title_lower:
                            product_info['category'] = 'Saree'
                        elif 'shirt' in title_lower:
                            product_info['category'] = 'Shirt'
                        elif 'pant' in title_lower:
                            product_info['category'] = 'Pant'
                        elif 'shoe' in title_lower:
                            product_info['category'] = 'Shoe'
                        elif 'dress' in title_lower:
                            product_info['category'] = 'Dress'
                        elif 'kurta' in title_lower:
                            product_info['category'] = 'Kurta'
                        elif 'jean' in title_lower:
                            product_info['category'] = 'Jeans'
                        elif 'top' in title_lower:
                            product_info['category'] = 'Top'
                        elif 'bottom' in title_lower:
                            product_info['category'] = 'Bottom'
                        else:
                            product_info['category'] = 'General'
                except:
                    pass
                
                # Extract reviews count (like Meesho)
                try:
                    card_text = card.text.strip()
                    lines = card_text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if ('rating' in line.lower() or 'review' in line.lower()) and ',' in line:
                            product_info['reviews_count'] = line
                            break
                except:
                    pass
                
                # Extract availability (like Meesho)
                try:
                    card_text = card.text.strip()
                    lines = card_text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if 'delivery' in line.lower() or 'stock' in line.lower() or 'available' in line.lower():
                            product_info['availability'] = line
                            break
                except:
                    pass
                
                # If we found any meaningful information, add it (like Meesho)
                if product_info.get('title') or product_info.get('price'):
                    products_info.append(product_info)
                    
            except Exception as e:
                print(f"Error extracting info from product {i+1}: {e}")
                continue
        
        # Display extracted information (like Meesho)
        if products_info:
            print(f"\n{'='*60}")
            print(f"EXTRACTED PRODUCT INFORMATION")
            print(f"{'='*60}")
            
            for i, product in enumerate(products_info, 1):
                print(f"\n{i}. {product.get('title', 'Title not found')}")
                print(f"   Price: {product.get('price', 'Price not found')}")
                if product.get('rating'):
                    print(f"   Rating: {product['rating']}")
                if product.get('brand'):
                    print(f"   Brand: {product['brand']}")
                if product.get('category'):
                    print(f"   Category: {product['category']}")
                if product.get('link'):
                    print(f"   Link: {product['link']}")
                if product.get('image_url'):
                    print(f"   Image: {product['image_url']}")
                print("-" * 50)
        else:
            print("No product information could be extracted.")

        # Display JSON data without saving to file (like Meesho)
        if products_info:
            json_data = {
                'query': query,
                'search_url': driver.current_url,
                'total_products': len(products_info),
                'products': products_info
            }
            print(f"\n{'='*60}")
            print(f"PRODUCT DATA (JSON FORMAT)")
            print(f"{'='*60}")
            print(json.dumps(json_data, indent=2, ensure_ascii=False))
            
            # Create detailed products from search results data (like Meesho)
            detailed_products = []
            
            print(f"\n{'='*60}")
            print(f"CREATING DETAILED PRODUCTS FROM SEARCH RESULTS")
            print(f"{'='*60}")
            
            # Take the first 3 products with the most complete information
            best_products = []
            for product in products_info:
                if product.get('title') and product.get('price'):
                    best_products.append(product)
                    if len(best_products) >= 3:
                        break
            
            for i, product in enumerate(best_products, 1):
                try:
                    print(f"\nProcessing product {i}: {product.get('title', 'Unknown')}")
                    
                    detailed_product = {
                        "name": product.get('title', ''),
                        "price": product.get('price', ''),
                        "brand": product.get('brand', ''),
                        "category": product.get('category', ''),
                        "rating": product.get('rating', ''),
                        "link": product.get('link', ''),
                        "images": [{"url": product.get('image_url', ''), "alt": product.get('image_alt', ''), "thumbnail": product.get('image_url', '')}] if product.get('image_url') else []
                    }
                    
                    detailed_products.append(detailed_product)
                    print(f"✅ Successfully processed product {i}")
                    
                except Exception as e:
                    print(f"❌ Error processing product {i}: {e}")
                    continue
            
            # Display detailed product information
            if detailed_products:
                print(f"\n{'='*80}")
                print(f"FINAL RESULTS - {len(detailed_products)} PRODUCTS")
                print(f"{'='*80}")
                
                for i, product in enumerate(detailed_products, 1):
                    print(f"\n{i}. {product.get('name', 'Name not found')}")
                    print(f"   Price: {product.get('price', 'Price not found')}")
                    print(f"   Brand: {product.get('brand', 'Brand not found')}")
                    print(f"   Category: {product.get('category', 'Category not found')}")
                    print(f"   Rating: {product.get('rating', 'Rating not found')}")
                    print(f"   Images: {len(product.get('images', []))} images found")
                    if product.get('images'):
                        print(f"   Main Image: {product['images'][0]['url']}")
                    print(f"   Link: {product.get('link', 'Link not found')}")
                    print("-" * 80)
                
                # Display detailed products JSON without saving to file (like Meesho)
                detailed_json_data = {
                    'query': query,
                    'search_url': driver.current_url,
                    'total_products': len(detailed_products),
                    'products': detailed_products
                }
                print(f"\n{'='*60}")
                print(f"DETAILED PRODUCT DATA (JSON FORMAT)")
                print(f"{'='*60}")
                print(json.dumps(detailed_json_data, indent=2, ensure_ascii=False))
            else:
                print("\nNo detailed product information could be extracted.")

        print(f"\nFiles created:")
        print(f"- {filename} (Search results HTML)")
        print("JSON data displayed in console (no files saved)")
        
        print("Closing browser automatically...")
        
        # Return structured data for intelligent search system (like Meesho)
        if products_info:
            result = {
                "site": "Flipkart",
                "query": query,
                "total_products": len(products_info),
                "basic_products": products_info,
                "detailed_products": detailed_products if detailed_products else []
            }
            
            print(f"✅ Flipkart search completed: Found {len(products_info)} products")
            return result
        else:
            print("⚠️ No products found on Flipkart")
            return {
                "site": "Flipkart", 
                "query": query,
                "total_products": 0,
                "basic_products": [],
                "detailed_products": []
            }

    except Exception as e:
        print(f"❌ Flipkart search error: {e}")
        return {
            "site": "Flipkart",
            "query": query, 
            "total_products": 0,
            "products": [],
            "error": str(e)
        }
    finally:
        driver.quit()

if __name__ == "__main__":
    # get query from CLI arg or input
    query: Optional[str] = None
    headless_flag = False

    if len(sys.argv) >= 2:
        # allow e.g. python flipkart_search.py "iphone 14"
        query = " ".join(sys.argv[1:])
    else:
        query = input("Enter product to search on Flipkart: ").strip()

    # If user included --headless keyword, detect it (optional)
    if query and "--headless" in query:
        headless_flag = True
        query = query.replace("--headless", "").strip()

    if not query:
        print("No query provided. Exiting.")
        sys.exit(1)

    search_flipkart(query, headless=headless_flag)
