from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class GoogleAuthRequest(BaseModel):
    code: str
class AppleAuthRequest(BaseModel):
    id_token: str
    full_name: Optional[str] = None
    
class SocialProfile(BaseModel):
    provider_user_id: str
    email: EmailStr
    full_name: str
    picture: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str
