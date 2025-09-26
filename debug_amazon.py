#!/usr/bin/env python3
"""
Debug script for Amazon scraper
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

def debug_amazon_search():
    """Debug Amazon search"""
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
        
        print(f"📍 Current URL: {driver.current_url}")
        print(f"📄 Page title: {driver.title}")
        
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
                print(f"🔍 Selector '{selector}' found {len(cards)} cards")
                if cards:
                    product_cards = cards
                    break
            except Exception as e:
                print(f"❌ Selector '{selector}' failed: {e}")
                continue
        
        if not product_cards:
            print("❌ No product cards found!")
            return
        
        print(f"✅ Found {len(product_cards)} product cards")
        
        # Debug first card
        card = product_cards[0]
        print(f"\n🔍 Debugging first card...")
        print(f"Card HTML (first 500 chars): {card.get_attribute('outerHTML')[:500]}...")
        
        # Try to find links
        link_selectors = [
            "a[href*='/dp/']",
            "a[href*='/gp/product/']",
            "h2 a",
            "div[data-component-type='s-product-image'] a",
            "span[data-component-type='s-product-image'] a",
            "a[data-component-type='s-product-image']"
        ]
        
        print(f"\n🔍 Looking for links...")
        for selector in link_selectors:
            try:
                link_elems = card.find_elements(By.CSS_SELECTOR, selector)
                print(f"Selector '{selector}' found {len(link_elems)} elements")
                for i, link_elem in enumerate(link_elems):
                    link = link_elem.get_attribute('href') or ''
                    text = link_elem.text.strip()
                    print(f"  Link {i+1}: {link[:100]}... (text: {text[:50]}...)")
            except Exception as e:
                print(f"❌ Selector '{selector}' failed: {e}")
        
        # Try to find titles
        title_selectors = [
            "h2.a-size-mini a span",
            "h2.a-size-mini a",
            "h2 a span",
            "h2 a",
            "a[data-automation-id='product-title']",
            "span[data-automation-id='product-title']"
        ]
        
        print(f"\n🔍 Looking for titles...")
        for selector in title_selectors:
            try:
                title_elems = card.find_elements(By.CSS_SELECTOR, selector)
                print(f"Selector '{selector}' found {len(title_elems)} elements")
                for i, title_elem in enumerate(title_elems):
                    text = title_elem.text.strip()
                    link = title_elem.get_attribute('href') or ''
                    print(f"  Title {i+1}: {text[:100]}... (link: {link[:100]}...)")
            except Exception as e:
                print(f"❌ Selector '{selector}' failed: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_amazon_search()




