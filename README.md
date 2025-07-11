# 🔒 Secure File Sharing System

A production-ready secure file-sharing system built with **FastAPI** that supports two types of users: **Operations Users** and **Client Users**. Features encrypted download URLs, email verification, JWT authentication, and comprehensive security measures.

## 🎯 Assignment Requirements Compliance

This system fulfills all assignment requirements:

### ✅ User 1: Operations User
- **Login**: Secure JWT-based authentication
- **Upload Files**: Restricted to `.pptx`, `.docx`, `.xlsx` files only
- **File Validation**: Automatic type and size validation

### ✅ User 2: Client User  
- **Sign Up**: Registration with encrypted verification URL
- **Email Verification**: Secure email verification via encrypted tokens
- **Login**: JWT-based authentication with email verification requirement
- **List Files**: View all uploaded files
- **Download Files**: Get secure encrypted download links
- **Secure Download**: Time-limited, one-time use encrypted URLs

### ✅ Security Features
- **Encrypted Download URLs**: Secure, tamper-proof download links
- **Client-Only Access**: Download URLs only accessible by client users
- **Access Control**: Non-client users are denied access to download URLs
- **Time-Limited**: Download tokens expire after 1 hour
- **One-Time Use**: Tokens invalidated after single use

## 🚀 Tech Stack

### **Backend Framework**
- **FastAPI** - Modern, fast web framework for building APIs
- **Python 3.11+** - Programming language
- **Uvicorn** - ASGI server for production deployment

### **Database**
- **PostgreSQL** - Production database (primary)
- **SQLAlchemy** - ORM for database operations
- **Alembic** - Database migrations

### **Authentication & Security**
- **JWT (JSON Web Tokens)** - Stateless authentication
- **BCrypt** - Password hashing
- **python-jose** - JWT token handling
- **Cryptography** - Fernet encryption for download URLs
- **python-decouple** - Environment variable management

### **Email Services**
- **aiosmtplib** - Async SMTP client
- **Jinja2** - Email template rendering
- **email-validator** - Email validation

### **File Handling**
- **aiofiles** - Async file operations
- **python-multipart** - File upload handling

### **Production & Monitoring**
- **Docker** - Containerization
- **Nginx** - Reverse proxy and load balancer
- **Redis** - Caching and session storage
- **Gunicorn** - WSGI server for production
- **Prometheus** - Metrics collection
- **Sentry** - Error tracking and monitoring

### **Development & Testing**
- **pytest** - Testing framework
- **structlog** - Structured logging

## 🌟 Key Features

### 🔐 **Security Features**
- **JWT Authentication** with secure token generation
- **BCrypt Password Hashing** with salt
- **Email Verification** required for client users
- **Encrypted Download URLs** using Fernet symmetric encryption
- **Time-Limited Tokens** (1 hour expiration)
- **One-Time Use Tokens** (invalidated after download)
- **File Type Validation** (only .pptx, .docx, .xlsx allowed)
- **File Size Limits** (configurable, default 50MB)
- **User Type Separation** (ops vs client users)
- **CORS Protection** with configurable origins
- **Rate Limiting** for API endpoints
- **HTTPS/SSL Support** with automatic redirect

### 📁 **File Management**
- **Secure File Upload** with unique file identifiers
- **File Type Validation** with whitelist approach
- **File Size Limits** to prevent abuse
- **Metadata Storage** with upload tracking
- **Async File Operations** for better performance

### 📧 **Email System**
- **HTML Email Templates** with Jinja2
- **Async Email Sending** for better performance
- **Email Verification** with secure tokens
- **SMTP Configuration** for various providers
- **Email Delivery Status** tracking

### 🔍 **Monitoring & Logging**
- **Health Check Endpoints** for load balancers
- **Structured Logging** with configurable levels
- **Error Tracking** with Sentry integration
- **Metrics Collection** with Prometheus
- **Database Connection Monitoring**

