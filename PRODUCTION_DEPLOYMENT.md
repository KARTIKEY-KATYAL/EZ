# 🚀 PRODUCTION DEPLOYMENT GUIDE

## **Production Deployment Strategy**

### **1. Infrastructure Options**

#### **Option A: Cloud Deployment (Recommended)**
```bash
# AWS/GCP/Azure Setup
- Application: EC2/Compute Engine/App Service
- Database: RDS PostgreSQL/Cloud SQL/Azure Database
- File Storage: S3/Cloud Storage/Blob Storage
- Load Balancer: ALB/Cloud Load Balancer
- CDN: CloudFront/Cloud CDN
- SSL: Let's Encrypt/AWS Certificate Manager
```

#### **Option B: Docker Deployment**
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/filedb
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads
  
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: filedb
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - app

volumes:
  postgres_data:
```

### **2. Security Hardening**

#### **Environment Variables**
```bash
# Production .env
SECRET_KEY=<strong-256-bit-secret>
DATABASE_URL=postgresql://user:pass@prod-db:5432/filedb
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com
CORS_ORIGINS=https://yourdomain.com
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USER=apikey
EMAIL_PASSWORD=<sendgrid-api-key>
SSL_REDIRECT=true
SECURE_COOKIES=true
```

#### **Security Headers**
```python
# Add to main.py
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["yourdomain.com"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

#### **Rate Limiting**
```python
# Install: pip install slowapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/ops/login")
@limiter.limit("5/minute")
async def ops_login(request: Request, ...):
    # Login endpoint with rate limiting
```

### **3. Database Migration**

#### **PostgreSQL Setup**
```python
# Update database.py
DATABASE_URL = "postgresql://user:password@localhost/filedb"

# Install psycopg2
pip install psycopg2-binary

# Migration script
import psycopg2
from sqlalchemy import create_engine

def migrate_to_postgresql():
    # Create new database
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    
    # Migrate data from SQLite if needed
    # ... migration logic
```

#### **Backup Strategy**
```bash
# Automated backups
#!/bin/bash
# backup.sh
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
aws s3 cp backup_*.sql s3://your-backup-bucket/
```

### **4. File Storage Strategy**

#### **Cloud Storage (Recommended)**
```python
# AWS S3 Integration
import boto3
from botocore.exceptions import NoCredentialsError

s3_client = boto3.client('s3')

async def upload_to_s3(file, bucket, key):
    try:
        s3_client.upload_fileobj(file, bucket, key)
        return f"https://{bucket}.s3.amazonaws.com/{key}"
    except NoCredentialsError:
        raise HTTPException(500, "AWS credentials not found")

# Update upload endpoint
@app.post("/ops/upload")
async def upload_file(...):
    # Upload to S3 instead of local storage
    s3_key = f"uploads/{file_id}{file_ext}"
    s3_url = await upload_to_s3(file, "your-bucket", s3_key)
    
    # Store S3 URL in database
    db_file.file_path = s3_url
```

### **5. Monitoring & Logging**

#### **Application Monitoring**
```python
# Add logging
import logging
import structlog

logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger()

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0"
    }

# Error tracking
import sentry_sdk
sentry_sdk.init(dsn="your-sentry-dsn")
```

#### **Metrics Collection**
```python
# Prometheus metrics
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

### **6. CI/CD Pipeline**

#### **GitHub Actions**
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python -m pytest test_comprehensive.py

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        run: |
          # Deploy to your cloud provider
          aws ecs update-service --cluster prod --service file-sharing
```

### **7. SSL/HTTPS Configuration**

#### **Nginx Configuration**
```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/ssl/cert.pem;
    ssl_certificate_key /etc/ssl/key.pem;
    
    location / {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # File upload size limit
    client_max_body_size 50M;
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

### **8. Performance Optimization**

#### **Caching Strategy**
```python
# Redis caching
import redis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

redis_client = redis.Redis(host="redis", port=6379, db=0)
FastAPICache.init(RedisBackend(redis_client), prefix="cache")

@app.get("/client/files")
@cache(expire=300)  # Cache for 5 minutes
async def list_files(...):
    # Cached file listing
```

#### **Database Optimization**
```python
# Connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=300
)
```

### **9. Deployment Checklist**

#### **Pre-deployment**
- [ ] Generate strong SECRET_KEY
- [ ] Configure production database
- [ ] Set up SSL certificates
- [ ] Configure email service (SendGrid/SES)
- [ ] Set up monitoring (Sentry, DataDog)
- [ ] Configure backup strategy
- [ ] Set up CDN for file delivery
- [ ] Configure rate limiting
- [ ] Set up log aggregation

#### **Post-deployment**
- [ ] Run security scan
- [ ] Test all API endpoints
- [ ] Verify SSL/HTTPS
- [ ] Test file upload/download
- [ ] Verify email delivery
- [ ] Check monitoring alerts
- [ ] Validate backup process
- [ ] Performance testing
- [ ] Load testing

### **10. Scaling Strategy**

#### **Horizontal Scaling**
```yaml
# Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: file-sharing-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: file-sharing
  template:
    metadata:
      labels:
        app: file-sharing
    spec:
      containers:
      - name: app
        image: your-registry/file-sharing:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
```

#### **Auto-scaling**
```bash
# AWS Auto Scaling
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name file-sharing-asg \
  --min-size 2 \
  --max-size 10 \
  --desired-capacity 3 \
  --target-group-arns arn:aws:elasticloadbalancing:...
```

### **11. Cost Optimization**

#### **Resource Planning**
- **Compute**: Start with 2-4 vCPUs, 4-8GB RAM
- **Database**: RDS t3.medium with Multi-AZ
- **Storage**: S3 with Intelligent Tiering
- **CDN**: CloudFront for global file delivery
- **Monitoring**: Basic CloudWatch + Sentry

#### **Estimated Monthly Costs**
- **AWS t3.medium**: ~$30/month
- **RDS PostgreSQL**: ~$50/month
- **S3 storage (100GB)**: ~$3/month
- **CloudFront**: ~$10/month
- **Total**: ~$100-150/month for small-medium scale

### **12. Security Compliance**

#### **GDPR/Privacy**
```python
# Data deletion endpoint
@app.delete("/admin/user/{user_id}")
async def delete_user_data(user_id: int, admin_user = Depends(get_admin_user)):
    # Delete user and associated files
    # Implement right to be forgotten
```

#### **Audit Logging**
```python
# Audit trail
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    action = Column(String)
    resource = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String)
```

## **Quick Production Deployment Commands**

```bash
# 1. Clone and setup
git clone <your-repo>
cd file-sharing-system

# 2. Configure environment
cp .env.example .env.production
# Edit .env.production with production values

# 3. Deploy with Docker
docker-compose -f docker-compose.prod.yml up -d

# 4. Run migrations
docker-compose exec app python create_ops_user.py

# 5. Set up SSL
certbot --nginx -d yourdomain.com

# 6. Verify deployment
curl https://yourdomain.com/health
```

This production deployment plan ensures:
- **Security**: HTTPS, rate limiting, input validation
- **Scalability**: Horizontal scaling, load balancing
- **Reliability**: Database backups, monitoring, health checks
- **Performance**: Caching, CDN, optimized queries
- **Compliance**: Audit logging, data protection
- **Cost-effective**: Right-sized resources with auto-scaling
