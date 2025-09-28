#!/usr/bin/env python3
"""Debug Amazon title extraction in detail"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

def debug_amazon_titles_detailed():
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
            
            # Get all spans and check their text content
            all_spans = first_card.find_elements(By.TAG_NAME, 'span')
            print(f'Total spans in card: {len(all_spans)}')
            
            for i, span in enumerate(all_spans):
                text = span.text.strip()
                classes = span.get_attribute('class') or ''
                if text and len(text) > 10:
                    print(f'Span {i}: class="{classes}" text="{text[:80]}..."')
                    if 'ASIAN' in text and 'MEXICO' in text:
                        print(f'*** FOUND TITLE SPAN {i} ***')
                        print(f'Full text: {text}')
                        print(f'Classes: {classes}')
                        break
                    
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_amazon_titles_detailed()
