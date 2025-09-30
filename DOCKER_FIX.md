# Docker I/O Issue Fix

## Problem
Docker is experiencing I/O errors preventing container operations.

## Quick Solutions

### Option 1: Restart Docker Desktop
1. Close Docker Desktop completely
2. Restart Docker Desktop
3. Run: `docker-compose up -d bilmo-api`

### Option 2: Manual Container with Port Mapping
```bash
# Stop all containers
docker stop $(docker ps -q)

# Remove problematic containers
docker system prune -f

# Start with proper port mapping
docker run -d --name bilmo-api-fixed -p 5000:5000 bilmo-main-bilmo-api
```

### Option 3: Run API Directly (No Docker)
```bash
# Install dependencies
pip install -r requirements.txt

# Run the API directly
python smart_api.py
```

## Frontend Fix Applied
- Changed API URL from `127.0.0.1:5000` to `localhost:5000`
- This should work once the container is running with proper port mapping

## Test Connection
```bash
curl http://localhost:5000/status
```

The main issue is Docker I/O errors preventing proper container management. Once Docker is restarted, the API should work with all platforms (Amazon, Myntra, Meesho, Flipkart).

