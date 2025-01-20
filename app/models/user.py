from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import re

class AuthProvider(str, Enum):
    LOCAL = "local"
    GOOGLE = "google"
    APPLE = "apple"

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone_number: Optional[str] = None
    auth_provider: AuthProvider = AuthProvider.LOCAL
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        if v is None:
            return v
        # Remove any spaces, dashes, or parentheses
        phone = re.sub(r'[\s\-\(\)]', '', v)
        # Basic phone number validation: +{country_code}{number} or just {number}
        # Allows for international format (+1234567890) or local format (1234567890)
        if not re.match(r'^\+?[1-9]\d{9,14}$', phone):
            raise ValueError('Invalid phone number format')
        return phone
    
class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        if v is None:
            return v
        phone = re.sub(r'[\s\-\(\)]', '', v)
        if not re.match(r'^\+?[1-9]\d{9,14}$', phone):
            raise ValueError('Invalid phone number format')
        return phone
    
class UserInDB(UserBase):
    id: str = Field(alias="_id")
    hashed_password: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    
class UserVerificationResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: bool
    is_verified: bool
    auth_provider: str
    created_at: datetime
    last_login: Optional[datetime] = None
    
    
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"