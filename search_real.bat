@echo off
echo Real Product Search Tool - MongoDB & JSON Output
echo =================================================
if "%1"=="" (
    echo Usage: search_real.bat "product name"
    echo Example: search_real.bat "iphone 15"
    echo.
    echo This will:
    echo - Search Amazon, Flipkart, Meesho, Myntra
    echo - Save JSON file with real product data
    echo - Store results in MongoDB
    echo.
    pause
    exit /b
)
python real_search_products.py %* --headless
pause
