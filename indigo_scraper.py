#!/usr/bin/env python3
"""
IndiGo Flights Scraper - Works with REAL IndiGo website
Based on actual goindigo.in structure
"""

import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_driver(headless=True):
    """Create Chrome WebDriver"""
    options = Options()
    
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
    else:
        options.add_argument("--start-maximized")
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        logger.info("IndiGo scraper initialized")
    except Exception as e:
        logger.error(f"ChromeDriverManager failed: {e}")
        driver = webdriver.Chrome(options=options)
        logger.info("Using system ChromeDriver")
    
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def scrape_indigo_flights(origin, destination, date, headless=True):
    """
    Scrape IndiGo flights using direct URL
    Works with real IndiGo website
    """
    driver = create_driver(headless=headless)
    all_flights = []
    
    try:
        # Direct URL to IndiGo flight search
        # Format: https://www.goindigo.in/booking/flight-select.html?dep=IXM&arr=BOM&date=2025-10-15&pax=1
        url = f"https://www.goindigo.in/booking/flight-select.html?dep={origin}&arr={destination}&date={date}&pax=1&class=E"
        
        logger.info(f"Visiting IndiGo: {origin} -> {destination} on {date}")
        driver.get(url)
        
        # Wait for page to load
        time.sleep(10)  # IndiGo needs time to load flights
        
        # Save HTML for debugging
        with open('indigo_flights.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        logger.info("Saved IndiGo HTML")
        
        # Scroll to load all flights
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Try multiple selectors for flight cards
        flight_selectors = [
            "div[class*='flight-card']",
            "div[class*='flightCard']",
            "div[class*='Flight']",
            "li[class*='flight']",
            "div[class*='result']",
        ]
        
        flight_elements = []
        for selector in flight_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                logger.info(f"Found {len(elements)} flights with selector: {selector}")
                flight_elements = elements
                break
        
        # If specific selectors don't work, search in ALL divs for flight data
        if not flight_elements:
            logger.info("Using aggressive search method...")
            all_elements = driver.find_elements(By.CSS_SELECTOR, "div, li")
            
            # Filter elements that likely contain flight info
            for elem in all_elements:
                try:
                    text = elem.text
                    # Check if element contains flight-like data (times, prices)
                    if text and re.search(r'\d{2}:\d{2}', text) and ('₹' in text or 'INR' in text):
                        flight_elements.append(elem)
                except:
                    continue
            
            logger.info(f"Found {len(flight_elements)} potential flight elements")
        
        # Extract flight data
        for idx, elem in enumerate(flight_elements[:50], 1):
            try:
                elem_text = elem.text
                
                if not elem_text or len(elem_text) < 20:
                    continue
                
                flight_info = {
                    "airline": "IndiGo",
                    "price": "",
                    "departure_time": "",
                    "arrival_time": "",
                    "duration": "",
                    "stops": "",
                    "flight_number": "",
                    "origin": origin,
                    "destination": destination,
                    "departure_date": date
                }
                
                # Extract times (format: 04:20, 06:55, etc.)
                times = re.findall(r'\d{2}:\d{2}', elem_text)
                if len(times) >= 2:
                    flight_info['departure_time'] = times[0]
                    flight_info['arrival_time'] = times[1]
                
                # Extract price (₹7,733, ₹17,407, etc.)
                price_match = re.search(r'₹[\d,]+', elem_text)
                if price_match:
                    flight_info['price'] = price_match.group(0)
                
                # Extract duration (02h 35m, 2h 30m, etc.)
                duration_match = re.search(r'\d+h\s*\d*m?', elem_text, re.IGNORECASE)
                if duration_match:
                    flight_info['duration'] = duration_match.group(0)
                
                # Extract stops
                if 'non-stop' in elem_text.lower() or 'nonstop' in elem_text.lower():
                    flight_info['stops'] = 'Non-stop'
                elif '1 stop' in elem_text.lower():
                    flight_info['stops'] = '1 stop'
                elif '2 stop' in elem_text.lower():
                    flight_info['stops'] = '2 stops'
                
                # Extract flight number (6E 2561, 6E format)
                flight_num_match = re.search(r'6E\s*\d{3,4}', elem_text)
                if flight_num_match:
                    flight_info['flight_number'] = flight_num_match.group(0)
                
                # Only add if we have essential data
                if flight_info['price'] and (flight_info['departure_time'] or flight_info['arrival_time']):
                    all_flights.append(flight_info)
                    logger.info(f"  {idx}. IndiGo {flight_info['flight_number']}: {flight_info['price']} ({flight_info['departure_time']} - {flight_info['arrival_time']}) {flight_info['stops']}")
                
            except Exception as e:
                logger.debug(f"Error processing element {idx}: {e}")
                continue
        
        logger.info(f"Total flights extracted: {len(all_flights)}")
        
        return {
            'timestamp': datetime.now().isoformat(),
            'origin': origin,
            'destination': destination,
            'departure_date': date,
            'airline': 'IndiGo',
            'total_flights': len(all_flights),
            'flights': all_flights
        }
        
    except Exception as e:
        logger.error(f"Error scraping IndiGo: {e}")
        return {
            'timestamp': datetime.now().isoformat(),
            'origin': origin,
            'destination': destination,
            'departure_date': date,
            'airline': 'IndiGo',
            'total_flights': 0,
            'flights': [],
            'error': str(e)
        }
    finally:
        driver.quit()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python indigo_scraper.py ORIGIN DEST YYYY-MM-DD")
        print("Example: python indigo_scraper.py IXM BOM 2025-10-15")
        print("\nMadurai Airport Code: IXM")
        sys.exit(1)
    
    origin = sys.argv[1].upper()
    dest = sys.argv[2].upper()
    date = sys.argv[3]
    
    print(f"\n{'='*60}")
    print(f"INDIGO FLIGHTS SCRAPER")
    print(f"{'='*60}")
    print(f"From: {origin}")
    print(f"To: {dest}")
    print(f"Date: {date}")
    print(f"{'='*60}\n")
    
    # Run with visible browser for testing
    result = scrape_indigo_flights(origin, dest, date, headless=False)
    
    print(f"\n{'='*60}")
    print(f"SCRAPING COMPLETE")
    print(f"{'='*60}")
    print(f"Total Flights: {result['total_flights']}")
    
    if result['flights']:
        print(f"\nFlights Found:")
        for i, flight in enumerate(result['flights'], 1):
            print(f"  {i}. {flight['flight_number'] or 'IndiGo'}: {flight['price']} ({flight['departure_time']} - {flight['arrival_time']}) {flight['stops']}")
        
        # Save to JSON
        with open('indigo_flights.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nSaved to: indigo_flights.json")
    else:
        print("No flights found")
        if 'error' in result:
            print(f"Error: {result['error']}")
    
    print(f"{'='*60}\n")

