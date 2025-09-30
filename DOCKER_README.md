# Bilmo E-commerce Scraper API - Docker Deployment Guide

This guide explains how to deploy the Bilmo E-commerce Scraper API using Docker containers.

## 📋 Prerequisites

- **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
- **Docker Compose** v3.8 or higher
- At least **4GB RAM** available for containers
- At least **10GB disk space**

## 🏗️ Architecture

The application consists of two services:

1. **API Service** (`bilmo-api`)
   - Flask-based REST API
   - Selenium web scraping for Amazon, Flipkart, Meesho, and Myntra
   - Chrome/ChromeDriver for headless browsing
   - Exposed on port `5000`

2. **MongoDB Service** (`bilmo-mongodb`)
   - MongoDB 7.0 database
   - Persistent data storage
   - Exposed on port `27017`

## 🚀 Quick Start

### Windows

```batch
# Deploy the application
deploy.bat
```

### Linux/Mac

```bash
# Make the script executable (first time only)
chmod +x deploy.sh

# Deploy the application
./deploy.sh
```

## 📝 Manual Deployment

If you prefer to run commands manually:

```bash
# Build and start services
docker-compose up -d --build

# View logs
docker-compose logs -f api

# Check service status
docker-compose ps

# Stop services
docker-compose down
```

## 🔧 Configuration

### Environment Variables

The API service uses the following environment variables (configured in `docker-compose.yml`):

- `FLASK_APP=app.py` - Main Flask application
- `FLASK_ENV=production` - Production mode
- `PYTHONUNBUFFERED=1` - Real-time logging
- `MONGODB_URI` - MongoDB connection string

### MongoDB Configuration

- **Username:** `admin`
- **Password:** `password123`
- **Database:** `scraper_db`
- **Port:** `27017`

⚠️ **Security Warning:** Change the default MongoDB credentials in production!

## 🌐 API Endpoints

Once deployed, the API is available at `http://localhost:5000`:

- `GET /` - Welcome page
- `GET /health` - Health check endpoint
- `POST /search` - Unified search across all platforms
- `GET /search/<site>` - Search specific site (amazon, flipkart, meesho, myntra)
- `GET /search/<site>/detailed` - Detailed product information
- `GET /mongodb/results` - Retrieve cached search results
- `GET /mongodb/results/<result_id>` - Get specific result by ID

## 📊 Monitoring

### View Logs

```bash
# All services
docker-compose logs -f

# API only
docker-compose logs -f api

# MongoDB only
docker-compose logs -f mongodb
```

### Health Checks

```bash
# Check API health
curl http://localhost:5000/health

# Check MongoDB health
docker exec bilmo-mongodb mongosh --eval "db.adminCommand('ping')"
```

### Container Stats

```bash
# Real-time resource usage
docker stats bilmo-api bilmo-mongodb
```

## 🔄 Updates and Maintenance

### Rebuild Containers

```bash
# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

### Clear All Data (Fresh Start)

```bash
# Stop and remove everything (including volumes)
docker-compose down -v --rmi all

# Restart
docker-compose up -d --build
```

### Backup MongoDB Data

```bash
# Export data
docker exec bilmo-mongodb mongodump --out=/data/backup

# Copy backup to host
docker cp bilmo-mongodb:/data/backup ./mongodb_backup
```

### Restore MongoDB Data

```bash
# Copy backup to container
docker cp ./mongodb_backup bilmo-mongodb:/data/backup

# Restore data
docker exec bilmo-mongodb mongorestore /data/backup
```

## 🐛 Troubleshooting

### API Container Fails to Start

1. Check logs: `docker-compose logs api`
2. Verify Chrome installation: `docker exec bilmo-api google-chrome --version`
3. Check memory limits: `docker stats bilmo-api`

### MongoDB Connection Issues

1. Verify MongoDB is running: `docker-compose ps`
2. Check MongoDB logs: `docker-compose logs mongodb`
3. Test connection: `docker exec bilmo-mongodb mongosh --eval "db.version()"`

### Port Conflicts

If ports 5000 or 27017 are already in use:

1. Edit `docker-compose.yml`
2. Change port mappings (e.g., `5001:5000` for API)
3. Restart: `docker-compose up -d`

### Out of Memory

If containers are killed due to memory:

1. Increase Docker Desktop memory allocation
2. Reduce container limits in `docker-compose.yml`
3. Close other applications

## 📦 Persistent Data

Data is persisted in Docker volumes:

- `mongodb_data` - Database files
- `mongodb_config` - MongoDB configuration
- `./html_files` - Scraped HTML files (mounted)
- `./logs` - Application logs (mounted)

## 🔒 Security Considerations

### Production Deployment

1. **Change MongoDB credentials**
   ```yaml
   environment:
     - MONGO_INITDB_ROOT_USERNAME=your_username
     - MONGO_INITDB_ROOT_PASSWORD=your_secure_password
   ```

2. **Use environment file for secrets**
   ```bash
   # Create .env file
   echo "MONGO_PASSWORD=secure_password" > .env
   
   # Reference in docker-compose.yml
   environment:
     - MONGO_INITDB_ROOT_PASSWORD=${MONGO_PASSWORD}
   ```

3. **Enable MongoDB authentication**
4. **Use HTTPS/TLS for API**
5. **Restrict MongoDB port exposure**

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [MongoDB Docker Hub](https://hub.docker.com/_/mongo)
- [Flask Documentation](https://flask.palletsprojects.com/)

## 🆘 Support

For issues or questions:
1. Check the logs first
2. Review this documentation
3. Create an issue on GitHub
4. Contact the development team

---

**Last Updated:** September 30, 2025

