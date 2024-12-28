# # requirements.txt
# fastapi==0.104.1
# pymongo==4.6.0
# python-jose[cryptography]==3.3.0
# passlib[bcrypt]==1.7.4
# python-multipart==0.0.6
# pydantic[email]==2.4.2
# python-dotenv==1.0.0
# motor==3.3.1

# # config.py
# from pydantic_settings import BaseSettings
# from typing import Optional

# class Settings(BaseSettings):
#     MONGODB_URL: str
#     JWT_SECRET_KEY: str
#     JWT_ALGORITHM: str = "HS256"
#     ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
#     REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
#     # For future social auth
#     GOOGLE_CLIENT_ID: Optional[str] = None
#     GOOGLE_CLIENT_SECRET: Optional[str] = None
#     APPLE_CLIENT_ID: Optional[str] = None
#     APPLE_TEAM_ID: Optional[str] = None
#     APPLE_KEY_ID: Optional[str] = None
#     APPLE_PRIVATE_KEY: Optional[str] = None

#     class Config:
#         env_file = ".env"

# settings = Settings()

# models.py
# from pydantic import BaseModel, EmailStr, Field
# from typing import Optional, List
# from datetime import datetime
# from enum import Enum

# class AuthProvider(str, Enum):
#     LOCAL = "local"
#     GOOGLE = "google"
#     APPLE = "apple"

# class UserBase(BaseModel):
#     email: EmailStr
#     full_name: str
#     auth_provider: AuthProvider = AuthProvider.LOCAL
    
# class UserCreate(UserBase):
#     password: str

# class UserUpdate(BaseModel):
#     full_name: Optional[str] = None
#     email: Optional[EmailStr] = None
    
# class UserInDB(UserBase):
#     id: str = Field(alias="_id")
#     hashed_password: Optional[str] = None
#     is_active: bool = True
#     is_verified: bool = False
#     created_at: datetime
#     updated_at: datetime
#     last_login: Optional[datetime] = None
    
# class Token(BaseModel):
#     access_token: str
#     refresh_token: str
#     token_type: str = "bearer"

# database.py
# from motor.motor_asyncio import AsyncIOMotorClient
# from pymongo import IndexModel, ASCENDING
# from datetime import datetime
# from config import settings

# class Database:
#     client: AsyncIOMotorClient = None
    
#     @classmethod
#     async def connect_db(cls):
#         cls.client = AsyncIOMotorClient(settings.MONGODB_URL)
        
#         # Create indexes
#         db = cls.client.flight_tracker
#         await db.users.create_indexes([
#             IndexModel([("email", ASCENDING)], unique=True),
#             IndexModel([("auth_provider", ASCENDING)]),
#         ])
    
#     @classmethod
#     async def close_db(cls):
#         if cls.client:
#             await cls.client.close()
    
#     @classmethod
#     async def get_db(cls):
#         if not cls.client:
#             await cls.connect_db()
#         return cls.client.flight_tracker

# # auth.py
# from datetime import datetime, timedelta
# from typing import Optional
# from fastapi import Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer
# from jose import JWTError, jwt
# from passlib.context import CryptContext
# from models import UserInDB
# from database import Database
# from bson import ObjectId

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# class AuthHandler:
#     @staticmethod
#     def verify_password(plain_password: str, hashed_password: str) -> bool:
#         return pwd_context.verify(plain_password, hashed_password)

#     @staticmethod
#     def get_password_hash(password: str) -> str:
#         return pwd_context.hash(password)

#     @staticmethod
#     def create_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
#         to_encode = data.copy()
#         if expires_delta:
#             expire = datetime.utcnow() + expires_delta
#         else:
#             expire = datetime.utcnow() + timedelta(minutes=15)
#         to_encode.update({"exp": expire})
#         return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

#     @staticmethod
#     async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
#         credentials_exception = HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Could not validate credentials",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#         try:
#             payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
#             user_id: str = payload.get("sub")
#             if user_id is None:
#                 raise credentials_exception
#         except JWTError:
#             raise credentials_exception

#         db = await Database.get_db()
#         user = await db.users.find_one({"_id": ObjectId(user_id)})
#         if user is None:
#             raise credentials_exception
#         return UserInDB(**user)

# # routes/auth.py
# from fastapi import APIRouter, Depends, HTTPException, status
# from datetime import datetime, timedelta
# from models import UserCreate, Token, UserInDB, UserUpdate
# from database import Database
# from auth import AuthHandler
# from bson import ObjectId

# router = APIRouter(prefix="/auth", tags=["auth"])

