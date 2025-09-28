#!/usr/bin/env python3
"""
Debug script for Amazon link extraction
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

def create_driver():
    """Create a Chrome WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--enable-unsafe-swiftshader")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✅ WebDriver initialized with ChromeDriverManager")
    except Exception as e:
        print(f"⚠️ ChromeDriverManager failed: {e}")
        try:
            driver = webdriver.Chrome(options=chrome_options)
            print("✅ WebDriver initialized with system ChromeDriver")
        except Exception as e2:
            print(f"❌ All ChromeDriver methods failed: {e2}")
            raise e2
    
    return driver

def debug_amazon_links():
    """Debug Amazon link extraction"""
    driver = create_driver()
    try:
        print("🔍 Navigating to Amazon...")
        driver.get("https://www.amazon.in")
        wait = WebDriverWait(driver, 10)

        # Search input
        print("🔍 Finding search input...")
        search_input = wait.until(EC.presence_of_element_located((By.ID, "twotabsearchtextbox")))
        search_input.clear()
        search_input.send_keys("iphone")
        search_input.send_keys(Keys.ENTER)

        # Wait for search results to load
        print("⏳ Waiting for search results...")
        time.sleep(5)
        
        # Get first product card
        product_cards = driver.find_elements(By.CSS_SELECTOR, "div[data-component-type='s-search-result']")
        if not product_cards:
            print("❌ No product cards found!")
            return
        
        card = product_cards[0]
        print(f"✅ Found product card")
        
        # Extract all links and their text
        link_selectors = [
            "a[href*='/dp/']",
            "a[href*='/gp/product/']",
            "span[data-component-type='s-product-image'] a",
            "div[data-component-type='s-product-image'] a",
            "a[data-component-type='s-product-image']"
        ]
        
        print(f"\n🔍 Extracting all links and text...")
        all_links = []
        
        for selector in link_selectors:
            try:
                link_elems = card.find_elements(By.CSS_SELECTOR, selector)
                print(f"Selector '{selector}' found {len(link_elems)} elements")
                for i, link_elem in enumerate(link_elems):
                    link = link_elem.get_attribute('href') or ''
                    text = link_elem.text.strip()
                    all_links.append((link, text))
                    print(f"  Link {i+1}: {link[:80]}...")
                    print(f"  Text {i+1}: '{text}'")
                    print(f"  Text length: {len(text)}")
                    print(f"  Text starts with ₹: {text.startswith('₹')}")
                    print(f"  Text starts with Rs: {text.startswith('Rs')}")
                    print(f"  Text ends with %: {text.endswith('%')}")
                    print(f"  Text contains 'off': {'off' in text.lower()}")
                    print(f"  Text contains 'delivery': {'delivery' in text.lower()}")
                    print(f"  Text contains 'reviews': {'reviews' in text.lower()}")
                    print(f"  Text contains 'rating': {'rating' in text.lower()}")
                    print(f"  Text contains 'M.R.P:': {'M.R.P:' in text}")
                    print(f"  Text starts with 'Best seller': {text.startswith('Best seller')}")
                    print(f"  Text starts with '5,109': {text.startswith('5,109')}")
                    print(f"  Text starts with '₹47,999': {text.startswith('₹47,999')}")
                    print(f"  Would be selected: {text and len(text) > 10 and len(text) < 200 and not text.startswith('₹') and not text.startswith('Rs') and not text.endswith('%') and 'off' not in text.lower() and 'delivery' not in text.lower() and 'reviews' not in text.lower() and 'rating' not in text.lower() and 'M.R.P:' not in text and not text.startswith('Best seller') and not text.startswith('5,109') and not text.startswith('₹47,999')}")
                    print("  ---")
            except Exception as e:
                print(f"❌ Selector '{selector}' failed: {e}")
        
        # Find the best candidate
        print(f"\n🎯 Finding best title candidate...")
        best_title = ""
        best_link = ""
        
        for link, text in all_links:
            if link and ('/dp/' in link or '/gp/product/' in link):
                if not best_link:
                    best_link = link
                
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
                    best_title = text
                    print(f"✅ Selected title: '{best_title}'")
                    print(f"✅ Selected link: {best_link[:80]}...")
                    break
        
        if not best_title:
            print("❌ No suitable title found!")
            print("Available text options:")
            for i, (link, text) in enumerate(all_links):
                if link and ('/dp/' in link or '/gp/product/' in link):
                    print(f"  {i+1}. '{text}' (length: {len(text)})")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_amazon_links()




