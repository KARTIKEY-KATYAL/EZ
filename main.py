from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os
import uuid
import aiofiles
from typing import List, Optional
import mimetypes
import logging
from decouple import config

from database import get_db, User, File as FileModel, DownloadToken
from schemas import (
    UserCreate, UserLogin, User as UserSchema, Token, 
    FileResponse, DownloadResponse, EmailVerification
)
from auth import (
    verify_password, get_password_hash, create_access_token, 
    verify_token, generate_verification_token, generate_secure_download_token,
    create_encrypted_url, decrypt_download_url
)
from email_service import send_verification_email

# Configure logging
logging.basicConfig(
    level=getattr(logging, config('LOG_LEVEL', default='INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Secure File Sharing System", 
    version="1.0.0",
    docs_url="/docs" if config('DEBUG', default=True, cast=bool) else None,
    redoc_url="/redoc" if config('DEBUG', default=True, cast=bool) else None
)

# Production middleware
if config('ENVIRONMENT', default='development') == 'production':
    # HTTPS redirect
    if config('SSL_REDIRECT', default=False, cast=bool):
        app.add_middleware(HTTPSRedirectMiddleware)
    
    # Trusted hosts
    allowed_hosts = config('ALLOWED_HOSTS', default='localhost').split(',')
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

# CORS middleware
cors_origins = config('CORS_ORIGINS', default='http://localhost:3000').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=config('ALLOW_CREDENTIALS', default=True, cast=bool),
    allow_methods=config('ALLOW_METHODS', default='GET,POST,PUT,DELETE').split(','),
    allow_headers=config('ALLOW_HEADERS', default='*').split(','),
)

# Security
security = HTTPBearer()

# Configuration
UPLOAD_DIRECTORY = config('UPLOAD_DIRECTORY', default='uploads')
MAX_FILE_SIZE = config('MAX_FILE_SIZE', default=10485760, cast=int)  # 10MB
ALLOWED_EXTENSIONS = config('ALLOWED_EXTENSIONS', default='.pptx,.docx,.xlsx').split(',')

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

# Dependency to get current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    username = verify_token(token)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

# Dependency to check if user is ops user
async def get_current_ops_user(current_user: User = Depends(get_current_user)):
    if current_user.user_type != 'ops':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Operations users can perform this action"
        )
    return current_user

# Dependency to check if user is client user
async def get_current_client_user(current_user: User = Depends(get_current_user)):
    if current_user.user_type != 'client':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Client users can perform this action"
        )
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before accessing this resource"
        )
    return current_user

@app.post("/ops/login", response_model=Token)
async def ops_login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Login for Operations User"""
    user = db.query(User).filter(User.username == user_credentials.username).first()
    
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.user_type != 'ops':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Operations users only."
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/ops/upload", response_model=FileResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_ops_user),
    db: Session = Depends(get_db)
):
    """Upload file - Only for Operations Users"""
    
    # Check file size
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum limit of {MAX_FILE_SIZE/1024/1024}MB"
        )
    
    # Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    filename = f"{file_id}{file_ext}"
    file_path = os.path.join(UPLOAD_DIRECTORY, filename)
    
    # Save file
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Get file type
    file_type = mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'
    
    # Save to database
    db_file = FileModel(
        filename=filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=file.size,
        file_type=file_type,
        uploaded_by=current_user.id
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    return db_file

@app.post("/client/signup")
async def client_signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """Sign up for Client User"""
    
    # Check if user already exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create user
    verification_token = generate_verification_token()
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        user_type='client',
        verification_token=verification_token,
        is_verified=False
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Send verification email
    email_sent = await send_verification_email(
        user_data.email, 
        user_data.username, 
        verification_token
    )
    
    if not email_sent:
        # Note: In production, you might want to handle this differently
        pass
    
    return {
        "message": "User created successfully. Please check your email for verification.",
        "user_id": db_user.id,
        "verification_url": f"/verify-email?token={verification_token}"
    }

@app.get("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify email for Client User"""
    
    user = db.query(User).filter(User.verification_token == token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    user.is_verified = True
    user.verification_token = None
    db.commit()
    
    return {"message": "Email verified successfully. You can now login."}

@app.post("/client/login", response_model=Token)
async def client_login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Login for Client User"""
    user = db.query(User).filter(User.username == user_credentials.username).first()
    
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.user_type != 'client':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Client users only."
        )
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in"
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/client/files", response_model=List[FileResponse])
async def list_files(current_user: User = Depends(get_current_client_user), db: Session = Depends(get_db)):
    """List all uploaded files - Only for verified Client Users"""
    
    files = db.query(FileModel).all()
    return files

@app.get("/client/download-file/{file_id}", response_model=DownloadResponse)
async def get_download_link(
    file_id: int, 
    current_user: User = Depends(get_current_client_user), 
    db: Session = Depends(get_db)
):
    """Get secure download link for file - Only for verified Client Users"""
    
    # Check if file exists
    file = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Generate secure download token
    download_token = generate_secure_download_token()
    
    # Create download token record
    db_token = DownloadToken(
        token=download_token,
        file_id=file_id,
        user_id=current_user.id,
        expires_at=datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
    )
    db.add(db_token)
    db.commit()
    
    # Create encrypted URL
    encrypted_url = create_encrypted_url(file_id, current_user.id, download_token)
    download_url = f"http://localhost:8000/download-file/{encrypted_url}"
    
    return {
        "download_link": download_url,
        "message": "success"
    }

@app.get("/download-file/{encrypted_token}")
async def download_file(encrypted_token: str, db: Session = Depends(get_db)):
    """Download file using secure encrypted token"""
    
    # Decrypt the token
    decrypted_data = decrypt_download_url(encrypted_token)
    if not decrypted_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid download link"
        )
    
    file_id = decrypted_data['file_id']
    user_id = decrypted_data['user_id']
    token = decrypted_data['token']
    
    # Verify token in database
    db_token = db.query(DownloadToken).filter(
        DownloadToken.token == token,
        DownloadToken.file_id == file_id,
        DownloadToken.user_id == user_id,
        DownloadToken.used == False
    ).first()
    
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download token not found or already used"
        )
    
    # Check if token is expired
    if db_token.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Download link has expired"
        )
    
    # Get file
    file = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Check if file exists on disk
    if not os.path.exists(file.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )
    
    # Mark token as used
    db_token.used = True
    db.commit()
    
    # Return file
    return FileResponse(
        path=file.file_path,
        filename=file.original_filename,
        media_type=file.file_type
    )

# Health check and monitoring endpoints
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint for load balancer and monitoring"""
    try:
        # Check database connection
        db.execute("SELECT 1")
        
        # Check upload directory
        upload_dir_exists = os.path.exists(UPLOAD_DIRECTORY)
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "database": "connected",
            "upload_directory": "available" if upload_dir_exists else "unavailable",
            "environment": config('ENVIRONMENT', default='development')
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )

@app.get("/metrics")
async def metrics():
    """Basic metrics endpoint (extend with Prometheus if needed)"""
    return {
        "uptime": "running",
        "timestamp": datetime.utcnow().isoformat()
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for production logging"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    # Don't expose internal errors in production
    if config('ENVIRONMENT', default='development') == 'production':
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)}
        )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Secure File Sharing System API",
        "version": "1.0.0",
        "endpoints": {
            "ops": {
                "login": "/ops/login",
                "upload": "/ops/upload"
            },
            "client": {
                "signup": "/client/signup",
                "login": "/client/login",
                "files": "/client/files",
                "download": "/client/download-file/{file_id}"
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