# @router.post("/register", response_model=UserInDB)
# async def register(user: UserCreate):
#     db = await Database.get_db()
    
#     # Check if user exists
#     if await db.users.find_one({"email": user.email}):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Email already registered"
#         )
    
#     # Create user
#     user_dict = user.model_dump()
#     user_dict["hashed_password"] = AuthHandler.get_password_hash(user_dict.pop("password"))
#     user_dict["created_at"] = datetime.utcnow()
#     user_dict["updated_at"] = user_dict["created_at"]
    
#     result = await db.users.insert_one(user_dict)
#     user_dict["_id"] = result.inserted_id
    
#     return UserInDB(**user_dict)

# @router.post("/login", response_model=Token)
# async def login(email: str, password: str):
#     db = await Database.get_db()
#     user = await db.users.find_one({"email": email})
    
#     if not user or not AuthHandler.verify_password(password, user["hashed_password"]):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect email or password"
#         )
    
#     # Update last login
#     await db.users.update_one(
#         {"_id": user["_id"]},
#         {"$set": {"last_login": datetime.utcnow()}}
#     )
    
#     # Create tokens
#     access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#     refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
#     access_token = AuthHandler.create_token(
#         data={"sub": str(user["_id"])},
#         expires_delta=access_token_expires
#     )
#     refresh_token = AuthHandler.create_token(
#         data={"sub": str(user["_id"]), "refresh": True},
#         expires_delta=refresh_token_expires
#     )
    
#     return Token(access_token=access_token, refresh_token=refresh_token)

# @router.post("/refresh", response_model=Token)
# async def refresh_token(refresh_token: str):
#     try:
#         payload = jwt.decode(
#             refresh_token, settings.JWT_SECRET_KEY,
#             algorithms=[settings.JWT_ALGORITHM]
#         )
#         if not payload.get("refresh"):
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Invalid refresh token"
#             )
#         user_id = payload.get("sub")
#     except JWTError:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid refresh token"
#         )
    
#     # Create new tokens
#     access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#     refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
#     access_token = AuthHandler.create_token(
#         data={"sub": user_id},
#         expires_delta=access_token_expires
#     )
#     new_refresh_token = AuthHandler.create_token(
#         data={"sub": user_id, "refresh": True},
#         expires_delta=refresh_token_expires
#     )
    
#     return Token(access_token=access_token, refresh_token=new_refresh_token)

# @router.get("/me", response_model=UserInDB)
# async def get_current_user(current_user: UserInDB = Depends(AuthHandler.get_current_user)):
#     return current_user

# @router.put("/me", response_model=UserInDB)
# async def update_user(
#     user_update: UserUpdate,
#     current_user: UserInDB = Depends(AuthHandler.get_current_user)
# ):
#     db = await Database.get_db()
#     update_data = user_update.model_dump(exclude_unset=True)
    
#     if update_data:
#         update_data["updated_at"] = datetime.utcnow()
#         await db.users.update_one(
#             {"_id": ObjectId(current_user.id)},
#             {"$set": update_data}
#         )
    
#     updated_user = await db.users.find_one({"_id": ObjectId(current_user.id)})
#     return UserInDB(**updated_user)

# main.py
# Standard library imports
import asyncio
import logging
import sys

# Third-party imports
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore

# Local application imports

from app.db.config import Database
from app.core.config import settings
from app.routes.index import router as index_route

# Configure logging
logger = logging.getLogger(__name__)

# Configure scheduler
jobstores = {"default": MemoryJobStore()}
scheduler = AsyncIOScheduler(jobstores=jobstores, timezone="Africa/Accra")

router = APIRouter()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle events"""
    try:
        # Startup logic
        mongodb = await Database.connect_db()
        if not mongodb:
            logger.error("MongoDB connection failed. Exiting the app.")
            sys.exit(1)

        scheduler.start()
        yield  # Run the application
        
    finally:
        # Shutdown logic
        scheduler.shutdown()
        await Database.close_db()
        

# Initialize FastAPI app with configuration
app = FastAPI(
    lifespan=lifespan,
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="BoardAndGo flight Agent Authentication",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@scheduler.scheduled_job('cron', day_of_week='mon', hour=9, minute=0)
async def schedule():
    pass

@router.get("/")
def root():
    try:
        return {"message": "Welcome to BoardAndGo flight Agent Services"}
    except Exception as e:
        logger.error(f"App is not running: {e}")
        return {"message": "Service is not available"}
    
# Include API routes
app.include_router(router)
app.include_router(index_route, prefix=settings.API_V1_STR)