## 🛠️ Installation & Setup

### **Prerequisites**
- Python 3.11+
- PostgreSQL (for production)
- Docker & Docker Compose (for containerized deployment)
- SMTP credentials (Gmail/SendGrid/etc.)

### **🚀 Quick Start (Recommended)**

1. **Clone the repository**:
```bash
git clone <repository-url>
cd EZ
```

2. **Set up environment**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Run with Docker (Production)**:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

4. **Create operations user**:
```bash
docker-compose exec app python create_ops_user.py
```

5. **Access the application**:
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### **🔧 Local Development Setup**

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure environment variables** (`.env` file):
```bash
# Database
DATABASE_URL=postgresql://fileuser:filepassword@localhost:5432/filedb

# Security
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com

# File Upload
UPLOAD_DIRECTORY=uploads
MAX_FILE_SIZE=52428800  # 50MB
ALLOWED_EXTENSIONS=.pptx,.docx,.xlsx

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

3. **Set up database**:
```bash
# For PostgreSQL
createdb filedb
```

4. **Create operations user**:
```bash
python create_ops_user.py
```

5. **Run the development server**:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### **🐳 Docker Deployment**

#### **Development Environment**
```bash
# Start services
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop services
docker-compose -f docker-compose.dev.yml down
```

#### **Production Environment**
```bash
# Deploy to production
docker-compose -f docker-compose.prod.yml up -d

# Scale application
docker-compose -f docker-compose.prod.yml up -d --scale app=3

# Monitor services
docker-compose -f docker-compose.prod.yml ps
```

## 📚 API Documentation

### **Operations User Endpoints**

#### **1. Login**
```http
POST /ops/login
Content-Type: application/json

{
  "username": "ops_admin",
  "password": "ops123456"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### **2. Upload File**
```http
POST /ops/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <binary-file-data>
```

**Response:**
```json
{
  "id": 1,
  "filename": "uuid-generated-name.docx",
  "original_filename": "document.docx",
  "file_size": 1024000,
  "file_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "uploaded_at": "2025-07-11T10:30:00Z",
  "uploader": {
    "id": 1,
    "username": "ops_admin",
    "email": "ops@example.com"
  }
}
```

### **Client User Endpoints**

#### **1. Sign Up**
```http
POST /client/signup
Content-Type: application/json

{
  "username": "client1",
  "email": "client@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "message": "User created successfully. Please check your email for verification.",
  "user_id": 2,
  "verification_url": "/verify-email?token=<encrypted-token>"
}
```

#### **2. Email Verification**
```http
GET /verify-email?token=<verification_token>
```

**Response:**
```json
{
  "message": "Email verified successfully. You can now login."
}
```

#### **3. Login**
```http
POST /client/login
Content-Type: application/json

{
  "username": "client1",
  "password": "password123"
}
```

#### **4. List Files**
```http
GET /client/files
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": 1,
    "filename": "uuid-generated-name.docx",
    "original_filename": "document.docx",
    "file_size": 1024000,
    "file_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "uploaded_at": "2025-07-11T10:30:00Z",
    "uploader": {
      "id": 1,
      "username": "ops_admin",
      "email": "ops@example.com"
    }
  }
]
```

#### **5. Get Download Link**
```http
GET /client/download-file/{file_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "download_link": "http://localhost:8000/download-file/gAAAAABhO2K8...",
  "message": "success"
}
```

#### **6. Download File**
```http
GET /download-file/{encrypted_token}
```

**Response:** Binary file download

### **System Endpoints**

#### **Health Check**
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-07-11T10:30:00Z",
  "version": "1.0.0",
  "database": "connected",
  "upload_directory": "available",
  "environment": "production"
}
```

## 🔐 Security Implementation

### **Download URL Security**
1. **Fernet Encryption**: URLs encrypted with unique keys
2. **Time-Limited**: Tokens expire after 1 hour
3. **One-Time Use**: Tokens invalidated after download
4. **User-Specific**: Tokens tied to specific users
5. **Tamper-Proof**: URLs cannot be modified without detection

### **Authentication Security**
1. **JWT Tokens**: Stateless, secure authentication
2. **Password Hashing**: BCrypt with salt rounds
3. **Email Verification**: Required for client users
4. **Token Expiration**: Access tokens expire after 30 minutes

### **File Upload Security**
1. **Type Validation**: Whitelist approach for file types
2. **Size Limits**: Configurable maximum file size
3. **User Authorization**: Only ops users can upload
4. **Secure Storage**: Files stored with UUID identifiers

## 🧪 Testing

### **Run Tests**
```bash
# Run all tests
python -m pytest test_comprehensive.py -v

