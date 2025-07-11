from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class User(BaseModel):
    id: int
    username: str
    email: str
    user_type: str
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class FileUpload(BaseModel):
    filename: str
    file_size: int
    file_type: str

class FileResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    uploaded_at: datetime
    uploader: User

    class Config:
        from_attributes = True

class DownloadResponse(BaseModel):
    download_link: str
    message: str

class EmailVerification(BaseModel):
    token: str
