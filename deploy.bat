@echo off
REM Bilmo E-commerce Scraper API - Deployment Script
REM This script builds and deploys the Docker containers

echo ========================================
echo Bilmo API Deployment
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running. Please start Docker Desktop.
    pause
    exit /b 1
)

echo [1/5] Stopping existing containers...
docker-compose down

echo.
echo [2/5] Removing old images...
docker-compose down --rmi all --volumes --remove-orphans 2>nul

echo.
echo [3/5] Building new images...
docker-compose build --no-cache

echo.
echo [4/5] Starting services...
docker-compose up -d

echo.
echo [5/5] Checking service health...
timeout /t 10 /nobreak >nul

docker-compose ps

echo.
echo ========================================
echo Deployment Complete!
echo ========================================
echo.
echo API is available at: http://localhost:5000
echo MongoDB is available at: localhost:27017
echo.
echo To view logs: docker-compose logs -f api
echo To stop services: docker-compose down
echo.
pause