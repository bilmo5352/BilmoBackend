@echo off
echo ========================================
echo BILMO DOCKER DEPLOYMENT - COMPLETE SETUP
echo ========================================
echo.

echo [1/8] Starting Docker Desktop...
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
echo Waiting for Docker to initialize...
timeout /t 45 /nobreak

echo.
echo [2/8] Checking Docker status...
docker version
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running properly
    pause
    exit /b 1
)

echo.
echo [3/8] Stopping any existing containers...
docker-compose down --remove-orphans

echo.
echo [4/8] Cleaning up old images and containers...
docker system prune -f
docker image prune -f

echo.
echo [5/8] Building fresh container with all fixes...
echo - Myntra rating extraction fix
echo - Amazon rating improvements  
echo - Flipkart enhanced scraping
echo - Meesho image handling
echo - Cache busting frontend
echo - MongoDB integration
docker-compose build --no-cache bilmo-api

echo.
echo [6/8] Starting the API container...
docker-compose up -d bilmo-api

echo.
echo [7/8] Waiting for container to start...
timeout /t 30 /nobreak

echo.
echo [8/8] Testing the API...
echo Testing API status...
curl -s http://localhost:5000/status
echo.
echo Testing search functionality...
curl -s "http://localhost:5000/search?q=test&force_refresh=true" | findstr "success"

echo.
echo ========================================
echo DEPLOYMENT COMPLETE!
echo ========================================
echo.
echo API Endpoints:
echo - Home: http://localhost:5000
echo - Search: http://localhost:5000/search?q=phones
echo - Status: http://localhost:5000/status
echo - History: http://localhost:5000/history
echo.
echo Features Included:
echo ✅ Myntra rating extraction (visits product pages)
echo ✅ Amazon comprehensive rating extraction
echo ✅ Flipkart enhanced MRP and discount parsing
echo ✅ Meesho improved image handling
echo ✅ Frontend cache busting
echo ✅ MongoDB caching system
echo ✅ All platforms working with ratings
echo.
echo Container Status:
docker-compose ps
echo.
echo To view logs: docker-compose logs -f bilmo-api
echo To stop: docker-compose down
echo.
pause
