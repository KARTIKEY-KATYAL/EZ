from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from decouple import config
import secrets
from cryptography.fernet import Fernet
import base64

SECRET_KEY = config('SECRET_KEY')
ALGORITHM = config('ALGORITHM', default='HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = config('ACCESS_TOKEN_EXPIRE_MINUTES', default=30, cast=int)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None

def generate_verification_token():
    return secrets.token_urlsafe(32)

def generate_secure_download_token():
    return secrets.token_urlsafe(64)

def create_encrypted_url(file_id: int, user_id: int, token: str) -> str:
    """Create an encrypted URL for file download"""
    key = Fernet.generate_key()
    cipher_suite = Fernet(key)
    
    # Create data to encrypt
    data = f"{file_id}:{user_id}:{token}"
    encrypted_data = cipher_suite.encrypt(data.encode())
    
    # Store the key in the token (in production, use a more secure method)
    encoded_key = base64.urlsafe_b64encode(key).decode()
    encoded_data = base64.urlsafe_b64encode(encrypted_data).decode()
    
    return f"{encoded_key}:{encoded_data}"

def decrypt_download_url(encrypted_url: str) -> Optional[dict]:
    """Decrypt the download URL and return file_id, user_id, token"""
    try:
        encoded_key, encoded_data = encrypted_url.split(':')
        key = base64.urlsafe_b64decode(encoded_key.encode())
        encrypted_data = base64.urlsafe_b64decode(encoded_data.encode())
        
        cipher_suite = Fernet(key)
        decrypted_data = cipher_suite.decrypt(encrypted_data).decode()
        
        file_id, user_id, token = decrypted_data.split(':')
        return {
            'file_id': int(file_id),
            'user_id': int(user_id),
            'token': token
        }
    except Exception:
        return None
