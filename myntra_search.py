#!/usr/bin/env python3
"""
myntra_search.py
Usage:
  python myntra_search.py "puma shoes"
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
    
    # Realistic user agent
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # Let Selenium handle ChromeDriver automatically (most reliable approach)
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # Execute script to remove webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_script("delete navigator.__proto__.webdriver")
        
        print("✅ Myntra WebDriver initialized successfully")
        return driver
        
    except Exception as e:
        print(f"❌ Failed to create Chrome driver: {e}")
        print("Please ensure Chrome browser is installed and up to date.")
        raise e

def extract_product_details(driver: webdriver.Chrome) -> dict:
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
        # Wait for page to fully load
        time.sleep(2)
        
        # Extract product name - Myntra-specific selectors
        name_selectors = [
            "h1.pdp-title",  # Main product title
            "h1[class*='pdp-title']",
            "h1[class*='title']",
            "span[class*='title']",
            "div[class*='title']",
            "h1",
            "h2",
            "div[class*='product-name']",
            "span[class*='product-name']",
            "div.pdp-product-name",  # Myntra specific
            "span.pdp-product-name",  # Myntra specific
            "div[class*='pdp-product']",  # Myntra specific
            "span[class*='pdp-product']",  # Myntra specific
            "div[class*='product-title']",  # Myntra specific
            "span[class*='product-title']"  # Myntra specific
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
            "div.pdp-price",  # Price div
            "span[class*='pdp-price']",
            "div[class*='pdp-price']",
            "span[class*='price']",
            "div[class*='price']",
            "span[class*='selling-price']",
            "div[class*='selling-price']",
            "span[class*='mrp']",
            "div[class*='mrp']"
        ]
        
        for selector in price_selectors:
            try:
                price_elem = driver.find_element(By.CSS_SELECTOR, selector)
                price_text = price_elem.text.strip()
                if price_text and ('₹' in price_text or 'Rs' in price_text or 'INR' in price_text):
                    product_details["price"] = price_text
                    print(f"    Found price: {price_text}")
                    break
            except:
                continue
        
        # Extract brand (from breadcrumbs or product name)
        try:
            breadcrumb_selectors = [
                "nav.breadcrumb a",
                "div.breadcrumb a",
                "nav[class*='breadcrumb'] a",
                "div[class*='breadcrumb'] a",
                "nav a",
                "div[class*='nav'] a"
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
        
        # Extract rating - Comprehensive Myntra rating extraction with debugging
        print("    Starting rating extraction...")
        
        # First, let's see what rating-related elements exist on the page
        rating_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'rating') or contains(@class, 'star') or contains(@class, 'review') or contains(text(), '★') or contains(text(), '⭐') or contains(text(), 'out of')]")
        print(f"    Found {len(rating_elements)} rating-related elements on page")
        
        for i, elem in enumerate(rating_elements[:10]):  # Check first 10 elements
            try:
                elem_text = elem.text.strip()
                elem_class = elem.get_attribute('class') or ''
                elem_tag = elem.tag_name
                if elem_text:
                    print(f"      Rating element {i+1}: tag={elem_tag}, class='{elem_class[:50]}', text='{elem_text[:50]}'")
            except:
                continue
        
        rating_selectors = [
            "div[class*='rating'] span",  # Rating span in div
            "span[class*='rating']",  # Rating span
            "div[class*='rating']",  # Rating div
            "div[class*='star'] span",  # Star rating span
            "span[class*='star']",  # Star rating span
            "div[class*='review'] span",  # Review rating span
            "span[class*='review']",  # Review rating span
            "div[class*='pdp-rating']",  # Myntra PDP rating
            "span[class*='pdp-rating']",  # Myntra PDP rating
            "div[class*='product-rating']",  # Product rating
            "span[class*='product-rating']",  # Product rating
            "div[class*='avg-rating']",  # Average rating
            "span[class*='avg-rating']",  # Average rating
            "div[class*='score']",  # Score
            "span[class*='score']",  # Score
            "div[class*='feedback']",  # Feedback
            "span[class*='feedback']",  # Feedback
            "div[class*='customer']",  # Customer rating
            "span[class*='customer']",  # Customer rating
            "div[class*='review-count']",  # Review count
            "span[class*='review-count']",  # Review count
            "div[class*='rating-count']",  # Rating count
            "span[class*='rating-count']"  # Rating count
        ]
        
        rating_found = False
        for i, selector in enumerate(rating_selectors):
            try:
                rating_elems = driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"    Rating selector {i+1} ({selector}): Found {len(rating_elems)} elements")
                
                for rating_elem in rating_elems:
                    try:
                        rating_text = rating_elem.text.strip()
                        print(f"      Rating text: '{rating_text}'")
                        
                        # More lenient validation - look for any rating-like text
                        if rating_text and len(rating_text) > 0:
                            # Check if it looks like a rating
                            is_rating = (
                                'out of' in rating_text.lower() or 
                                'star' in rating_text.lower() or 
                                '★' in rating_text or 
                                '⭐' in rating_text or
                                rating_text.replace('.', '').replace(',', '').replace('(', '').replace(')', '').isdigit() or
                                ('/' in rating_text and any(char.isdigit() for char in rating_text)) or
                                ('(' in rating_text and ')' in rating_text and any(char.isdigit() for char in rating_text))
                            )
                            
                            if is_rating:
                                product_details["rating"] = rating_text
                                print(f"    ✅ Found rating: {rating_text}")
                                rating_found = True
                                break
                    except Exception as e:
                        print(f"      Error processing rating element: {e}")
                        continue
                
                if rating_found:
                    break
            except Exception as e:
                print(f"    Error with rating selector {selector}: {e}")
                continue
        
        # Try XPath for ratings if CSS selectors didn't work
        if not rating_found:
            print("    Trying XPath for ratings...")
            try:
                rating_xpaths = [
                    "//*[contains(text(), 'out of')]",
                    "//*[contains(text(), '★')]",
                    "//*[contains(text(), '⭐')]",
                    "//*[contains(@class, 'rating')]",
                    "//*[contains(@class, 'star')]",
                    "//*[contains(@class, 'review')]",
                    "//span[contains(text(), '4.') or contains(text(), '3.') or contains(text(), '2.') or contains(text(), '1.')]",
                    "//div[contains(text(), '4.') or contains(text(), '3.') or contains(text(), '2.') or contains(text(), '1.')]"
                ]
                
                for i, xpath in enumerate(rating_xpaths):
                    try:
                        rating_elems = driver.find_elements(By.XPATH, xpath)
                        print(f"    Rating XPath {i+1} ({xpath}): Found {len(rating_elems)} elements")
                        
                        for rating_elem in rating_elems:
                            try:
                                rating_text = rating_elem.text.strip()
                                print(f"      XPath rating text: '{rating_text}'")
                                
                                if rating_text and len(rating_text) > 0:
                                    product_details["rating"] = rating_text
                                    print(f"    ✅ Found rating via XPath: {rating_text}")
                                    rating_found = True
                                    break
                            except:
                                continue
                        
                        if rating_found:
                            break
                    except Exception as e:
                        print(f"    Error with rating XPath {xpath}: {e}")
                        continue
            except Exception as e:
                print(f"    XPath rating extraction failed: {e}")
        
        if not rating_found:
            print("    ❌ No rating found - Myntra may not display ratings on product pages")
        
        # If brand not found in breadcrumbs, try to extract from product name
        if not product_details["brand"] and product_details["name"]:
            name_parts = product_details["name"].split()
            if name_parts:
                # Common brand names that might be at the start
                common_brands = ["Nike", "Adidas", "Puma", "Reebok", "Converse", "Vans", "New Balance", "Under Armour", "Skechers", "Fila", "Jordan", "Champion", "Levi's", "Tommy Hilfiger", "Calvin Klein", "H&M", "Zara", "Forever 21", "Uniqlo", "Gap", "American Eagle", "Hollister", "Abercrombie", "Ralph Lauren", "Lacoste", "Polo", "Gucci", "Prada", "Versace", "Armani", "Hugo Boss", "Diesel", "Guess", "Michael Kors", "Coach", "Kate Spade", "Tory Burch", "Ray-Ban", "Oakley", "Puma", "Reebok", "Asics", "Mizuno", "Brooks", "Saucony"]
                for brand in common_brands:
                    if brand.lower() in product_details["name"].lower():
                        product_details["brand"] = brand
                        print(f"    Found brand from name: {brand}")
                        break
        
        # Extract product images - Enhanced Myntra-specific approach
        try:
            print(f"    Starting image extraction...")
            
            # Wait longer for images to load
            time.sleep(3)
            
            # First, let's see what images are actually on the page
            all_page_images = driver.find_elements(By.TAG_NAME, "img")
            print(f"    Total images on page: {len(all_page_images)}")
            
            # Check first few images to understand the structure
            for i, img in enumerate(all_page_images[:10]):
                try:
                    img_src = img.get_attribute('src')
                    img_alt = img.get_attribute('alt') or ''
                    img_class = img.get_attribute('class') or ''
                    if img_src:
                        print(f"      Image {i+1}: src={img_src[:80]}... alt='{img_alt[:30]}' class='{img_class[:50]}'")
                except:
                    continue
            
            # Myntra-specific image selectors (more comprehensive)
            image_selectors = [
                "img[class*='image-grid']",  # Myntra image grid
                "img[class*='pdp-image']",  # PDP (Product Detail Page) image
                "img[class*='zoom-image']",  # Zoom image
                "img[class*='main-image']",  # Main product image
                "img[class*='product-image']",  # Product image
                "img[class*='hero-image']",  # Hero image
                "img[class*='thumbnail']",  # Thumbnail image
                "img[class*='gallery']",  # Gallery image
                "img[class*='carousel']",  # Carousel image
                "img[class*='pdp']",  # PDP image
                "img[class*='product']",  # Product image
                "div[class*='image'] img",  # Image in div
                "div[class*='gallery'] img",  # Gallery image
                "div[class*='carousel'] img",  # Carousel image
                "div[class*='pdp'] img",  # PDP div image
                "div[class*='product'] img",  # Product div image
                "div[class*='image-grid'] img",  # Image grid div
                "div[class*='zoom'] img",  # Zoom div
                "div[class*='main'] img",  # Main div
                "div[class*='hero'] img",  # Hero div
                "img[src*='myntra']",  # Any image with myntra in src
                "img[src*='cloudinary']",  # Any image with cloudinary in src
                "img[src*='amazonaws']",  # Any image with amazonaws in src
                "img[src*='images']",  # Any image with images in src
                "img[src*='cdn']"  # Any image with cdn in src
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
                            img_class = img.get_attribute('class') or ''
                            
                            # Debug: print image details
                            if img_src:
                                print(f"      Image src: {img_src[:100]}...")
                                print(f"      Image alt: {img_alt[:50]}")
                                print(f"      Image class: {img_class[:50]}")
                            
                            # More lenient filtering - accept any image that looks like a product image
                            if img_src and len(img_src) > 20 and 'placeholder' not in img_src.lower() and 'icon' not in img_src.lower():
                                # Check if it's a product-related image
                                is_product_image = (
                                    'myntra' in img_src.lower() or 
                                    'cloudinary' in img_src.lower() or 
                                    'amazonaws' in img_src.lower() or
                                    'images' in img_src.lower() or
                                    'cdn' in img_src.lower() or
                                    'product' in img_class.lower() or
                                    'pdp' in img_class.lower() or
                                    'gallery' in img_class.lower() or
                                    'carousel' in img_class.lower()
                                )
                                
                                if is_product_image:
                                    # Get high-resolution image URL
                                    high_res_src = img_src
                                    if 'q=' in img_src:
                                        high_res_src = img_src.replace('q=70', 'q=100').replace('q=50', 'q=100')
                                    
                                    # Avoid duplicates
                                    if high_res_src not in found_images:
                                        found_images.add(high_res_src)
                                        
                                        image_info = {
                                            "url": high_res_src,
                                            "alt": img_alt,
                                            "thumbnail": img_src
                                        }
                                        
                                        all_images.append(image_info)
                                        print(f"      ✅ Added image: {img_alt[:50]}...")
                                        
                        except Exception as img_error:
                            print(f"      Error processing image: {img_error}")
                            continue
                                
                except Exception as e:
                    print(f"    Error with selector {selector}: {e}")
                    continue
            
            # Also try to find images using XPath with more patterns
            try:
                print(f"    Trying XPath image extraction...")
                xpath_patterns = [
                    "//img[contains(@src, 'myntra')]",
                    "//img[contains(@src, 'cloudinary')]",
                    "//img[contains(@src, 'amazonaws')]",
                    "//img[contains(@src, 'images')]",
                    "//img[contains(@src, 'cdn')]",
                    "//img[contains(@class, 'product')]",
                    "//img[contains(@class, 'pdp')]",
                    "//img[contains(@class, 'gallery')]",
                    "//img[contains(@class, 'carousel')]"
                ]
                
                for xpath in xpath_patterns:
                    try:
                        xpath_images = driver.find_elements(By.XPATH, xpath)
                        print(f"    Found {len(xpath_images)} images via XPath: {xpath}")
                        
                        for img in xpath_images:
                            try:
                                img_src = img.get_attribute('src')
                                img_alt = img.get_attribute('alt') or ''
                                
                                if img_src and 'placeholder' not in img_src.lower() and 'icon' not in img_src.lower():
                                    high_res_src = img_src
                                    if 'q=' in img_src:
                                        high_res_src = img_src.replace('q=70', 'q=100').replace('q=50', 'q=100')
                                    
                                    if high_res_src not in found_images:
                                        found_images.add(high_res_src)
                                        
                                        image_info = {
                                            "url": high_res_src,
                                            "alt": img_alt,
                                            "thumbnail": img_src
                                        }
                                        
                                        all_images.append(image_info)
                                        print(f"      ✅ Added XPath image: {img_alt[:50]}...")
                            except:
                                continue
                    except:
                        continue
            except Exception as xpath_error:
                print(f"    XPath image extraction error: {xpath_error}")
            
            # Limit to first 5 images to avoid too much data
            product_details["images"] = all_images[:5]
            print(f"    Final result: Found {len(product_details['images'])} product images")
            
            # Debug: print all found image URLs
            if product_details["images"]:
                for i, img in enumerate(product_details["images"]):
                    print(f"    Image {i+1} URL: {img['url']}")
            else:
                print(f"    ❌ No images found!")
            
        except Exception as e:
            print(f"    Error extracting images: {e}")
            product_details["images"] = []
        
        # Debug: Print what we found
        print(f"    Final extracted data: {product_details}")
        
    except Exception as e:
        print(f"    Error extracting product details: {e}")
    
    return product_details

def search_myntra(query: str, headless: bool = False):
    driver = None
    try:
        driver = create_driver(headless=headless)
        wait = WebDriverWait(driver, 10)

        print(f"Searching Myntra for: {query}")
        
        # Navigate to Myntra
        driver.get("https://www.myntra.com")
        time.sleep(3)
        
        # Search input
        search_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.desktop-searchBar")))
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.ENTER)

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
        
        # Try different selectors for product cards
        product_selectors = [
            "li.product-base",  # Main product card container
            "div[class*='product']",  # Generic product containers
            "div[class*='card']",  # Alternative card selector
            "div[class*='item']",  # Another card selector
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
            return {
                "site": "Myntra",
                "query": query,
                "total_products": 0,
                "products": []
            }
        
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
        for i, card in enumerate(product_cards[:8]):
            try:
                product_info = {}
                
                # More comprehensive title selectors
                title_selectors = [
                    "h3.product-brand",  # Brand
                    "h4.product-product",  # Product name
                    "a[title]",     # Title attribute
                    "div[class*='title']",
                    "span[class*='title']",
                    "a",            # Any link
                    "h3",           # Heading tags
                    "h4",           # Heading tags
                    "h2",           # Heading tags
                ]
                
                brand = ""
                product_name = ""
                for selector in title_selectors:
                    try:
                        title_elem = card.find_element(By.CSS_SELECTOR, selector)
                        title_text = title_elem.text.strip()
                        if title_text and len(title_text) > 2:  # Only use if meaningful text
                            if selector == "h3.product-brand":
                                brand = title_text
                            elif selector == "h4.product-product":
                                product_name = title_text
                            else:
                                if not product_info.get('title'):
                                    product_info['title'] = title_text
                                    product_info['link'] = title_elem.get_attribute('href') or ''
                    except:
                        continue
                
                # Combine brand and product name
                if brand and product_name:
                    product_info['title'] = f"{brand} {product_name}"
                elif brand:
                    product_info['title'] = brand
                elif product_name:
                    product_info['title'] = product_name
                
                # More comprehensive price selectors
                price_selectors = [
                    "span.product-discountedPrice",  # Main price
                    "span.product-strike",  # Strike price
                    "span[class*='price']",
                    "div[class*='price']",
                    "span[class*='discounted']",
                    "div[class*='discounted']",
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
                    "div.rating",
                    "span[class*='rating']",
                    "div[class*='rating']",
                    "span[class*='star']",
                    "div[class*='star']",
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
                if product.get('link'):
                    print(f"   Link: {product['link']}")
                print("-" * 50)
        else:
            print("No product information could be extracted.")
            # Return empty result for intelligent search system
            return {
                "site": "Myntra",
                "query": query,
                "total_products": 0,
                "products": []
            }

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
        
        # Return structured data for intelligent search system
        return {
            "site": "Myntra",
            "query": query,
            "total_products": len(products_info),
            "products": products_info
        }

    except Exception as e:
        print(f"Error occurred: {e}")
        print("Make sure you have Chrome browser installed and internet connection.")
        return {
            "site": "Myntra",
            "query": query,
            "total_products": 0,
            "products": []
        }
    finally:
        if driver:
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