# Run specific test categories
python -m pytest test_comprehensive.py::test_ops_user_login -v
python -m pytest test_comprehensive.py::test_file_upload -v
python -m pytest test_comprehensive.py::test_client_signup -v
```

### **Test Coverage**
- ✅ Operations user authentication
- ✅ File upload validation
- ✅ Client user registration
- ✅ Email verification
- ✅ Download URL encryption
- ✅ Security controls
- ✅ Error handling

## 📊 Configuration

### **Environment Variables**
```bash
# Application Security
SECRET_KEY=your-256-bit-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DOWNLOAD_TOKEN_EXPIRE_HOURS=1

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/filedb

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com

# File Upload
UPLOAD_DIRECTORY=uploads
MAX_FILE_SIZE=52428800  # 50MB
ALLOWED_EXTENSIONS=.pptx,.docx,.xlsx

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
ALLOW_CREDENTIALS=true

# Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

## 🚀 Production Deployment

### **Docker Production Deployment**
```bash
# 1. Configure environment
cp .env.example .env.production
# Edit .env.production with production values

# 2. Deploy with Docker
docker-compose -f docker-compose.prod.yml up -d

# 3. Set up SSL certificates
certbot --nginx -d yourdomain.com

# 4. Create operations user
docker-compose exec app python create_ops_user.py

# 5. Verify deployment
curl https://yourdomain.com/health
```

### **Production Checklist**
- [ ] Strong SECRET_KEY generated
- [ ] Production database configured
- [ ] SSL certificates installed
- [ ] Email service configured
- [ ] Monitoring set up
- [ ] Backup strategy implemented
- [ ] Rate limiting configured
- [ ] Log aggregation enabled

## 📁 Project Structure

```
EZ/
├── 📄 Core Application
│   ├── main.py              # FastAPI application
│   ├── database.py          # Database models and connection
│   ├── schemas.py           # Pydantic schemas
│   ├── auth.py              # Authentication utilities
│   └── email_service.py     # Email service
│
├── 🐳 Docker Configuration
│   ├── Dockerfile           # Container image
│   ├── docker-compose.prod.yml # Production stack
│   └── init.sql             # Database initialization
│
├── 🌐 Web Server
│   └── nginx/
│       ├── nginx.conf       # Nginx configuration
│       └── ssl/             # SSL certificates
│
├── 🧪 Testing & Scripts
│   ├── test_comprehensive.py   # Test suite
│   ├── create_ops_user.py     # Ops user creation
│   └── verify_assignment.py   # Assignment verification
│
├── 📋 Configuration
│   ├── .env                 # Environment variables
│   ├── requirements.txt     # Python dependencies
│   └── .gitignore          # Git ignore rules
│
└── 📚 Documentation
    ├── README.md            # This file
    └── PRODUCTION_DEPLOYMENT.md # Deployment guide
```

## 🎯 Default Credentials

### **Operations User**
- **Username**: `ops_admin`
- **Password**: `ops123456`
- **Email**: `ops@example.com`

> ⚠️ **Important**: Change the default password immediately in production!

## 🔗 Quick Links

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics


