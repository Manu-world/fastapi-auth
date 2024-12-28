# routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timedelta
from app.models.user import UserCreate, Token, UserInDB, UserUpdate
from app.db.config import Database
from app.core.auth import AuthHandler
from bson import ObjectId

router = APIRouter()

@router.get("/me", response_model=UserInDB)
async def get_current_user(current_user: UserInDB = Depends(AuthHandler.get_current_user)):
    current_user.id = str(current_user.id)
    return current_user

@router.put("/me", response_model=UserInDB)
async def update_user(
    user_update: UserUpdate,
    current_user: UserInDB = Depends(AuthHandler.get_current_user)
):
    
    db = await Database.get_db()
    update_data = user_update.model_dump(exclude_unset=True)
    
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        await db.users.update_one(
            {"_id": ObjectId(current_user.id)},
            {"$set": update_data}
        )
    
    updated_user = await db.users.find_one({"_id": ObjectId(current_user.id)})
    
    # Convert ObjectId to string for the _id field
    updated_user["_id"] = str(updated_user["_id"])  # Ensure _id is a string
    return UserInDB(**updated_user)  # Create UserInDB instance with string _id