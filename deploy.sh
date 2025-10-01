#!/bin/bash
# Bilmo E-commerce Scraper API - Deployment Script
# This script builds and deploys the Docker containers

set -e

echo "========================================"
echo "Bilmo API Deployment"
echo "========================================"
echo

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "[ERROR] Docker is not running. Please start Docker."
    exit 1
fi

echo "[1/5] Stopping existing containers..."
docker-compose down

echo
echo "[2/5] Removing old images..."
docker-compose down --rmi all --volumes --remove-orphans 2>/dev/null || true

echo
echo "[3/5] Building new images..."
docker-compose build --no-cache

echo
echo "[4/5] Starting services..."
docker-compose up -d

echo
echo "[5/5] Checking service health..."
sleep 10

docker-compose ps

echo
echo "========================================"
echo "Deployment Complete!"
echo "========================================"
echo
echo "API is available at: http://localhost:5000"
echo "MongoDB is available at: localhost:27017"
echo
echo "To view logs: docker-compose logs -f api"
echo "To stop services: docker-compose down"
echo


