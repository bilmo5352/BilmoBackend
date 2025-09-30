@echo off
echo ========================================
echo BILMO DOCKER RESET AND REDEPLOY
echo ========================================
echo.

echo [1/6] Stopping all containers...
docker-compose down --remove-orphans

echo.
echo [2/6] Removing all containers and images...
docker container prune -f
docker image prune -a -f
docker volume prune -f

echo.
echo [3/6] Cleaning Docker system...
docker system prune -a -f

echo.
echo [4/6] Building fresh container...
docker-compose build --no-cache bilmo-api

echo.
echo [5/6] Starting fresh deployment...
docker-compose up -d bilmo-api

echo.
echo [6/6] Testing deployment...
timeout /t 30 /nobreak
curl -s http://localhost:5000/status

echo.
echo ========================================
echo RESET COMPLETE!
echo ========================================
echo.
echo Container Status:
docker-compose ps
echo.
echo API is running at: http://localhost:5000
echo.
pause
