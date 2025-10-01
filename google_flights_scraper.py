#!/usr/bin/env python3
"""
Google Flights Scraper - Shows ALL Airlines
Much more reliable than scraping individual airline websites
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_driver(headless=True):
    """Create Chrome WebDriver"""
    options = Options()
    
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        logger.info("Google Flights scraper initialized")
    except Exception as e:
        logger.error(f"ChromeDriverManager failed: {e}")
        driver = webdriver.Chrome(options=options)
        logger.info("Using system ChromeDriver")
    
    # Remove webdriver detection
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def scrape_google_flights(origin, destination, date, headless=True):
    """
    Scrape Google Flights for all airlines
    More reliable than individual airline websites
    """
    driver = create_driver(headless=headless)
    all_flights = []
    
    try:
        # Build Google Flights URL
        # Format: https://www.google.com/travel/flights?q=Flights%20from%20IXM%20to%20BOM%20on%202025-10-15
        url = f"https://www.google.com/travel/flights?q=Flights from {origin} to {destination} on {date}"
        
        logger.info(f"Visiting Google Flights...")
        logger.info(f"Route: {origin} -> {destination} on {date}")
        driver.get(url)
        
        # Wait for page to load
        time.sleep(5)
        
        # Wait for flight results
        try:
            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.pIav2d, div.pIav2d, div[jsname='YdtKid']")))
            logger.info("Flight results loaded")
        except:
            logger.warning("Timeout waiting for results")
        
        # Additional wait for content to fully load
        time.sleep(3)
        
        # Save HTML for debugging
        html_content = driver.page_source
        with open('google_flights.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info("Saved Google Flights HTML for debugging")
        
        # Try multiple selectors for flight cards
        flight_selectors = [
            "li.pIav2d",  # Google Flights flight list item
            "div.pIav2d",
            "div[jsname='YdtKid']",
            "div[class*='flight']",
            "li[class*='flight']",
        ]
        
        flight_elements = []
        for selector in flight_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    logger.info(f"Found {len(elements)} elements with selector: {selector}")
                    flight_elements = elements
                    break
            except:
                continue
        
        if not flight_elements:
            logger.warning("No flight elements found with any selector")
            # Try to find ANY elements that might contain flight info
            all_divs = driver.find_elements(By.TAG_NAME, "div")
            logger.info(f"Total divs on page: {len(all_divs)}")
            
            # Look for divs with rupee symbol (likely prices)
            price_divs = []
            for div in all_divs:
                try:
                    text = div.text
                    if text and ('₹' in text or 'INR' in text or 'Rs' in text):
                        price_divs.append(div)
                except:
                    continue
            
            logger.info(f"Found {len(price_divs)} divs with price symbols")
            flight_elements = price_divs[:20]  # Take first 20 as potential flights
        
        logger.info(f"Processing {len(flight_elements)} potential flight elements...")
        
        # Extract flight information
        for idx, elem in enumerate(flight_elements[:30], 1):  # Limit to first 30
            try:
                elem_text = elem.text
                
                if not elem_text or len(elem_text) < 10:
                    continue
                
                # Extract flight details from text
                flight_info = {
                    "airline": "",
                    "price": "",
                    "departure_time": "",
                    "arrival_time": "",
                    "duration": "",
                    "stops": "",
                    "origin": origin,
                    "destination": destination,
                    "departure_date": date,
                    "full_text": elem_text[:200]  # Store sample text for debugging
                }
                
                # Extract airline name (usually first line or contains "Air", "Airways", etc.)
                lines = elem_text.split('\n')
                for line in lines:
                    if any(keyword in line for keyword in ['Air', 'Indigo', 'Vistara', 'SpiceJet', 'GoAir', 'AirAsia']):
                        flight_info['airline'] = line.strip()
                        break
                
                # Extract price (contains ₹ or INR)
                for line in lines:
                    if '₹' in line or 'INR' in line or 'Rs' in line:
                        # Clean up price
                        import re
                        price_match = re.search(r'₹\s*[\d,]+|INR\s*[\d,]+|Rs\.?\s*[\d,]+', line)
                        if price_match:
                            flight_info['price'] = price_match.group(0).strip()
                            break
                
                # Extract times (format like "6:00 AM" or "18:30")
                import re
                time_pattern = r'\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?'
                times = re.findall(time_pattern, elem_text)
                if len(times) >= 2:
                    flight_info['departure_time'] = times[0]
                    flight_info['arrival_time'] = times[1]
                
                # Extract duration (like "2h 30m" or "2 hr 30 min")
                duration_pattern = r'\d+h\s*\d*m?|\d+\s*hr\s*\d*\s*min'
                duration_match = re.search(duration_pattern, elem_text, re.IGNORECASE)
                if duration_match:
                    flight_info['duration'] = duration_match.group(0)
                
                # Extract stops info
                if 'nonstop' in elem_text.lower() or 'non-stop' in elem_text.lower():
                    flight_info['stops'] = 'Nonstop'
                elif '1 stop' in elem_text.lower():
                    flight_info['stops'] = '1 stop'
                elif '2 stop' in elem_text.lower():
                    flight_info['stops'] = '2 stops'
                
                # Only add if we have at least price or airline
                if flight_info['price'] or flight_info['airline']:
                    all_flights.append(flight_info)
                    logger.info(f"  {idx}. {flight_info['airline'] or 'Unknown'}: {flight_info['price'] or 'N/A'} ({flight_info['departure_time']} - {flight_info['arrival_time']})")
                
            except Exception as e:
                logger.debug(f"Error processing flight element {idx}: {e}")
                continue
        
        logger.info(f"Extracted {len(all_flights)} flights total")
        
        return {
            'timestamp': datetime.now().isoformat(),
            'origin': origin,
            'destination': destination,
            'departure_date': date,
            'total_flights': len(all_flights),
            'flights': all_flights
        }
        
    except Exception as e:
        logger.error(f"Error scraping Google Flights: {e}")
        return {
            'timestamp': datetime.now().isoformat(),
            'origin': origin,
            'destination': destination,
            'departure_date': date,
            'total_flights': 0,
            'flights': [],
            'error': str(e)
        }
    finally:
        driver.quit()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python google_flights_scraper.py ORIGIN DEST YYYY-MM-DD")
        print("Example: python google_flights_scraper.py IXM BOM 2025-10-15")
        print("\nMadurai Airport Code: IXM")
        sys.exit(1)
    
    origin = sys.argv[1].upper()
    dest = sys.argv[2].upper()
    date = sys.argv[3]
    
    print(f"\n{'='*60}")
    print(f"GOOGLE FLIGHTS SCRAPER - ALL AIRLINES")
    print(f"{'='*60}")
    print(f"From: {origin}")
    print(f"To: {dest}")
    print(f"Date: {date}")
    print(f"{'='*60}\n")
    
    result = scrape_google_flights(origin, dest, date, headless=False)
    
    print(f"\n{'='*60}")
    print(f"SCRAPING COMPLETE")
    print(f"{'='*60}")
    print(f"Total Flights: {result['total_flights']}")
    
    if result['flights']:
        print(f"\nFlights Found:")
        for i, flight in enumerate(result['flights'][:10], 1):
            print(f"  {i}. {flight['airline']}: {flight['price']} ({flight['departure_time']} - {flight['arrival_time']}) {flight['stops']}")
        
        # Save to JSON
        with open('google_flights_results.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nSaved to: google_flights_results.json")
    else:
        print("No flights found")
        if 'error' in result:
            print(f"Error: {result['error']}")
    
    print(f"{'='*60}\n")

