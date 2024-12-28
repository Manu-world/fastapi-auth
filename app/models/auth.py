from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class GoogleAuthRequest(BaseModel):
    code: str
    
class SocialProfile(BaseModel):
    provider_user_id: str
    email: EmailStr
    full_name: str
    picture: Optional[str] = None
