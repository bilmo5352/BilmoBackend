@echo off
echo Product Search Tool
echo ===================
if "%1"=="" (
    echo Usage: search.bat "product name"
    echo Example: search.bat "iphone 15"
    pause
    exit /b
)
python search_products.py %*
pause
