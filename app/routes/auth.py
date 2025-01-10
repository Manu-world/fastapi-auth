# routes/auth.py
from fastapi import APIRouter
from app.models.auth import AppleAuthRequest, GoogleAuthRequest, LoginRequest
from app.models.user import UserCreate
from app.schema.auth import StandardResponse
from app.services.auth_service import AuthService

router = APIRouter()
auth_service = AuthService()

@router.post("/register", response_model=StandardResponse)
async def register(user: UserCreate):
    """Register a new user with email and password."""
    try:
        user_data = await auth_service.register_user(user)
        return StandardResponse(
            status=True,
            data=user_data,
            message="User registered successfully"
        )
    except Exception as e:
        return StandardResponse(
            status=False,
            message=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=StandardResponse)
async def login(login_request: LoginRequest):
    """Authenticate user with email and password."""
    try:
        token = await auth_service.login_user(login_request.email, login_request.password)
        return StandardResponse(
            status=True,
            data=token,
            message="Login successful"
        )
    except Exception as e:
        return StandardResponse(
            status=False,
            message=f"Login failed: {str(e)}"
        )

@router.post("/refresh", response_model=StandardResponse)
async def refresh_token(refresh_token: str):
    """Generate new access and refresh tokens using a valid refresh token."""
    try:
        token = auth_service.refresh_user_token(refresh_token)
        return StandardResponse(
            status=True,
            data=token,
            message="Tokens refreshed successfully"
        )
    except Exception as e:
        return StandardResponse(
            status=False,
            message=f"Token refresh failed: {str(e)}"
        )

@router.post("/google", response_model=StandardResponse)
async def authenticate_with_google(auth_request: GoogleAuthRequest):
    """Handle Google Sign-In with ID token."""
    try:
        token = await auth_service.authenticate_with_google(auth_request)
        return StandardResponse(
            status=True,
            data=token,
            message="Google authentication successful"
        )
    except Exception as e:
        return StandardResponse(
            status=False,
            message=f"Google authentication failed: {str(e)}"
        )
        
@router.post("/apple", response_model=StandardResponse)
async def authenticate_with_apple(auth_request: AppleAuthRequest):
    try:
        token = await auth_service.authenticate_with_apple(auth_request)
        return StandardResponse(
            status=True,
            data=token,
            message="Apple authentication successful"
        )
    except Exception as e:
        return StandardResponse(
            status=False,
            message=f"Apple authentication failed: {str(e)}"
        )
