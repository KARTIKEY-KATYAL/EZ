# Secure File Sharing System

A secure file-sharing system built with FastAPI that supports two types of users: Operations Users and Client Users.

## Features

### Operations User (Ops User)
- **Login**: Secure authentication for operations users
- **Upload Files**: Upload files with restrictions (only `.pptx`, `.docx`, `.xlsx` files allowed)
- **File Type Validation**: Automatic validation of file types and sizes

### Client User
- **Sign Up**: Registration with email verification
- **Email Verification**: Secure email verification process
- **Login**: Secure authentication for client users
- **List Files**: View all uploaded files
- **Download Files**: Get secure encrypted download links
- **Secure Download**: Download files using encrypted, time-limited URLs

## Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: BCrypt password hashing
- **Email Verification**: Required for client users
- **Encrypted Download URLs**: Secure, time-limited download links
- **File Type Restrictions**: Only specific file types allowed
- **User Type Separation**: Clear separation between ops and client users
- **Token Expiration**: Download tokens expire after 1 hour
- **One-time Use**: Download tokens can only be used once

## Installation and Setup

### Prerequisites
- Python 3.7+
- Gmail account for email verification (or configure your own SMTP)

### Quick Start

1. **Clone/Download the project**
2. **Run the setup script**:
   ```bash
   python setup_and_run.py
   ```

This will:
- Install all dependencies
- Set up the database
- Create upload directories
- Create a default operations user
- Start the server

### Manual Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment variables** (edit `.env` file):
   ```
   SECRET_KEY=your-secret-key-here
   EMAIL_USER=your-email@gmail.com
   EMAIL_PASSWORD=your-app-password
   EMAIL_FROM=your-email@gmail.com
   ```

3. **Create default operations user**:
   ```bash
   python create_ops_user.py
   ```

4. **Run the server**:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

## API Endpoints

### Operations User Endpoints

#### 1. Login
- **POST** `/ops/login`
- **Body**: `{"username": "ops_admin", "password": "ops123456"}`
- **Response**: `{"access_token": "...", "token_type": "bearer"}`

#### 2. Upload File
- **POST** `/ops/upload`
- **Headers**: `Authorization: Bearer <token>`
- **Body**: Form data with file
- **Allowed Files**: `.pptx`, `.docx`, `.xlsx`
- **Max Size**: 10MB

### Client User Endpoints

#### 1. Sign Up
- **POST** `/client/signup`
- **Body**: `{"username": "client1", "email": "client@example.com", "password": "password123"}`
- **Response**: User created + verification email sent

#### 2. Email Verification
- **GET** `/verify-email?token=<verification_token>`
- **Response**: Email verified successfully

#### 3. Login
- **POST** `/client/login`
- **Body**: `{"username": "client1", "password": "password123"}`
- **Response**: `{"access_token": "...", "token_type": "bearer"}`

#### 4. List Files
- **GET** `/client/files`
- **Headers**: `Authorization: Bearer <token>`
- **Response**: List of all uploaded files

#### 5. Get Download Link
- **GET** `/client/download-file/{file_id}`
- **Headers**: `Authorization: Bearer <token>`
- **Response**: 
  ```json
  {
    "download_link": "http://localhost:8000/download-file/encrypted_token",
    "message": "success"
  }
  ```

#### 6. Download File
- **GET** `/download-file/{encrypted_token}`
- **No authentication required** (security is in the encrypted token)
- **Response**: File download

## Default Users

### Operations User
- **Username**: `ops_admin`
- **Password**: `ops123456`
- **Type**: Operations User

## API Documentation

Once the server is running, you can access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Security Implementation

### Download URL Security
1. **Encryption**: Download URLs are encrypted using Fernet symmetric encryption
2. **Time-limited**: Tokens expire after 1 hour
3. **One-time use**: Tokens are marked as used after download
4. **User-specific**: Tokens are tied to specific users
5. **Tamper-proof**: URLs cannot be modified without detection

### File Upload Security
1. **Type validation**: Only specific file types allowed
2. **Size limits**: Maximum 10MB per file
3. **User authorization**: Only ops users can upload
4. **Secure storage**: Files stored with unique identifiers

### Authentication Security
1. **JWT tokens**: Secure, stateless authentication
2. **Password hashing**: BCrypt with salt
3. **Email verification**: Required for client users
4. **Token expiration**: Access tokens expire after 30 minutes

## File Structure

```
EZ/
├── main.py              # FastAPI application
├── database.py          # Database models and connection
├── schemas.py           # Pydantic models
├── auth.py              # Authentication utilities
├── email_service.py     # Email sending service
├── create_ops_user.py   # Script to create default ops user
├── setup_and_run.py     # Setup and run script
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables
├── file_sharing.db      # SQLite database (created automatically)
└── uploads/             # Directory for uploaded files
```

## Usage Examples

### 1. Operations User Workflow
```bash
# Login as ops user
curl -X POST "http://localhost:8000/ops/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "ops_admin", "password": "ops123456"}'

# Upload file
curl -X POST "http://localhost:8000/ops/upload" \
  -H "Authorization: Bearer <token>" \
  -F "file=@document.docx"
```

### 2. Client User Workflow
```bash
# Sign up
curl -X POST "http://localhost:8000/client/signup" \
  -H "Content-Type: application/json" \
  -d '{"username": "client1", "email": "client@example.com", "password": "password123"}'

# Verify email (check your email for verification link)
curl -X GET "http://localhost:8000/verify-email?token=<verification_token>"

# Login
curl -X POST "http://localhost:8000/client/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "client1", "password": "password123"}'

# List files
curl -X GET "http://localhost:8000/client/files" \
  -H "Authorization: Bearer <token>"

# Get download link
curl -X GET "http://localhost:8000/client/download-file/1" \
  -H "Authorization: Bearer <token>"

# Download file (use the encrypted URL from previous response)
curl -X GET "http://localhost:8000/download-file/<encrypted_token>" \
  --output downloaded_file.docx
```

## Configuration

### Email Configuration
To enable email verification, configure these in your `.env` file:
- `EMAIL_HOST`: SMTP server (default: smtp.gmail.com)
- `EMAIL_PORT`: SMTP port (default: 587)
- `EMAIL_USER`: Your email address
- `EMAIL_PASSWORD`: Your app password (for Gmail)
- `EMAIL_FROM`: From email address

### Security Configuration
- `SECRET_KEY`: JWT secret key (change in production)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time
- `MAX_FILE_SIZE`: Maximum file size in bytes
- `ALLOWED_EXTENSIONS`: Comma-separated list of allowed file extensions

## Production Deployment

For production deployment:

1. **Change security settings**:
   - Generate a strong `SECRET_KEY`
   - Use a production database (PostgreSQL)
   - Configure proper SMTP settings

2. **Use HTTPS**: Ensure all communications are encrypted

3. **Environment variables**: Store sensitive data in environment variables

4. **File storage**: Consider using cloud storage for file uploads

5. **Database**: Use a production database like PostgreSQL

## Troubleshooting

### Common Issues

1. **Email not sending**: Check SMTP configuration in `.env`
2. **File upload fails**: Check file type and size limits
3. **Download link expired**: Links expire after 1 hour
4. **Database errors**: Delete `file_sharing.db` and restart

### Logs
Check the console output for detailed error messages and debugging information.

## License

This project is for educational purposes. Use at your own risk in production environments.
