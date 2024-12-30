# routes/user.py
from fastapi import APIRouter, Depends
from app.models.user import UserInDB, UserUpdate
from app.core.auth import AuthHandler
from app.services.user_service import UserService
from app.schema.auth import StandardResponse

router = APIRouter()
user_service = UserService()

@router.get("/me", response_model=StandardResponse)
async def get_current_user(current_user: UserInDB = Depends(AuthHandler.get_current_user)):
    """Get current user profile."""
    try:
        user = await user_service.get_user_by_id(str(current_user.id))
        return StandardResponse(
            status=True,
            data=user,
            message="User profile retrieved successfully"
        )
    except Exception as e:
        return StandardResponse(
            status=False,
            message=f"Failed to retrieve user profile: {str(e)}"
        )

@router.put("/me", response_model=StandardResponse)
async def update_user(
    user_update: UserUpdate,
    current_user: UserInDB = Depends(AuthHandler.get_current_user)
):
    """Update current user profile."""
    try:
        updated_user = await user_service.update_user(
            str(current_user.id),
            user_update
        )
        return StandardResponse(
            status=True,
            data=updated_user,
            message="User profile updated successfully"
        )
    except Exception as e:
        return StandardResponse(
            status=False,
            message=f"Failed to update user profile: {str(e)}"
        )