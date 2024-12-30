# auth_service.py
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from jose import jwt, JWTError

from app.models.user import UserCreate, Token, UserInDB, AuthProvider
from app.models.auth import GoogleAuthRequest
from app.core.auth import AuthHandler
from app.core.config import settings as config_settings
from app.db.config import Database
from app.services.google_auth import verify_google_token

class AuthService:
    def __init__(self):
        self.db = None
    
    async def _get_db(self):
        if self.db is None:
            self.db = await Database.get_db()
        return self.db
    
    async def register_user(self, user: UserCreate) -> UserInDB:
        """Register a new user with email and password."""
        db = await self._get_db()
        
        if await db.users.find_one({"email": user.email}):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        user_dict = user.model_dump()
        user_dict["hashed_password"] = AuthHandler.get_password_hash(user_dict.pop("password"))
        current_time = datetime.utcnow()
        user_dict.update({
            "created_at": current_time,
            "updated_at": current_time
        })
        
        result = await db.users.insert_one(user_dict)
        user_dict["_id"] = str(result.inserted_id)
        
        return UserInDB(**user_dict)
    
    async def login_user(self, email: str, password: str) -> Token:
        """Authenticate user with email and password."""
        db = await self._get_db()
        user = await db.users.find_one({"email": email})
        
        if not user or not AuthHandler.verify_password(password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        return self._create_tokens(str(user["_id"]))
    
    def refresh_user_token(self, refresh_token: str) -> Token:
        """Generate new access and refresh tokens using a valid refresh token."""
        try:
            payload = jwt.decode(
                refresh_token,
                config_settings.JWT_SECRET_KEY,
                algorithms=[config_settings.JWT_ALGORITHM]
            )
            
            if not payload.get("refresh"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid refresh token"
                )
            
            return self._create_tokens(payload.get("sub"))
            
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
    
    async def authenticate_with_google(self, auth_request: GoogleAuthRequest) -> Token:
        """Handle Google Sign-In authentication."""
        token_data = verify_google_token(auth_request.id_token)
        
        user_info = {
            "email": token_data["email"],
            "full_name": token_data.get("name"),
            "provider_user_id": token_data["sub"],
            "profile_picture": token_data.get("picture"),
        }
        
        db = await self._get_db()
        user = await db.users.find_one({
            "email": user_info["email"],
            "auth_provider": AuthProvider.GOOGLE
        })
        
        current_time = datetime.utcnow()
        
        if not user:
            user_info.update({
                "is_active": True,
                "is_verified": True,
                "auth_provider": AuthProvider.GOOGLE,
                "created_at": current_time,
                "updated_at": current_time,
                "last_login": current_time
            })
            
            result = await db.users.insert_one(user_info)
            user_id = str(result.inserted_id)
        else:
            await db.users.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "last_login": current_time,
                        "full_name": user_info["full_name"],
                        "profile_picture": user_info["profile_picture"],
                        "updated_at": current_time
                    }
                }
            )
            user_id = str(user["_id"])
        
        return self._create_tokens(user_id)
    
    def _create_tokens(self, user_id: str) -> Token:
        """Create access and refresh tokens for a user."""
        access_token = AuthHandler.create_token(
            data={"sub": user_id},
            expires_delta=timedelta(minutes=config_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token = AuthHandler.create_token(
            data={"sub": user_id, "refresh": True},
            expires_delta=timedelta(days=config_settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        )
        
        return Token(access_token=access_token, refresh_token=refresh_token)