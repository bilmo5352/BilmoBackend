#!/usr/bin/env python3
"""
Flipkart Homepage Deals Scraper
Scrapes deals and offers from Flipkart India homepage
"""

import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_driver(headless: bool = True) -> webdriver.Chrome:
    """Create a Chrome WebDriver with stable settings"""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--window-size=1920,1080")
    
    # Enhanced anti-detection measures
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option("detach", True)
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("Flipkart Deals WebDriver initialized with ChromeDriverManager")
    except Exception as e:
        logger.error(f"ChromeDriverManager failed: {e}")
        try:
            driver = webdriver.Chrome(options=chrome_options)
            logger.info("Flipkart Deals WebDriver initialized with system ChromeDriver")
        except Exception as e2:
            logger.error(f"All ChromeDriver methods failed: {e2}")
            raise e2
    
    # Execute JavaScript to remove webdriver properties
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_script("delete navigator.__proto__.webdriver")
    driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
    driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
    driver.execute_script("window.chrome = {runtime: {}}")
    
    return driver

def scrape_flipkart_homepage_deals(headless: bool = True, max_items_per_section: int = 10):
    """Scrape Flipkart homepage focusing on actual product deals with prices"""
    driver = create_driver(headless=headless)
    all_sections = []
    
    try:
        logger.info("🏠 Visiting Flipkart India homepage...")
        driver.get("https://www.flipkart.com")
        time.sleep(10)  # Wait longer for page to load
        
        # Scroll down to load content
        logger.info("📜 Scrolling to load deals...")
        for i in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
        
        # Scroll back to top
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(5)
        
        logger.info("🔍 Extracting product deals with prices...")
        
        # Strategy 1: Look for actual product cards with images and prices
        logger.info("🛍️ Looking for product cards with images and prices...")
        
        # Find all elements that contain both product links and price text
        all_elements = driver.find_elements(By.CSS_SELECTOR, "div, section, article")
        product_containers = []
        
        for elem in all_elements:
            try:
                # Check if this element has product links
                product_links = elem.find_elements(By.CSS_SELECTOR, "a[href*='/p/']")
                if not product_links:
                    continue
                
                # Check if this element has price text
                elem_text = elem.text
                has_price = False
                if elem_text and ('₹' in elem_text or 'Rs' in elem_text):
                    # Check if it's a valid price (not just text containing rupee symbol)
                    lines = elem_text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and ('₹' in line or 'Rs' in line):
                            # Extract numbers from the line
                            import re
                            numbers = re.findall(r'[\d,]+', line)
                            if numbers and any(len(num.replace(',', '')) >= 3 for num in numbers):
                                has_price = True
                                break
                
                if has_price:
                    product_containers.append(elem)
                    
            except Exception as e:
                logger.debug(f"Error checking element: {e}")
                continue
        
        logger.info(f"   Found {len(product_containers)} containers with products and prices")
        
        sections_found = {}
        
        for container in product_containers[:20]:  # Check first 20 containers
            try:
                # Extract section title
                section_title = extract_section_title_from_card(container)
                if not section_title:
                    section_title = "Featured Products"
                
                # Extract products from this container
                products = []
                product_links = container.find_elements(By.CSS_SELECTOR, "a[href*='/p/']")
                
                for link in product_links[:max_items_per_section]:
                    product_info = extract_product_info_from_container(link, container)
                    if product_info and is_valid_product(product_info) and product_info.get('price'):
                        products.append(product_info)
                
                if products:
                    if section_title not in sections_found:
                        sections_found[section_title] = []
                    sections_found[section_title].extend(products)
                    logger.info(f"  ✅ Found {len(products)} products with prices in '{section_title}'")
                    
            except Exception as e:
                logger.debug(f"Error processing container: {e}")
                continue
        
        # Strategy 2: Look for specific deal banners and sections
        logger.info("🎯 Looking for deal banners...")
        deal_selectors = [
            "div[class*='banner']",
            "div[class*='promo']",
            "div[class*='offer']",
            "div[class*='deal']",
            "div[class*='flash']",
            "div[class*='sale']"
        ]
        
        for selector in deal_selectors:
            try:
                deal_containers = driver.find_elements(By.CSS_SELECTOR, selector)
                for container in deal_containers[:5]:  # Check first 5
                    products = extract_products_from_deal_container(container, driver, max_items_per_section)
                    if products:
                        section_title = extract_section_title_from_card(container) or "Special Deals"
                        if section_title not in sections_found:
                            sections_found[section_title] = []
                        sections_found[section_title].extend(products)
                        logger.info(f"  ✅ Found {len(products)} products in deal banner '{section_title}'")
            except Exception as e:
                logger.debug(f"Error with deal selector {selector}: {e}")
                continue
        
        # Strategy 3: Direct product link extraction with better price detection
        logger.info("🔗 Extracting direct product links with prices...")
        all_product_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/p/']")
        logger.info(f"   Found {len(all_product_links)} total product links")
        
        direct_products = {}
        for link in all_product_links[:max_items_per_section * 3]:
            try:
                # Find parent container
                parent_section = find_product_parent_section(link, driver)
                section_title = extract_section_title_from_parent(parent_section) if parent_section else "Direct Products"
                
                product_info = extract_product_info_from_container(link, parent_section)
                if product_info and is_valid_product(product_info) and product_info.get('price'):
                    if section_title not in direct_products:
                        direct_products[section_title] = []
                    direct_products[section_title].append(product_info)
            except Exception as e:
                logger.debug(f"Error processing direct link: {e}")
                continue
        
        # Merge all sections
        for section_title, products in sections_found.items():
            if products:
                section_data = {
                    'section_title': section_title,
                    'item_count': len(products),
                    'items': products[:max_items_per_section]
                }
                all_sections.append(section_data)
        
        for section_title, products in direct_products.items():
            if products and not any(s['section_title'] == section_title for s in all_sections):
                section_data = {
                    'section_title': section_title,
                    'item_count': len(products),
                    'items': products[:max_items_per_section]
                }
                all_sections.append(section_data)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📦 TOTAL SECTIONS EXTRACTED: {len(all_sections)}")
        total_items = sum(s['item_count'] for s in all_sections)
        logger.info(f"📦 TOTAL ITEMS EXTRACTED: {total_items}")
        logger.info(f"{'='*60}")
        
        # Save to JSON file
        homepage_data = {
            'timestamp': datetime.now().isoformat(),
            'source': 'Flipkart India Homepage',
            'total_sections': len(all_sections),
            'total_items': total_items,
            'sections': all_sections
        }
        
        with open('flipkart_homepage_deals.json', 'w', encoding='utf-8') as f:
            json.dump(homepage_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Saved {len(all_sections)} sections to flipkart_homepage_deals.json")
        
        return homepage_data
        
    except Exception as e:
        logger.error(f"❌ Error scraping Flipkart homepage: {e}")
        return {
            'timestamp': datetime.now().isoformat(),
            'source': 'Flipkart India Homepage',
            'total_deals': 0,
            'deals': [],
            'error': str(e)
        }
    finally:
        driver.quit()

def extract_section_title_from_card(card_element):
    """Extract section title from a product card"""
    try:
        # Look for headings in the card
        title_selectors = ["h1", "h2", "h3", "h4", "h5", "h6", "span", "div"]
        
        for selector in title_selectors:
            try:
                title_elem = card_element.find_element(By.CSS_SELECTOR, selector)
                title_text = title_elem.text.strip()
                if title_text and len(title_text) > 5 and len(title_text) < 100:
                    # Clean up the title
                    title_text = title_text.replace('\n', ' ').strip()
                    return title_text
            except:
                continue
        
        return None
    except:
        return None

def extract_product_info_improved(link_element, parent_element):
    """Extract detailed product information with better accuracy"""
    product_info = {
        'title': '',
        'price': '',
        'discount': '',
        'image': '',
        'link': ''
    }
    
    try:
        # Extract link
        link = link_element.get_attribute('href') or ''
        if link:
            if link.startswith('/'):
                link = 'https://www.flipkart.com' + link
            product_info['link'] = link
        
        # Extract title - try multiple methods
        title = ''
        
        # Method 1: aria-label
        title = link_element.get_attribute('aria-label') or ''
        
        # Method 2: image alt text
        if not title:
            try:
                img = link_element.find_element(By.TAG_NAME, 'img')
                title = img.get_attribute('alt') or ''
            except:
                pass
        
        # Method 3: text content
        if not title:
            title = link_element.text.strip()
        
        # Method 4: Look in parent for title
        if not title and parent_element:
            try:
                title_elem = parent_element.find_element(By.CSS_SELECTOR, "span, div, p")
                title = title_elem.text.strip()
            except:
                pass
        
        # Clean up title
        if title:
            title = title.split('\n')[0].strip()
            title = title.split('(')[0].strip()
            # Filter out invalid titles
            if len(title) > 5 and len(title) < 200 and not title.lower().startswith('mailto:'):
                product_info['title'] = title
        
        # Extract image
        try:
            img = link_element.find_element(By.TAG_NAME, 'img')
            img_src = img.get_attribute('src') or ''
            if img_src and ('flipkart' in img_src.lower() or 'img' in img_src.lower()):
                product_info['image'] = img_src
        except:
            pass
        
        # Extract price - look in parent element
        if parent_element:
            try:
                price_selectors = [
                    # Flipkart specific price selectors
                    "span[class*='_30jeq3']",
                    "div[class*='_30jeq3']",
                    "span[class*='_1vC4OE']",
                    "div[class*='_1vC4OE']",
                    "span[class*='_25b18c']",
                    "div[class*='_25b18c']",
                    "span[class*='_3tbKJd']",
                    "div[class*='_3tbKJd']",
                    "span[class*='_2tW1I0']",
                    "div[class*='_2tW1I0']",
                    # Generic price selectors
                    "span[class*='price']",
                    "div[class*='price']", 
                    "span[class*='rupee']",
                    "div[class*='rupee']",
                    "span[class*='amount']",
                    "div[class*='amount']",
                    "span[class*='cost']",
                    "div[class*='cost']",
                    # Look for any element with ₹ symbol
                    "span:contains('₹')",
                    "div:contains('₹')",
                    "p:contains('₹')"
                ]
                
                for selector in price_selectors:
                    try:
                        if ':contains(' in selector:
                            # Use XPath for contains
                            xpath_selector = f".//{selector.split(':')[0]}[contains(text(), '₹')]"
                            price_elem = parent_element.find_element(By.XPATH, xpath_selector)
                        else:
                            price_elem = parent_element.find_element(By.CSS_SELECTOR, selector)
                        
                        price_text = price_elem.text.strip()
                        if price_text and ('₹' in price_text or price_text.replace(',', '').replace('.', '').isdigit()):
                            if '₹' not in price_text:
                                price_text = f'₹{price_text}'
                            product_info['price'] = price_text
                            break
                    except:
                        continue
            except:
                pass
        
        # Also try to find price in the link element itself
        if not product_info['price']:
            try:
                # Look for price elements near the link
                link_parent = link_element.find_element(By.XPATH, './..')
                price_elements = link_parent.find_elements(By.CSS_SELECTOR, "span, div, p")
                
                for elem in price_elements:
                    text = elem.text.strip()
                    if text and ('₹' in text or text.replace(',', '').replace('.', '').isdigit()):
                        if '₹' not in text:
                            text = f'₹{text}'
                        product_info['price'] = text
                        break
            except:
                pass
        
        # Extract discount
        if parent_element:
            try:
                discount_selectors = [
                    "span[class*='discount']",
                    "div[class*='discount']",
                    "span[class*='off']",
                    "div[class*='off']",
                    "span[class*='save']",
                    "div[class*='save']",
                    "span[class*='deal']",
                    "div[class*='deal']",
                    "span[class*='_3Ay6Sb']",
                    "div[class*='_3Ay6Sb']"
                ]
                
                for selector in discount_selectors:
                    try:
                        discount_elem = parent_element.find_element(By.CSS_SELECTOR, selector)
                        discount_text = discount_elem.text.strip()
                        if discount_text and ('%' in discount_text or 'off' in discount_text.lower() or 'save' in discount_text.lower()):
                            product_info['discount'] = discount_text
                            break
                    except:
                        continue
            except:
                pass
        
        return product_info
    except Exception as e:
        logger.debug(f"Error extracting product info: {e}")
        return product_info

def is_valid_product(product_info):
    """Check if this is a valid product (not email, generic text, etc.)"""
    if not product_info or not product_info.get('title'):
        return False
    
    title = product_info['title'].lower()
    
    # Only filter out obvious non-products
    invalid_keywords = [
        'mailto:', 'email', '@', 'contact', 'support', 'help',
        'purchases.oni@flipkart.com'
    ]
    
    for keyword in invalid_keywords:
        if keyword in title:
            return False
    
    # Must have a reasonable title length
    if len(product_info['title']) < 5 or len(product_info['title']) > 200:
        return False
    
    return True

def extract_products_from_container(container, driver, max_items):
    """Extract products from a deal container"""
    products = []
    
    try:
        product_links = container.find_elements(By.CSS_SELECTOR, "a[href*='/p/']")
        
        for link in product_links[:max_items]:
            product_info = extract_product_info_improved(link, container)
            if product_info and is_valid_product(product_info):
                products.append(product_info)
        
        return products
    except Exception as e:
        logger.debug(f"Error extracting products from container: {e}")
        return []

def find_product_parent_section(link_element, driver):
    """Find the parent section for a product link"""
    try:
        # Try to find a parent div that looks like a section
        parent = link_element.find_element(By.XPATH, "./ancestor::div[contains(@class, '_') or contains(@class, 'css-') or contains(@class, 'card') or contains(@class, 'widget')][1]")
        return parent
    except:
        try:
            # Fallback to any div parent within 3 levels
            parent = link_element.find_element(By.XPATH, "./ancestor::div[3]")
            return parent
        except:
            return None

def find_parent_section(link_element, driver):
    """Find the parent section/container for a product link"""
    try:
        # Try to find a parent div that looks like a section
        parent = link_element.find_element(By.XPATH, "./ancestor::div[contains(@class, '_') or contains(@class, 'css-') or contains(@class, 'card') or contains(@class, 'widget')][1]")
        return parent
    except:
        try:
            # Fallback to any div parent within 3 levels
            parent = link_element.find_element(By.XPATH, "./ancestor::div[3]")
            return parent
        except:
            return None

def extract_section_title_from_parent(parent_element):
    """Extract section title from parent element"""
    try:
        # Look for headings in the parent
        title_selectors = ["h1", "h2", "h3", "h4", "h5", "h6", "span", "div"]
        
        for selector in title_selectors:
            try:
                title_elem = parent_element.find_element(By.CSS_SELECTOR, selector)
                title_text = title_elem.text.strip()
                if title_text and len(title_text) > 5 and len(title_text) < 100:
                    # Clean up the title
                    title_text = title_text.replace('\n', ' ').strip()
                    return title_text
            except:
                continue
        
        return None
    except:
        return None

def extract_item_info_from_link(link_element, driver):
    """Extract detailed item information from a product link"""
    item_info = {
        'title': '',
        'price': '',
        'discount': '',
        'image': '',
        'link': ''
    }
    
    try:
        # Extract link
        link = link_element.get_attribute('href') or ''
        if link:
            if link.startswith('/'):
                link = 'https://www.flipkart.com' + link
            item_info['link'] = link
        
        # Extract title from various sources
        # 1. Try aria-label
        title = link_element.get_attribute('aria-label') or ''
        
        # 2. Try image alt text
        if not title:
            try:
                img = link_element.find_element(By.TAG_NAME, 'img')
                title = img.get_attribute('alt') or ''
            except:
                pass
        
        # 3. Try text content
        if not title:
            title = link_element.text.strip()
        
        # 4. Try to find title in parent elements
        if not title:
            try:
                parent = link_element.find_element(By.XPATH, './..')
                title_elem = parent.find_element(By.CSS_SELECTOR, "span, div, p")
                title = title_elem.text.strip()
            except:
                pass
        
        # Clean up title
        if title:
            title = title.split('\n')[0].strip()  # Take first line
            title = title.split('(')[0].strip()    # Remove parentheses content
            if len(title) > 5 and len(title) < 200:
                item_info['title'] = title
        
        # Extract image
        try:
            img = link_element.find_element(By.TAG_NAME, 'img')
            img_src = img.get_attribute('src') or ''
            if img_src and ('flipkart' in img_src.lower() or 'img' in img_src.lower()):
                item_info['image'] = img_src
        except:
            pass
        
        # Extract price (look in parent section)
        try:
            parent = link_element.find_element(By.XPATH, './..')
            price_selectors = [
                "span[class*='price']",
                "div[class*='price']",
                "span[class*='rupee']",
                "div[class*='rupee']",
                "span[class*='amount']",
                "div[class*='amount']",
                "span[class*='cost']",
                "div[class*='cost']"
            ]
            
            for selector in price_selectors:
                try:
                    price_elem = parent.find_element(By.CSS_SELECTOR, selector)
                    price_text = price_elem.text.strip()
                    if price_text and ('₹' in price_text or price_text.replace(',', '').replace('.', '').isdigit()):
                        if '₹' not in price_text:
                            price_text = f'₹{price_text}'
                        item_info['price'] = price_text
                        break
                except:
                    continue
        except:
            pass
        
        # Extract discount
        try:
            parent = link_element.find_element(By.XPATH, './..')
            discount_selectors = [
                "span[class*='discount']",
                "div[class*='discount']",
                "span[class*='off']",
                "div[class*='off']",
                "span[class*='save']",
                "div[class*='save']",
                "span[class*='deal']",
                "div[class*='deal']"
            ]
            
            for selector in discount_selectors:
                try:
                    discount_elem = parent.find_element(By.CSS_SELECTOR, selector)
                    discount_text = discount_elem.text.strip()
                    if discount_text and ('%' in discount_text or 'off' in discount_text.lower() or 'save' in discount_text.lower()):
                        item_info['discount'] = discount_text
                        break
                except:
                    continue
        except:
            pass
        
        return item_info
    except Exception as e:
        logger.debug(f"Error extracting item info from link: {e}")
        return item_info

def extract_sections_from_headings_improved(driver, max_items=10):
    """Extract sections from headings with improved product detection"""
    sections = []
    
    try:
        # Get ALL headings (h1, h2, h3, h4)
        all_headings = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4")
        logger.info(f"   Found {len(all_headings)} total headings")
        
        for heading in all_headings:
            try:
                title = heading.text.strip()
                
                # Skip if invalid
                if not title or len(title) < 3 or len(title) > 150:
                    continue
                
                # Find parent container
                parent = None
                try:
                    parent = heading.find_element(By.XPATH, "./ancestor::div[contains(@class, '_') or contains(@class, 'css-')][1]")
                except:
                    try:
                        parent = heading.find_element(By.XPATH, "./ancestor::div[5]")
                    except:
                        continue
                
                if not parent:
                    continue
                
                # Extract items from this parent
                items = extract_section_items_improved(parent, driver, max_items)
                
                if items and len(items) > 0:
                    section_data = {
                        'section_title': title,
                        'item_count': len(items),
                        'items': items
                    }
                    sections.append(section_data)
            except:
                continue
        
        return sections
    except Exception as e:
        logger.error(f"Heading extraction error: {e}")
        return []

def extract_section_items_improved(section_element, driver, max_items=10):
    """Extract items from a section with improved detection"""
    items = []
    
    try:
        # Try to find product links within the section
        item_selectors = [
            "a[href*='/p/']",
            "a[href*='/product/']",
            "a[href*='/dp/']",
            "div[class*='product'] a",
            "div[class*='item'] a",
            "div[class*='card'] a",
            "div[class*='widget'] a",
            "li a",
            "div[class^='_'] a",
            "div[class*='css-'] a",
        ]
        
        seen_links = set()
        
        for selector in item_selectors:
            try:
                item_links = section_element.find_elements(By.CSS_SELECTOR, selector)
                
                for item_link in item_links:
                    try:
                        href = item_link.get_attribute('href') or ''
                        if href and href not in seen_links:
                            item_info = extract_item_info_from_link(item_link, driver)
                            if item_info and item_info.get('title') and len(item_info['title']) > 10:
                                items.append(item_info)
                                seen_links.add(href)
                                
                                if len(items) >= max_items:
                                    break
                    except:
                        continue
                
                if len(items) >= max_items:
                    break
            except:
                continue
        
        return items[:max_items]
    except Exception as e:
        logger.debug(f"Error extracting section items: {e}")
        return []

def extract_section_title(section_element):
    """Extract section title/heading from a container"""
    try:
        # Try multiple heading selectors
        title_selectors = [
            "h1", "h2", "h3", "h4", "h5", "h6",
            "div._1AtVbE h2",
            "div._2MlkI1 h2",
            "div._1YokD2 h2",
            "div._1HmYoV h2",
            "div._3e7xtJ h2",
            "div._2cLu-l h2",
            "div._1fQZEK h2",
            "div._3gijNv h2",
            "div._2d0qh9 h2",
            "div._3O0U0u h2",
            "div._2QfC02 h2",
            "div[class*='header'] h2",
            "div[class*='title'] span",
            "div[class*='title'] div",
            "div[class*='title'] p",
            "span[class*='headline']",
            "div._1AtVbE span",
            "div._2MlkI1 span",
            "div._1YokD2 span",
            "div._1HmYoV span",
            "div._3e7xtJ span",
            "div._2cLu-l span",
            "div._1fQZEK span",
            "div._3gijNv span",
            "div._2d0qh9 span",
            "div._3O0U0u span",
            "div._2QfC02 span",
            # Generic selectors
            "div[class*='title']",
            "div[class*='header']",
            "div[class*='heading']",
            "span[class*='title']",
            "span[class*='header']",
            "span[class*='heading']",
        ]
        
        for selector in title_selectors:
            try:
                title_elem = section_element.find_element(By.CSS_SELECTOR, selector)
                title_text = title_elem.text.strip()
                if title_text and len(title_text) > 2 and len(title_text) < 100:
                    # Clean up the title
                    title_text = title_text.replace('\n', ' ').strip()
                    return title_text
            except:
                continue
        
        return None
    except Exception as e:
        logger.debug(f"Error extracting section title: {e}")
        return None

def extract_section_items(section_element, driver, max_items=10):
    """Extract items from a section"""
    items = []
    
    try:
        # Try to find product cards within the section
        item_selectors = [
            # Current Flipkart selectors
            "div.q8WwEU a",
            "div._3zsGrb a", 
            "div._2-LWwB a",
            "div.css-175oi2r a",
            "div[class*='q8WwEU'] a",
            "div[class*='_3zsGrb'] a",
            "div[class*='_2-LWwB'] a",
            "div[class*='css-175oi2r'] a",
            # Legacy Flipkart selectors
            "div._1AtVbE a",
            "div._2MlkI1 a",
            "div._1YokD2 a",
            "div._1HmYoV a",
            "div._3e7xtJ a",
            "div._2cLu-l a",
            "div._1fQZEK a",
            "div._3gijNv a",
            "div._2d0qh9 a",
            "div._3O0U0u a",
            "div._2QfC02 a",
            # Generic selectors
            "li a",
            "div[class*='item'] a",
            "div[class*='product'] a",
            "div[class*='card'] a",
            "div[class*='widget'] a",
            "div[class*='section'] a",
            "div[class*='container'] a",
            "div[class*='grid'] a",
            "div[class*='row'] a",
            "div[class*='col'] a",
            # Direct product links
            "a[href*='/p/']",
            "a[href*='/product/']",
            "a[href*='/dp/']",
            # Any link within divs with underscore classes
            "div[class^='_'] a",
            "div[class*='css-'] a",
        ]
        
        for selector in item_selectors:
            try:
                item_links = section_element.find_elements(By.CSS_SELECTOR, selector)
                
                if item_links and len(item_links) > 0:
                    for item_link in item_links[:max_items]:
                        item_info = extract_item_info(item_link, section_element)
                        if item_info and item_info.get('title'):
                            items.append(item_info)
                    
                    if len(items) > 0:
                        break
            except:
                continue
        
        return items[:max_items]
    except Exception as e:
        logger.debug(f"Error extracting section items: {e}")
        return []

def extract_item_info(item_element, section_element):
    """Extract information from a single item"""
    item_info = {
        'title': '',
        'price': '',
        'discount': '',
        'image': '',
        'link': ''
    }
    
    try:
        # Extract link
        link = item_element.get_attribute('href') or ''
        if link:
            if link.startswith('/'):
                link = 'https://www.flipkart.com' + link
            item_info['link'] = link
        
        # Extract title from various sources
        # 1. Try aria-label
        title = item_element.get_attribute('aria-label') or ''
        
        # 2. Try image alt text
        if not title:
            try:
                img = item_element.find_element(By.TAG_NAME, 'img')
                title = img.get_attribute('alt') or ''
            except:
                pass
        
        # 3. Try text content
        if not title:
            title = item_element.text.strip()
        
        # Clean up title
        if title:
            title = title.split('\n')[0].strip()  # Take first line
            title = title.split('(')[0].strip()    # Remove parentheses content
            if len(title) > 10 and len(title) < 200:
                item_info['title'] = title
        
        # Extract image
        try:
            img = item_element.find_element(By.TAG_NAME, 'img')
            img_src = img.get_attribute('src') or ''
            if img_src and 'flipkart' in img_src.lower():
                item_info['image'] = img_src
        except:
            pass
        
        # Extract price (look in parent section)
        try:
            # Try to find price near the link
            parent = item_element.find_element(By.XPATH, './..')
            price_elem = parent.find_element(By.CSS_SELECTOR, "div[class*='price'], div._30jeq3, div._1vC4OE")
            price_text = price_elem.text.strip()
            if price_text and ('₹' in price_text or price_text.replace(',', '').isdigit()):
                if '₹' not in price_text:
                    price_text = f'₹{price_text}'
                item_info['price'] = price_text
        except:
            pass
        
        # Extract discount
        try:
            parent = item_element.find_element(By.XPATH, './..')
            discount_elem = parent.find_element(By.CSS_SELECTOR, "div[class*='badge'], div[class*='discount'], div._3Ay6Sb")
            discount_text = discount_elem.text.strip()
            if discount_text and ('%' in discount_text or 'off' in discount_text.lower()):
                item_info['discount'] = discount_text
        except:
            pass
        
        return item_info
    except Exception as e:
        logger.debug(f"Error extracting item info: {e}")
        return item_info

def extract_sections_from_all_headings(driver, max_items=10, processed_titles=set()):
    """Extract sections from ALL headings on page"""
    sections = []
    
    try:
        # Get ALL headings (h1, h2, h3, h4)
        all_headings = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4")
        logger.info(f"   Found {len(all_headings)} total headings")
        
        for heading in all_headings:
            try:
                title = heading.text.strip()
                
                # Skip if invalid or already processed
                if not title or len(title) < 3 or len(title) > 150 or title in processed_titles:
                    continue
                
                # Find parent container (try multiple levels)
                parent = None
                try:
                    # Try to find a card/widget parent
                    parent = heading.find_element(By.XPATH, "./ancestor::div[contains(@class, '_1AtVbE') or contains(@class, '_2MlkI1') or contains(@data-testid, '')]")
                except:
                    try:
                        # Fallback to any div parent within 5 levels
                        parent = heading.find_element(By.XPATH, "./ancestor::div[5]")
                    except:
                        continue
                
                if not parent:
                    continue
                
                # Extract items from this parent
                items = extract_section_items(parent, driver, max_items)
                
                if items and len(items) > 0:
                    section_data = {
                        'section_title': title,
                        'item_count': len(items),
                        'items': items
                    }
                    sections.append(section_data)
            except:
                continue
        
        return sections
    except Exception as e:
        logger.error(f"Heading extraction error: {e}")
        return []

def extract_remaining_products(driver, processed_titles, max_items=20):
    """Capture any products not yet categorized into sections"""
    try:
        # Find all links with images that look like products
        all_product_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/p/'], a[href*='/product/']")
        logger.info(f"   Found {len(all_product_links)} potential product links")
        
        remaining_items = []
        seen_links = set()
        
        for link in all_product_links[:max_items * 2]:  # Check more to filter
            try:
                href = link.get_attribute('href') or ''
                
                # Skip if already seen or invalid
                if not href or href in seen_links:
                    continue
                
                # Try to find an image within the link
                try:
                    img = link.find_element(By.TAG_NAME, 'img')
                except:
                    continue
                
                # Extract item info
                item_info = extract_item_info(link, link)
                
                if item_info and item_info.get('title') and len(item_info['title']) > 10:
                    remaining_items.append(item_info)
                    seen_links.add(href)
                    
                    if len(remaining_items) >= max_items:
                        break
            except:
                continue
        
        if remaining_items:
            return {
                'section_title': 'More Products',
                'item_count': len(remaining_items),
                'items': remaining_items
            }
        
        return None
    except Exception as e:
        logger.error(f"Remaining products extraction error: {e}")
        return None

if __name__ == "__main__":
    import sys
    
    headless = '--headless' in sys.argv or '-h' in sys.argv
    max_items = 10
    
    # Check for max items argument
    for arg in sys.argv:
        if arg.startswith('--max='):
            try:
                max_items = int(arg.split('=')[1])
            except:
                pass
    
    print(f"\n{'='*60}")
    print(f"🛒 FLIPKART HOMEPAGE - COMPLETE PAGE SCRAPER")
    print(f"{'='*60}")
    print(f"Mode: {'Headless' if headless else 'Visible Browser'}")
    print(f"Max Items Per Section: {max_items}")
    print(f"Strategy: Scroll entire page + Multi-level extraction")
    print(f"{'='*60}\n")
    
    result = scrape_flipkart_homepage_deals(headless=headless, max_items_per_section=max_items)
    
    print(f"\n{'='*60}")
    print(f"✅ SCRAPING COMPLETE")
    print(f"{'='*60}")
    print(f"Total Sections: {result.get('total_sections', 0)}")
    print(f"Total Items: {result.get('total_items', 0)}")
    
    if result.get('sections'):
        print(f"\n📊 Sections Found:")
        for i, section in enumerate(result['sections'][:5], 1):
            print(f"   {i}. {section['section_title']} ({section['item_count']} items)")
        if len(result['sections']) > 5:
            print(f"   ... and {len(result['sections']) - 5} more sections")
    
    print(f"\n💾 Saved to: flipkart_homepage_deals.json")
    print(f"{'='*60}\n")

def extract_product_info_with_price(link_element, parent_element):
    """Extract product information with enhanced price detection"""
    product_info = {
        'title': '',
        'price': '',
        'discount': '',
        'image': '',
        'link': ''
    }
    
    try:
        # Extract link
        product_info['link'] = link_element.get_attribute('href') or ''
        
        # Extract title - try multiple methods
        title_selectors = [
            # Aria label
            "aria-label",
            # Image alt text
            "img[alt]",
            # Text content
            "span", "div", "p", "h1", "h2", "h3", "h4", "h5", "h6"
        ]
        
        title_found = False
        for selector in title_selectors:
            try:
                if selector == "aria-label":
                    title = link_element.get_attribute('aria-label')
                    if title and len(title) > 5:
                        product_info['title'] = title.strip()
                        title_found = True
                        break
                elif selector.startswith("img"):
                    img_elem = link_element.find_element(By.CSS_SELECTOR, selector)
                    title = img_elem.get_attribute('alt')
                    if title and len(title) > 5:
                        product_info['title'] = title.strip()
                        title_found = True
                        break
                else:
                    text_elem = link_element.find_element(By.CSS_SELECTOR, selector)
                    title = text_elem.text.strip()
                    if title and len(title) > 5:
                        product_info['title'] = title
                        title_found = True
                        break
            except:
                continue
        
        # If no title found in link, try parent element
        if not title_found and parent_element:
            try:
                # Look for text in parent
                parent_text = parent_element.text.strip()
                if parent_text and len(parent_text) > 5:
                    # Take first line or first 50 chars
                    lines = parent_text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and len(line) > 5 and len(line) < 100:
                            product_info['title'] = line
                            break
            except:
                pass
        
        # Extract image
        try:
            img_elem = link_element.find_element(By.CSS_SELECTOR, "img")
            product_info['image'] = img_elem.get_attribute('src') or ''
        except:
            pass
        
        # Enhanced price extraction - look in parent element first
        if parent_element:
            try:
                # Get all text elements in parent
                all_elements = parent_element.find_elements(By.CSS_SELECTOR, "*")
                price_candidates = []
                
                for elem in all_elements:
                    try:
                        text = elem.text.strip()
                        if text and ('₹' in text or 'Rs' in text or 'INR' in text):
                            # Check if it looks like a price
                            clean_text = text.replace('₹', '').replace('Rs', '').replace('INR', '').replace(',', '').replace('*', '').strip()
                            if clean_text and clean_text.replace('.', '').isdigit():
                                price_candidates.append(text)
                    except:
                        continue
                
                # Take the first valid price
                if price_candidates:
                    product_info['price'] = price_candidates[0]
                
                # Also try specific selectors
                if not product_info['price']:
                    price_selectors = [
                        "span[class*='_30jeq3']", "div[class*='_30jeq3']", # Flipkart specific
                        "span[class*='_1vC4OE']", "div[class*='_1vC4OE']", # Flipkart specific
                        "span[class*='_25b18c']", "div[class*='_25b18c']", # Flipkart specific
                        "span[class*='_3tbKJd']", "div[class*='_3tbKJd']", # Flipkart specific
                        "span[class*='_2tW1I0']", "div[class*='_2tW1I0']", # Flipkart specific
                        "span[class*='price']", "div[class*='price']", # Generic
                        "span[class*='amount']", "div[class*='amount']", # Generic
                        "span[class*='cost']", "div[class*='cost']" # Generic
                    ]
                    
                    for selector in price_selectors:
                        try:
                            price_elem = parent_element.find_element(By.CSS_SELECTOR, selector)
                            price_text = price_elem.text.strip()
                            if price_text and ('₹' in price_text or price_text.replace(',', '').replace('.', '').isdigit()):
                                product_info['price'] = price_text
                                break
                        except:
                            continue
            except:
                pass
        
        # Also try to find price in the link element itself
        if not product_info['price']:
            try:
                # Look for price elements near the link
                link_text = link_element.text.strip()
                if link_text and ('₹' in link_text or link_text.replace(',', '').replace('.', '').isdigit()):
                    product_info['price'] = link_text
            except:
                pass
        
        # Extract discount
        if parent_element:
            try:
                discount_selectors = [
                    "span[class*='_3Ay6Sb']", "div[class*='_3Ay6Sb']", # Flipkart specific
                    "span[class*='discount']", "div[class*='discount']", # Generic
                    "span[class*='off']", "div[class*='off']", # Generic
                    "span[class*='save']", "div[class*='save']" # Generic
                ]
                
                for selector in discount_selectors:
                    try:
                        discount_elem = parent_element.find_element(By.CSS_SELECTOR, selector)
                        discount_text = discount_elem.text.strip()
                        if discount_text and ('%' in discount_text or 'off' in discount_text.lower() or 'save' in discount_text.lower()):
                            product_info['discount'] = discount_text
                            break
                    except:
                        continue
            except:
                pass
        
        return product_info
        
    except Exception as e:
        logger.debug(f"Error extracting product info: {e}")
        return product_info

def extract_products_from_deal_container(container, driver, max_items):
    """Extract products from a deal container"""
    products = []
    try:
        # Look for product links in this container
        product_links = container.find_elements(By.CSS_SELECTOR, "a[href*='/p/']")
        
        for link in product_links[:max_items]:
            product_info = extract_product_info_with_price(link, container)
            if product_info and is_valid_product(product_info):
                products.append(product_info)
                
    except Exception as e:
        logger.debug(f"Error extracting from deal container: {e}")
    
    return products

def extract_section_title_from_parent(parent_element):
    """Extract section title from parent element"""
    if not parent_element:
        return "Products"
    
    try:
        # Look for headings
        heading_selectors = ["h1", "h2", "h3", "h4", "h5", "h6", "span", "div"]
        
        for selector in heading_selectors:
            try:
                headings = parent_element.find_elements(By.CSS_SELECTOR, selector)
                for heading in headings:
                    text = heading.text.strip()
                    if text and len(text) > 3 and len(text) < 100:
                        # Skip if it looks like a price
                        if '₹' not in text and not text.replace(',', '').replace('.', '').isdigit():
                            return text
            except:
                continue
        
        return "Featured Products"
    except:
        return "Featured Products"

def extract_product_info_from_container(link_element, container):
    """Extract product information from a container with enhanced price detection"""
    product_info = {
        'title': '',
        'price': '',
        'discount': '',
        'image': '',
        'link': ''
    }
    
    try:
        # Extract link
        product_info['link'] = link_element.get_attribute('href') or ''
        
        # Extract title from URL first (most reliable)
        if product_info['link']:
            product_info['title'] = extract_title_from_url(product_info['link'])
        
        # If no title from URL, try other methods
        if not product_info['title']:
            title_selectors = [
                # Aria label
                "aria-label",
                # Image alt text
                "img[alt]",
                # Text content
                "span", "div", "p", "h1", "h2", "h3", "h4", "h5", "h6"
            ]
            
            for selector in title_selectors:
                try:
                    if selector == "aria-label":
                        title = link_element.get_attribute('aria-label')
                        if title and len(title) > 5:
                            product_info['title'] = title.strip()
                            break
                    elif selector.startswith("img"):
                        img_elem = link_element.find_element(By.CSS_SELECTOR, selector)
                        title = img_elem.get_attribute('alt')
                        if title and len(title) > 5:
                            product_info['title'] = title.strip()
                            break
                    else:
                        text_elem = link_element.find_element(By.CSS_SELECTOR, selector)
                        title = text_elem.text.strip()
                        if title and len(title) > 5:
                            product_info['title'] = title
                            break
                except:
                    continue
        
        # Extract image
        try:
            img_elem = link_element.find_element(By.CSS_SELECTOR, "img")
            product_info['image'] = img_elem.get_attribute('src') or ''
        except:
            pass
        
        # Enhanced price extraction - look in container
        if container:
            try:
                # Get all text elements in container
                all_elements = container.find_elements(By.CSS_SELECTOR, "*")
                price_candidates = []
                
                for elem in all_elements:
                    try:
                        text = elem.text.strip()
                        if text and ('₹' in text or 'Rs' in text or 'INR' in text):
                            # Check if it looks like a price
                            import re
                            numbers = re.findall(r'[\d,]+', text)
                            if numbers and any(len(num.replace(',', '')) >= 3 for num in numbers):
                                price_candidates.append(text)
                    except:
                        continue
                
                # Take the first valid price
                if price_candidates:
                    product_info['price'] = price_candidates[0]
                
                # Also try specific selectors
                if not product_info['price']:
                    price_selectors = [
                        "span[class*='_30jeq3']", "div[class*='_30jeq3']", # Flipkart specific
                        "span[class*='_1vC4OE']", "div[class*='_1vC4OE']", # Flipkart specific
                        "span[class*='_25b18c']", "div[class*='_25b18c']", # Flipkart specific
                        "span[class*='_3tbKJd']", "div[class*='_3tbKJd']", # Flipkart specific
                        "span[class*='_2tW1I0']", "div[class*='_2tW1I0']", # Flipkart specific
                        "span[class*='price']", "div[class*='price']", # Generic
                        "span[class*='amount']", "div[class*='amount']", # Generic
                        "span[class*='cost']", "div[class*='cost']" # Generic
                    ]
                    
                    for selector in price_selectors:
                        try:
                            price_elem = container.find_element(By.CSS_SELECTOR, selector)
                            price_text = price_elem.text.strip()
                            if price_text and ('₹' in price_text or price_text.replace(',', '').replace('.', '').isdigit()):
                                product_info['price'] = price_text
                                break
                        except:
                            continue
            except:
                pass
        
        # Also try to find price in the link element itself
        if not product_info['price']:
            try:
                # Look for price elements near the link
                link_text = link_element.text.strip()
                if link_text and ('₹' in link_text or link_text.replace(',', '').replace('.', '').isdigit()):
                    product_info['price'] = link_text
            except:
                pass
        
        # Extract discount
        if container:
            try:
                discount_selectors = [
                    "span[class*='_3Ay6Sb']", "div[class*='_3Ay6Sb']", # Flipkart specific
                    "span[class*='discount']", "div[class*='discount']", # Generic
                    "span[class*='off']", "div[class*='off']", # Generic
                    "span[class*='save']", "div[class*='save']" # Generic
                ]
                
                for selector in discount_selectors:
                    try:
                        discount_elem = container.find_element(By.CSS_SELECTOR, selector)
                        discount_text = discount_elem.text.strip()
                        if discount_text and ('%' in discount_text or 'off' in discount_text.lower() or 'save' in discount_text.lower()):
                            product_info['discount'] = discount_text
                            break
                    except:
                        continue
            except:
                pass
        
        return product_info
        
    except Exception as e:
        logger.debug(f"Error extracting product info: {e}")
        return product_info

def extract_title_from_url(url):
    """Extract product title from Flipkart URL"""
    try:
        if not url or '/p/' not in url:
            return ''
        
        # Extract the product part from URL
        # Example: https://www.flipkart.com/samsung-galaxy-f36-5g-black-128-gb/p/itm...
        parts = url.split('/p/')[0].split('/')
        
        # Get the last part which should be the product name
        product_part = parts[-1] if parts else ''
        
        if product_part:
            # Replace hyphens with spaces and clean up
            title = product_part.replace('-', ' ').replace('_', ' ')
            
            # Capitalize words
            title = ' '.join(word.capitalize() for word in title.split())
            
            # Clean up common patterns
            title = title.replace('Gb', 'GB').replace('Mb', 'MB')
            
            return title
        
        return ''
    except Exception as e:
        logger.debug(f"Error extracting title from URL: {e}")
        return ''
