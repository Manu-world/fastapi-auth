# services/user_service.py
from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException, status

from app.models.user import UserInDB, UserUpdate
from app.db.config import Database

class UserService:
    def __init__(self):
        self.db = None
    
    async def _get_db(self):
        if self.db is None:
            self.db = await Database.get_db()
        return self.db
    
    async def get_user_by_id(self, user_id: str) -> UserInDB:
        """Retrieve user by ID."""
        db = await self._get_db()
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user["_id"] = str(user["_id"])
        return UserInDB(**user)
    
    async def update_user(self, user_id: str, user_update: UserUpdate) -> UserInDB:
        """Update user profile."""
        db = await self._get_db()
        
        # Get update data excluding unset fields
        update_data = user_update.model_dump(exclude_unset=True)
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid update data provided"
            )
        
        # Add updated timestamp
        update_data["updated_at"] = datetime.utcnow()
        
        # Perform update
        result = await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Fetch and return updated user
        updated_user = await db.users.find_one({"_id": ObjectId(user_id)})
        updated_user["_id"] = str(updated_user["_id"])
        return UserInDB(**updated_user)
