#!/bin/bash
# Quick fix for ChromeDriver version mismatch
# This script removes the old ChromeDriver and lets WebDriverManager handle it

echo "🔧 Fixing ChromeDriver version mismatch..."

# Remove old ChromeDriver
rm -f /usr/local/bin/chromedriver

echo "✅ Old ChromeDriver removed"
echo "🔄 WebDriverManager will now download the correct version automatically"
echo "🚀 Restart the container to apply changes"

# Test if WebDriverManager works
python3 -c "
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium import webdriver

try:
    print('Testing WebDriverManager...')
    service = Service(ChromeDriverManager().install())
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(service=service, options=options)
    driver.get('https://www.google.com')
    print('✅ WebDriverManager test successful!')
    driver.quit()
except Exception as e:
    print(f'❌ WebDriverManager test failed: {e}')
"

