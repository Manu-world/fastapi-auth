from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class AuthProvider(str, Enum):
    LOCAL = "local"
    GOOGLE = "google"
    APPLE = "apple"

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    auth_provider: AuthProvider = AuthProvider.LOCAL
    
class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    
class UserInDB(UserBase):
    id: str = Field(alias="_id")
    hashed_password: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"