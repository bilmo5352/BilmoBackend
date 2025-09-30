# Docker Deployment Guide

## Quick Start

1. **Start Docker Desktop** (if not already running)
2. **Run the deployment script:**
   ```bash
   deploy.bat
   ```

## Manual Deployment

### 1. Build the Container
```bash
docker-compose build bilmo-api
```

### 2. Run the API
```bash
docker-compose up -d bilmo-api
```

### 3. Test the API
```bash
curl http://localhost:5000/status
```

## API Endpoints

- **Home:** http://localhost:5000
- **Search:** http://localhost:5000/search?q=phones
- **Status:** http://localhost:5000/status
- **History:** http://localhost:5000/history

## With MongoDB (Optional)

To run with MongoDB caching:
```bash
docker-compose --profile mongodb up -d
```

## Container Features

- **Smart Caching:** Results cached for 24 hours
- **Multi-platform Search:** Amazon, Flipkart, Meesho, Myntra
- **Health Checks:** Automatic container health monitoring
- **Security:** Non-root user, proper capabilities
- **Persistence:** HTML files and logs mounted as volumes

## Troubleshooting

1. **Docker not running:** Start Docker Desktop manually
2. **Port conflicts:** Change port mapping in docker-compose.yml
3. **Chrome issues:** Container includes all necessary Chrome dependencies
4. **Memory issues:** Increase Docker Desktop memory allocation

## Development

To rebuild after code changes:
```bash
docker-compose build --no-cache bilmo-api
docker-compose up -d bilmo-api
```

