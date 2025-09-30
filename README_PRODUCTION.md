# Bilmo API - Production Docker Deployment

## 🚀 Quick Start

### Option 1: Automated Deployment (Windows)
```bash
docker-deploy-prod.bat
```

### Option 2: Manual Deployment

#### Build the image:
```bash
docker-compose -f docker-compose.prod.yml build
```

#### Start the container:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

#### Check status:
```bash
curl http://localhost:5000/status
```

## 📍 API Endpoints

- **Home:** http://localhost:5000
- **Status:** http://localhost:5000/status
- **Search:** http://localhost:5000/search?q=phones
- **History:** http://localhost:5000/history

## 🛠️ Container Management

### View Logs
```bash
docker-compose -f docker-compose.prod.yml logs -f bilmo-api-prod
```

### Stop Container
```bash
docker-compose -f docker-compose.prod.yml down
```

### Restart Container
```bash
docker-compose -f docker-compose.prod.yml restart bilmo-api-prod
```

### Rebuild After Code Changes
```bash
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

## 🔧 Configuration

### With MongoDB (Optional)

1. Uncomment the MongoDB service in `docker-compose.prod.yml`
2. Uncomment the MongoDB environment variable
3. Rebuild and restart:
```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

## 📊 Features

- ✅ **Multi-platform Search**: Amazon, Flipkart, Meesho, Myntra
- ✅ **Smart Caching**: 24-hour result caching
- ✅ **Chrome Integration**: Headless browser for web scraping
- ✅ **Health Checks**: Automatic container monitoring
- ✅ **Security**: Non-root user, proper capabilities
- ✅ **Resource Limits**: 4GB memory limit, 2GB shared memory

## 🐛 Troubleshooting

### Container won't start
```bash
docker-compose -f docker-compose.prod.yml logs bilmo-api-prod
```

### Port already in use
Change the port mapping in `docker-compose.prod.yml`:
```yaml
ports:
  - "5001:5000"  # Use port 5001 instead
```

### Chrome issues
The container includes all necessary Chrome dependencies. If issues persist:
1. Check logs for specific Chrome errors
2. Verify shared memory allocation (shm_size: 2gb)
3. Ensure SYS_ADMIN capability is enabled

### Memory issues
Increase Docker Desktop memory allocation:
1. Open Docker Desktop
2. Settings → Resources → Advanced
3. Increase Memory to at least 6GB

## 📦 What's Included

- **Dockerfile.production**: Optimized production Dockerfile
- **docker-compose.prod.yml**: Production compose configuration
- **docker-deploy-prod.bat**: Automated deployment script
- **Health checks**: Automatic container health monitoring
- **Volume mounts**: Persistent data storage

## 🔐 Security Features

- Non-root user execution
- Proper capability management
- Seccomp profile configuration
- Resource limits and quotas


