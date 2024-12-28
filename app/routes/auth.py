# routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timedelta
from app.models.user import UserCreate, Token, UserInDB, UserUpdate
from app.db.config import Database
from app.core.auth import AuthHandler
from bson import ObjectId
from app.core.config import settings as config_settings
from app.services.google_auth import GoogleAuthService
from app.core.auth import AuthHandler
from jose import jwt, JWTError
from app.models.user import AuthProvider
from app.models.auth import GoogleAuthRequest, SocialProfile

router = APIRouter()
google_auth_service = GoogleAuthService()

@router.post("/register", response_model=UserInDB)
async def register(user: UserCreate):
    db = await Database.get_db()
    
    # Check if user exists
    if await db.users.find_one({"email": user.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user_dict = user.model_dump()
    user_dict["hashed_password"] = AuthHandler.get_password_hash(user_dict.pop("password"))
    user_dict["created_at"] = datetime.utcnow()
    user_dict["updated_at"] = user_dict["created_at"]
    
    result = await db.users.insert_one(user_dict)
    user_dict["_id"] = str(result.inserted_id)
    
    return UserInDB(**user_dict)

@router.post("/login", response_model=Token)
async def login(email: str, password: str):
    db = await Database.get_db()
    user = await db.users.find_one({"email": email})
    
    if not user or not AuthHandler.verify_password(password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Update last login
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    # Create tokens
    access_token_expires = timedelta(minutes=config_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=config_settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = AuthHandler.create_token(
        data={"sub": str(user["_id"])},
        expires_delta=access_token_expires
    )
    refresh_token = AuthHandler.create_token(
        data={"sub": str(user["_id"]), "refresh": True},
        expires_delta=refresh_token_expires
    )
    
    return Token(access_token=access_token, refresh_token=refresh_token)

@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    try:
        payload = jwt.decode(
            refresh_token, config_settings.JWT_SECRET_KEY,
            algorithms=[config_settings.JWT_ALGORITHM]
        )
        if not payload.get("refresh"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid refresh token"
            )
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Create new tokens
    access_token_expires = timedelta(minutes=config_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=config_settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = AuthHandler.create_token(
        data={"sub": user_id},
        expires_delta=access_token_expires
    )
    new_refresh_token = AuthHandler.create_token(
        data={"sub": user_id, "refresh": True},
        expires_delta=refresh_token_expires
    )
    
    return Token(access_token=access_token, refresh_token=new_refresh_token)



@router.get("/google/url")
async def google_auth_url():
    """Get the Google OAuth URL for client-side redirect."""
    return {"url": await google_auth_service.get_oauth_url()}

@router.get("/google/callback", response_model=Token)
async def google_callback(auth_request: GoogleAuthRequest):
    """Handle Google OAuth callback and create/login user."""
    try:
        
        print("auth request: ", auth_request)
        # Exchange code for tokens
        tokens = await google_auth_service.exchange_code_for_token(auth_request.code)
        access_token = tokens["access_token"]
        
        # Get user profile from Google
        profile = await google_auth_service.get_user_profile(access_token)
        
        # Get database instance
        db = await Database.get_db()
        
        # Check if user exists
        user = await db.users.find_one({
            "email": profile.email,
            "auth_provider": AuthProvider.GOOGLE
        })
        
        if not user:
            # Create new user
            user = {
                "email": profile.email,
                "full_name": profile.full_name,
                "auth_provider": AuthProvider.GOOGLE,
                "provider_user_id": profile.provider_user_id,
                "is_active": True,
                "is_verified": True,  # Auto-verify Google users
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_login": datetime.utcnow(),
                "profile_picture": profile.picture
            }
            result = await db.users.insert_one(user)
            user["_id"] = result.inserted_id
        else:
            # Update existing user's last login and profile
            await db.users.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "last_login": datetime.utcnow(),
                        "full_name": profile.full_name,
                        "profile_picture": profile.picture,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        
        # Generate JWT tokens
        access_token_expires = timedelta(minutes=config_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=config_settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        
        access_token = AuthHandler.create_token(
            data={"sub": str(user["_id"])},
            expires_delta=access_token_expires
        )
        refresh_token = AuthHandler.create_token(
            data={"sub": str(user["_id"]), "refresh": True},
            expires_delta=refresh_token_expires
        )
        
        return Token(access_token=access_token, refresh_token=refresh_token)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google authentication failed: {str(e)}"
        )