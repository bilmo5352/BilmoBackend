#!/usr/bin/env python3
"""
Flight Price Scraper - Multi-Airline Support
Scrapes flight prices from Air India, IndiGo, and other airlines
"""
import csv
import time
import re
from datetime import datetime
from dateutil import parser as dateparser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
try:
    from fake_useragent import UserAgent
except ImportError:
    UserAgent = None
import sys
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- Config ----------
HEADLESS = False           # start with headful to reduce blocks
IMPLICIT_WAIT = 5
EXPLICIT_TIMEOUT = 25
OUTPUT_CSV = "airline_prices.csv"

# ---------- Helpers ----------
def make_driver(headless=HEADLESS, proxy=None):
    options = Options()
    
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
    
    # User agent
    if UserAgent:
        ua = UserAgent()
        options.add_argument(f"user-agent={ua.random}")
    else:
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-blink-features=AutomationControlled")
    if not headless:
        options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    if proxy:
        options.add_argument(f'--proxy-server={proxy}')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        logger.info("Flight scraper WebDriver initialized")
    except Exception as e:
        logger.error(f"ChromeDriverManager failed: {e}")
        try:
            driver = webdriver.Chrome(options=options)
            logger.info("Flight scraper using system ChromeDriver")
        except Exception as e2:
            logger.error(f"All ChromeDriver methods failed: {e2}")
            raise e2
    
    driver.implicitly_wait(IMPLICIT_WAIT)
    
    # Remove webdriver properties
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def parse_price(text):
    """Extract numeric price from a string like 'INR 4,799' or '₹4,799'"""
    if not text:
        return None
    # remove non digits except dot
    cleaned = re.sub(r"[^\d\.]", "", text)
    try:
        if cleaned == "":
            return None
        # some prices have no cents, parse int
        if "." in cleaned:
            return float(cleaned)
        return int(cleaned)
    except:
        return None

def safe_get_text(elem):
    try:
        return elem.text.strip()
    except:
        return ""

# ---------- Scraper functions ----------
def scrape_airindia(driver, origin, dest, depart_date):
    """
    Template approach:
    - go to airindia.in
    - fill origin/destination/date
    - submit search
    - wait for results and extract rows
    NOTE: site structure may change; inspect and replace selectors.
    """
    out = []
    driver.get("https://www.airindia.in/")
    wait = WebDriverWait(driver, EXPLICIT_TIMEOUT)

    # Accept cookies if present (example)
    try:
        cookie_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Accept')]")))
        cookie_btn.click()
    except TimeoutException:
        pass

    # NOTE: the actual Air India site uses custom form elements — you must inspect and update selectors.
    # Below are example interactions; you may need to change to match current DOM.
    try:
        # origin
        origin_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input#originPlace")))  # <- adjust
        origin_input.click()
        origin_input.clear()
        origin_input.send_keys(origin)
        time.sleep(0.6)
        origin_input.send_keys(Keys.ENTER)

        # destination
        dest_input = driver.find_element(By.CSS_SELECTOR, "input#destinationPlace")  # <- adjust
        dest_input.click()
        dest_input.clear()
        dest_input.send_keys(dest)
        time.sleep(0.6)
        dest_input.send_keys(Keys.ENTER)

        # date — open datepicker, set value if possible
        # Some airline date inputs accept direct text; others require clicking calendar.
        try:
            date_input = driver.find_element(By.CSS_SELECTOR, "input#departureDate")  # <- adjust
            date_input.click()
            date_input.clear()
            date_input.send_keys(depart_date)
            date_input.send_keys(Keys.ENTER)
        except NoSuchElementException:
            pass

        # Click search button
        search_btn = driver.find_element(By.CSS_SELECTOR, "button.search-flights")  # <- adjust
        search_btn.click()

        # Wait for results to appear
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".flight-result, .fare-result, .result-row")))  # <- adjust

        # Collect top results
        rows = driver.find_elements(By.CSS_SELECTOR, ".flight-result, .fare-result, .result-row")  # <- adjust
        for r in rows[:10]:
            try:
                price_elem = r.find_element(By.CSS_SELECTOR, ".price, .fare, .total")  # <- adjust
            except:
                price_elem = None
            try:
                carrier_elem = r.find_element(By.CSS_SELECTOR, ".airline, .carrier")  # <- adjust
            except:
                carrier_elem = None
            try:
                dep = r.find_element(By.CSS_SELECTOR, ".dept-time, .departure-time").text
            except:
                dep = ""
            try:
                arr = r.find_element(By.CSS_SELECTOR, ".arrival-time, .arr-time").text
            except:
                arr = ""
            price_text = safe_get_text(price_elem) if price_elem else ""
            price_val = parse_price(price_text)
            out.append({
                "site": "AirIndia",
                "carrier": safe_get_text(carrier_elem) if carrier_elem else "Air India",
                "price_text": price_text,
                "price": price_val,
                "dep_time": dep,
                "arr_time": arr,
                "search_date": datetime.utcnow().isoformat(),
                "origin": origin,
                "destination": dest,
                "departure_date": depart_date
            })
    except Exception as e:
        print("AirIndia scrape error:", e)
    return out

