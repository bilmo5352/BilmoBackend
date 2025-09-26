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
        
        # Extract rating - comprehensive selectors
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
                rating_elem = driver.find_element(By.CSS_SELECTOR, selector)
                rating_text = rating_elem.text.strip()
                if rating_text and rating_text.replace('.', '').replace(',', '').isdigit():
                    product_details["rating"] = rating_text
                    print(f"    Found rating: {rating_text}")
                    break
            except:
                continue
        
        # If brand not found in breadcrumbs, try to extract from product name
        if not product_details["brand"] and product_details["name"]:
            name_parts = product_details["name"].split()
            if name_parts:
                # Common brand names that might be at the start
                common_brands = ["Apple", "Samsung", "OnePlus", "Xiaomi", "Realme", "Vivo", "Oppo", "Motorola", "Nokia", "Sony", "LG", "HP", "Dell", "Lenovo", "Asus", "Acer", "MSI", "Google", "Nothing", "Honor", "POCO"]
                for brand in common_brands:
                    if brand.lower() in product_details["name"].lower():
                        product_details["brand"] = brand
                        print(f"    Found brand from name: {brand}")
                        break
        
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
    driver = create_driver(headless=headless)
    try:
        driver.get("https://www.flipkart.com")
        wait = WebDriverWait(driver, 10)

        # Close login popup if present
        close_flipkart_login_popup(driver)

        # Search input
        search_input = wait.until(EC.presence_of_element_located((By.NAME, "q")))
        search_input.clear()
        search_input.send_keys(query)
        search_input.send_keys(Keys.ENTER)

        # Wait for search results to load
        print("Waiting for search results to load...")
        time.sleep(5)  # Give more time for results to load
        
        # Save the HTML content of the search results page
        html_content = driver.page_source
        filename = f"flipkart_search_{query.replace(' ', '_')}.html"
        
        # Write HTML to file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\nSearch results saved as: {filename}")
        print(f"Current URL: {driver.current_url}")
        print(f"Page title: {driver.title}")
        
        # Extract detailed product information
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
                            product_info['title'] = title_text
                            product_info['link'] = title_elem.get_attribute('href') or ''
                            break
                    except:
                        continue
                
                # More comprehensive price selectors
                price_selectors = [
                    "div._30jeq3",  # Main price
                    "div[class*='_30jeq3']",
                    "span[class*='price']",
                    "div[class*='price']",
                    "span[class*='_30jeq3']",
                    "div[class*='_25b18c']",  # Alternative price selector
                    "span[class*='_25b18c']", # Alternative price selector
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
                
                # More comprehensive rating selectors
                rating_selectors = [
                    "div._3LWZlK",  # Rating stars
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
                
                # More comprehensive review selectors
                review_selectors = [
                    "span._2_R_DZ",  # Reviews count
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
                
                # More comprehensive discount selectors
                discount_selectors = [
                    "div._3Ay6Sb",  # Discount percentage
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
                if product.get('rating'):
                    print(f"   Rating: {product['rating']}")
                if product.get('reviews'):
                    print(f"   Reviews: {product['reviews']}")
                if product.get('discount'):
                    print(f"   Discount: {product['discount']}")
                if product.get('link'):
                    print(f"   Link: {product['link']}")
                print("-" * 50)
        else:
            print("No product information could be extracted.")

        # Save extracted data to JSON file
        if products_info:
            json_filename = f"flipkart_products_{query.replace(' ', '_')}.json"
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
                    
                    # Find the product card and click on it
                    if i < len(product_cards):
                        product_card = product_cards[i]
                        clickable_elements = product_card.find_elements(By.TAG_NAME, "a")
                        
                        if clickable_elements:
                            product_link = clickable_elements[0]
                            product_link.click()
                            
                            # Wait for page to load
                            time.sleep(3)
                            
                            # Check if new tab opened
                            if len(driver.window_handles) > 1:
                                driver.switch_to.window(driver.window_handles[-1])
                                print(f"  Switched to product page: {driver.current_url}")
                                
                                # Extract detailed product information
                                detailed_product = extract_product_details(driver)
                                detailed_products.append(detailed_product)
                                
                                # Close the product tab and go back to search results
                                driver.close()
                                driver.switch_to.window(driver.window_handles[0])
                                time.sleep(1)
                            else:
                                print(f"  No new tab opened for product {i+1}")
                                
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
                    print(f"   Brand: {product.get('brand', 'Brand not found')}")
                    print(f"   Category: {product.get('category', 'Category not found')}")
                    print(f"   Rating: {product.get('rating', 'Rating not found')}")
                    print(f"   Images: {len(product.get('images', []))} images found")
                    if product.get('images'):
                        print(f"   Main Image: {product['images'][0]['url']}")
                    print(f"   Link: {product.get('link', 'Link not found')}")
                    print("-" * 80)
                
                # Save detailed products to JSON
                detailed_json_filename = f"flipkart_detailed_products_{query.replace(' ', '_')}.json"
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
