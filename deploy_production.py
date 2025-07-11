#!/usr/bin/env python3
"""
Production Deployment Script for Secure File Sharing System
"""

import os
import sys
import subprocess
import shutil
import secrets
import string
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_secret_key():
    """Generate a secure secret key"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(64))

def check_requirements():
    """Check if required tools are installed"""
    required_tools = ['docker', 'docker-compose']
    
    for tool in required_tools:
        if not shutil.which(tool):
            logger.error(f"{tool} is not installed or not in PATH")
            return False
    
    logger.info("All required tools are available")
    return True

def setup_environment():
    """Setup production environment variables"""
    env_file = '.env.production'
    
    if os.path.exists(env_file):
        logger.info(f"{env_file} already exists")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            return
    
    # Generate secure values
    secret_key = generate_secret_key()
    
    # Get user inputs
    print("\n=== Production Configuration ===")
    domain = input("Enter your domain (e.g., yourdomain.com): ").strip()
    if not domain:
        domain = "localhost"
    
    email_host = input("Enter email host (e.g., smtp.sendgrid.net): ").strip()
    if not email_host:
        email_host = "smtp.gmail.com"
    
    email_user = input("Enter email username/API key: ").strip()
    email_password = input("Enter email password/API key: ").strip()
    email_from = input(f"Enter 'from' email address (noreply@{domain}): ").strip()
    if not email_from:
        email_from = f"noreply@{domain}"
    
    # Database configuration
    db_password = generate_secret_key()[:32]
    
    # Write environment file
    env_content = f"""# Production Environment Variables
# Generated on {os.popen('date').read().strip()}

# Application Security
SECRET_KEY={secret_key}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DOWNLOAD_TOKEN_EXPIRE_HOURS=1

# Database Configuration
DATABASE_URL=postgresql://fileuser:{db_password}@db:5432/filedb

# Email Configuration
EMAIL_HOST={email_host}
EMAIL_PORT=587
EMAIL_USER={email_user}
EMAIL_PASSWORD={email_password}
EMAIL_FROM={email_from}

# File Upload Configuration
UPLOAD_DIRECTORY=/app/uploads
MAX_FILE_SIZE=52428800
ALLOWED_EXTENSIONS=.pptx,.docx,.xlsx,.pdf

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false

# CORS Configuration
CORS_ORIGINS=https://{domain},https://www.{domain}
ALLOW_CREDENTIALS=true
ALLOW_METHODS=GET,POST,PUT,DELETE
ALLOW_HEADERS=*

# SSL/Security
SSL_REDIRECT=true
SECURE_COOKIES=true
ALLOWED_HOSTS={domain},www.{domain}

# Redis
REDIS_URL=redis://redis:6379/0

# Environment
ENVIRONMENT=production

# Operations user (CHANGE THESE IMMEDIATELY)
OPS_ADMIN_PASSWORD=change-me-immediately
OPS_ADMIN_EMAIL=ops@{domain}
"""
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    logger.info(f"Environment file created: {env_file}")
    logger.warning("IMPORTANT: Change the OPS_ADMIN_PASSWORD in the environment file!")
    
    return domain

def setup_ssl_certificates(domain):
    """Setup SSL certificates directory"""
    ssl_dir = Path("nginx/ssl")
    ssl_dir.mkdir(parents=True, exist_ok=True)
    
    cert_file = ssl_dir / "cert.pem"
    key_file = ssl_dir / "key.pem"
    
    if not cert_file.exists() or not key_file.exists():
        logger.info("SSL certificates not found. Creating self-signed certificates for testing...")
        
        # Create self-signed certificate for testing
        subprocess.run([
            'openssl', 'req', '-x509', '-newkey', 'rsa:4096', '-nodes',
            '-out', str(cert_file),
            '-keyout', str(key_file),
            '-days', '365',
            '-subj', f'/CN={domain}'
        ], check=True)
        
        logger.info("Self-signed SSL certificates created")
        logger.warning("For production, replace with real SSL certificates from Let's Encrypt")

def update_nginx_config(domain):
    """Update Nginx configuration with the correct domain"""
    nginx_conf = Path("nginx/nginx.conf")
    
    if nginx_conf.exists():
        # Read the file
        with open(nginx_conf, 'r') as f:
            content = f.read()
        
        # Replace placeholder domain
        content = content.replace('yourdomain.com', domain)
        content = content.replace('www.yourdomain.com', f'www.{domain}')
        
        # Write back
        with open(nginx_conf, 'w') as f:
            f.write(content)
        
        logger.info(f"Nginx configuration updated for domain: {domain}")

def build_application():
    """Build the Docker application"""
    logger.info("Building Docker images...")
    
    try:
        subprocess.run(['docker-compose', '-f', 'docker-compose.prod.yml', 'build'], check=True)
        logger.info("Docker images built successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to build Docker images: {e}")
        return False
    
    return True

def deploy_application():
    """Deploy the application"""
    logger.info("Deploying application...")
    
    try:
        # Stop any existing containers
        subprocess.run(['docker-compose', '-f', 'docker-compose.prod.yml', 'down'], 
                      capture_output=True)
        
        # Start the application
        subprocess.run(['docker-compose', '-f', 'docker-compose.prod.yml', 'up', '-d'], 
                      check=True)
        
        logger.info("Application deployed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to deploy application: {e}")
        return False

def run_migrations():
    """Run database migrations"""
    logger.info("Running database migrations...")
    
    try:
        subprocess.run([
            'docker-compose', '-f', 'docker-compose.prod.yml', 'exec', '-T', 'app',
            'python', 'migrate_database.py'
        ], check=True)
        
        logger.info("Database migrations completed")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Database migration failed: {e}")
        return False

def health_check(domain):
    """Perform health check"""
    import time
    import requests
    
    logger.info("Performing health check...")
    
    # Wait for services to start
    time.sleep(30)
    
    try:
        response = requests.get(f"http://{domain}:8000/health", timeout=10)
        if response.status_code == 200:
            logger.info("Health check passed!")
            return True
        else:
            logger.error(f"Health check failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False

def main():
    """Main deployment function"""
    print("🚀 Secure File Sharing System - Production Deployment")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Setup environment
    domain = setup_environment()
    
    # Setup SSL
    try:
        setup_ssl_certificates(domain)
    except Exception as e:
        logger.warning(f"SSL setup failed: {e}")
        logger.info("Continuing without SSL...")
    
    # Update Nginx config
    update_nginx_config(domain)
    
    # Build application
    if not build_application():
        sys.exit(1)
    
    # Deploy application
    if not deploy_application():
        sys.exit(1)
    
    # Run migrations
    if not run_migrations():
        logger.warning("Database migration failed, but continuing...")
    
    # Health check
    health_check(domain)
    
    print("\n🎉 Deployment completed!")
    print("\nNext steps:")
    print(f"1. Access your application at: https://{domain}")
    print(f"2. API documentation: https://{domain}/docs")
    print("3. Change the default ops admin password")
    print("4. Configure real SSL certificates")
    print("5. Set up monitoring and backups")
    print("\nDefault credentials:")
    print("  Username: ops_admin")
    print("  Password: change-me-immediately")

if __name__ == "__main__":
    main()
