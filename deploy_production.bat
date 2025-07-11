@echo off
REM Production Deployment Script for Windows

echo 🚀 Secure File Sharing System - Production Deployment
echo ==================================================

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker Compose is not installed or not in PATH
    pause
    exit /b 1
)

echo INFO: All required tools are available

REM Create directories
if not exist "nginx\ssl" mkdir nginx\ssl
if not exist "logs" mkdir logs

REM Copy environment template if it doesn't exist
if not exist ".env" (
    copy .env.production .env
    echo INFO: Environment file created. Please edit .env with your configuration.
)

echo.
echo Building Docker images...
docker-compose -f docker-compose.prod.yml build

if errorlevel 1 (
    echo ERROR: Failed to build Docker images
    pause
    exit /b 1
)

echo.
echo Starting services...
docker-compose -f docker-compose.prod.yml up -d

if errorlevel 1 (
    echo ERROR: Failed to start services
    pause
    exit /b 1
)

echo.
echo Waiting for services to start...
timeout /t 30 /nobreak >nul

echo.
echo Running database migration...
docker-compose -f docker-compose.prod.yml exec -T app python migrate_database.py

echo.
echo 🎉 Deployment completed!
echo.
echo Next steps:
echo 1. Edit .env file with your production configuration
echo 2. Access your application at: http://localhost:8000
echo 3. API documentation: http://localhost:8000/docs
echo 4. Change the default ops admin password
echo 5. Configure SSL certificates for production
echo.
echo Default credentials:
echo   Username: ops_admin
echo   Password: ops123456
echo.
pause
