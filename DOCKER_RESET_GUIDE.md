# Docker Reset Instructions

## Problem
Docker Desktop has corrupted storage causing I/O errors.

## Solution Steps

### 1. Reset Docker Desktop Completely
1. **Close Docker Desktop** (already done)
2. **Open Docker Desktop Settings**
3. **Go to "Troubleshoot" tab**
4. **Click "Reset to factory defaults"**
5. **Confirm the reset**

### 2. Alternative: Manual Reset
```bash
# Delete Docker data directory
rmdir /s "C:\Users\%USERNAME%\AppData\Roaming\Docker Desktop"
rmdir /s "C:\Users\%USERNAME%\AppData\Local\Docker"

# Restart Docker Desktop
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
```

### 3. After Reset
```bash
# Test Docker
docker version

# Build your API
docker-compose build bilmo-api

# Run your API
docker-compose up -d bilmo-api

# Test API
curl http://localhost:5000/status
```

## Why This Happened
- Docker's containerd storage got corrupted
- I/O errors in metadata database
- Need complete reset to fix

## After Reset
Your API will work with all platforms:
- ✅ Amazon
- ✅ Flipkart  
- ✅ Myntra
- ✅ Meesho

The ChromeDriver issue is already fixed in the code.