def scrape_indigo(driver, origin, dest, depart_date):
    """
    Template approach for IndiGo (goindigo.in).
    Similar caveats as above: selectors will likely change.
    """
    out = []
    driver.get("https://www.goindigo.in/")
    wait = WebDriverWait(driver, EXPLICIT_TIMEOUT)

    # Accept cookie popups if any
    try:
        consent = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Accept')]")))
        consent.click()
    except TimeoutException:
        pass

    try:
        # Sample selectors; update after inspecting site
        origin_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input#fromCity")))
        origin_input.click()
        origin_input.clear()
        origin_input.send_keys(origin)
        time.sleep(0.8)
        origin_input.send_keys(Keys.ENTER)

        dest_input = driver.find_element(By.CSS_SELECTOR, "input#toCity")
        dest_input.click()
        dest_input.clear()
        dest_input.send_keys(dest)
        time.sleep(0.8)
        dest_input.send_keys(Keys.ENTER)

        # date input
        date_input = driver.find_element(By.CSS_SELECTOR, "input#departDate")
        date_input.click()
        date_input.clear()
        date_input.send_keys(depart_date)
        date_input.send_keys(Keys.ENTER)

        # search
        search_btn = driver.find_element(By.CSS_SELECTOR, "button.search-flights")
        search_btn.click()

        # wait for results
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".flightListItem, .search-result-row, .fares-list")))
        rows = driver.find_elements(By.CSS_SELECTOR, ".flightListItem, .search-result-row, .fares-list")
        for r in rows[:10]:
            try:
                price_elem = r.find_element(By.CSS_SELECTOR, ".price, .fare, .amount")
            except:
                price_elem = None
            try:
                carrier_elem = r.find_element(By.CSS_SELECTOR, ".airline-name")
            except:
                carrier_elem = None
            try:
                dep = r.find_element(By.CSS_SELECTOR, ".departure .time").text
            except:
                dep = ""
            try:
                arr = r.find_element(By.CSS_SELECTOR, ".arrival .time").text
            except:
                arr = ""
            price_text = safe_get_text(price_elem) if price_elem else ""
            price_val = parse_price(price_text)
            out.append({
                "site": "IndiGo",
                "carrier": safe_get_text(carrier_elem) if carrier_elem else "IndiGo",
                "price_text": price_text,
                "price": price_val,
                "dep_time": dep,
                "arr_time": arr,
                "search_date": datetime.utcnow().isoformat(),
                "origin": origin,
                "destination": dest,
                "departure_date": depart_date
            })
    except Exception as e:
        print("IndiGo scrape error:", e)
    return out

# ---------- Runner ----------
def main():
    # example usage: python flightapi.py DEL BOM 2025-10-20
    if len(sys.argv) < 4:
        print("Usage: python flightapi.py ORIGIN DEST YYYY-MM-DD")
        print("Example: python flightapi.py DEL BOM 2025-10-20")
        sys.exit(1)
    origin = sys.argv[1]
    dest = sys.argv[2]
    depart_date = sys.argv[3]

    print(f"\n{'='*60}")
    print(f"FLIGHT PRICE SCRAPER")
    print(f"{'='*60}")
    print(f"Route: {origin} -> {dest}")
    print(f"Date: {depart_date}")
    print(f"Mode: {'Headless' if HEADLESS else 'Visible Browser'}")
    print(f"{'='*60}\n")

    driver = make_driver(headless=HEADLESS)
    all_results = []
    try:
        logger.info("Scraping Air India...")
        all_results += scrape_airindia(driver, origin, dest, depart_date)
        logger.info(f"Found {len([r for r in all_results if r['site'] == 'AirIndia'])} Air India flights")
        
        # small randomized sleep
        time.sleep(random.uniform(2.0, 4.5))
        
        logger.info("Scraping IndiGo...")
        all_results += scrape_indigo(driver, origin, dest, depart_date)
        logger.info(f"Found {len([r for r in all_results if r['site'] == 'IndiGo'])} IndiGo flights")
    finally:
        driver.quit()

    print(f"\n{'='*60}")
    print(f"SCRAPING COMPLETE")
    print(f"{'='*60}")
    print(f"Total Flights Found: {len(all_results)}")
    
    if all_results:
        try:
            import pandas as pd
            df = pd.DataFrame(all_results)
            df.to_csv(OUTPUT_CSV, index=False)
            print(f"Saved to: {OUTPUT_CSV}")
        except ImportError:
            # Save as JSON if pandas not available
            import json
            with open('airline_prices.json', 'w') as f:
                json.dump(all_results, f, indent=2, default=str)
            print(f"Saved to: airline_prices.json")
        
        print(f"\nSample flights:")
        for i, flight in enumerate(all_results[:5], 1):
            print(f"  {i}. {flight['carrier']}: {flight['price_text']} ({flight['dep_time']} - {flight['arr_time']})")
    else:
        print("No results collected. Inspect selectors / site behavior.")
    
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
