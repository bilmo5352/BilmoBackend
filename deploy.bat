@echo off
echo Starting Docker Desktop...
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"

echo Waiting for Docker to start...
timeout /t 30 /nobreak

echo Checking Docker status...
docker version

echo Building the container...
docker-compose build bilmo-api

echo Starting the API container...
docker-compose up -d bilmo-api

echo API should be running at http://localhost:5000
echo Check status with: curl http://localhost:5000/status
pause

