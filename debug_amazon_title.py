#!/usr/bin/env python3
"""Debug Amazon title extraction"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

def debug_amazon_titles():
    options = Options()
    options.add_argument('--headless=new')
    driver = webdriver.Chrome(options=options)

    try:
        driver.get('https://www.amazon.in/s?k=shoes&ref=nb_sb_noss')
        time.sleep(3)
        
        # Find first product card
        cards = driver.find_elements(By.CSS_SELECTOR, 'div[data-component-type="s-search-result"]')
        if cards:
            first_card = cards[0]
            print('First card found')
            
            # Try different title selectors
            selectors = [
                'span.a-size-base-plus',
                'span.a-color-base', 
                'h2.a-size-mini a span',
                'h2.a-size-mini a',
                'a span.a-size-base-plus',
                'a span.a-color-base',
                'span.a-size-medium',
                'span.a-text-normal',
                'div[data-cy="title-recipe-title"] span',
                'span[data-automation-id="product-title"]'
            ]
            
            for selector in selectors:
                try:
                    elements = first_card.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        for i, elem in enumerate(elements[:3]):
                            text = elem.text.strip()
                            if text and len(text) > 10:
                                print(f'Selector {selector}: Found text: {text[:100]}...')
                                break
                    else:
                        print(f'Selector {selector}: No elements found')
                except Exception as e:
                    print(f'Selector {selector}: Error - {e}')
            
            # Try to find any span with meaningful text
            all_spans = first_card.find_elements(By.TAG_NAME, 'span')
            print(f'Total spans in card: {len(all_spans)}')
            for i, span in enumerate(all_spans[:10]):
                text = span.text.strip()
                if text and len(text) > 20 and 'shoes' in text.lower():
                    print(f'Span {i}: {text[:100]}...')
                    
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_amazon_titles()
