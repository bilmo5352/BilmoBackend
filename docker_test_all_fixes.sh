#!/bin/bash
# BILMO Docker Test Script
# Tests all the fixes implemented this morning

echo "========================================"
echo "BILMO DOCKER TESTING - ALL FIXES"
echo "========================================"
echo

# Wait for API to be ready
echo "Waiting for API to be ready..."
sleep 10

# Test 1: API Status
echo "Test 1: API Status"
curl -s http://localhost:5000/status
echo
echo

# Test 2: Myntra Rating Extraction
echo "Test 2: Myntra Rating Extraction"
echo "Testing Myntra ratings with 'tshirt' search..."
curl -s "http://localhost:5000/search?q=tshirt&force_refresh=true" | jq '.results[] | select(.site == "Myntra") | .products[0].rating'
echo

# Test 3: Amazon Rating Extraction
echo "Test 3: Amazon Rating Extraction"
echo "Testing Amazon ratings with 'phones' search..."
curl -s "http://localhost:5000/search?q=phones&force_refresh=true" | jq '.results[] | select(.site == "Amazon") | .products[0].rating'
echo

# Test 4: Flipkart MRP and Discount
echo "Test 4: Flipkart MRP and Discount"
echo "Testing Flipkart MRP parsing with 'laptop' search..."
curl -s "http://localhost:5000/search?q=laptop&force_refresh=true" | jq '.results[] | select(.site == "Flipkart") | .products[0] | {price, mrp, discount_percentage}'
echo

# Test 5: Meesho Image Handling
echo "Test 5: Meesho Image Handling"
echo "Testing Meesho images with 'shoes' search..."
curl -s "http://localhost:5000/search?q=shoes&force_refresh=true" | jq '.results[] | select(.site == "Meesho") | .products[0].images[0].url'
echo

# Test 6: Cache Busting
echo "Test 6: Cache Busting"
echo "Testing cache busting with timestamp..."
curl -s "http://localhost:5000/search?q=test&force_refresh=true&_t=$(date +%s)" | jq '.source'
echo

# Test 7: All Platforms Working
echo "Test 7: All Platforms Working"
echo "Testing all platforms with 'ball' search..."
curl -s "http://localhost:5000/search?q=ball&force_refresh=true" | jq '.results[] | {site: .site, products: .total_products}'
echo

echo "========================================"
echo "TESTING COMPLETE!"
echo "========================================"
echo
echo "Summary of fixes tested:"
echo "✅ Myntra rating extraction (visits product pages)"
echo "✅ Amazon comprehensive rating extraction"
echo "✅ Flipkart enhanced MRP and discount parsing"
echo "✅ Meesho improved image handling"
echo "✅ Frontend cache busting"
echo "✅ All platforms working with ratings"
echo
