from fastapi import HTTPException, status
import httpx
from app.models.auth import SocialProfile
from app.core.config import settings
from typing import Tuple, Dict


class GoogleAuthService:
    def __init__(self):
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI
        self.endpoints = settings.GOOGLE_OAUTH_ENDPOINTS

    async def get_oauth_url(self) -> str:
        """Generate the Google OAuth URL for client-side redirect."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "email profile",
            "access_type": "offline",
            "prompt": "consent"
        }
        
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.endpoints['auth_uri']}?{query_string}"

    async def exchange_code_for_token(self, code: str) -> Dict[str, str]:
        """Exchange authorization code for tokens."""
        async with httpx.AsyncClient() as client:
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "redirect_uri": self.redirect_uri,
                "grant_type": "authorization_code"
            }
            
            response = await client.post(self.endpoints["token_uri"], data=data)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange authorization code"
                )
                
            return response.json()

    async def get_user_profile(self, access_token: str) -> SocialProfile:
        """Get user profile information from Google."""
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await client.get(self.endpoints["userinfo_uri"], headers=headers)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user profile"
                )
            
            profile_data = response.json()
            return SocialProfile(
                provider_user_id=profile_data["sub"],
                email=profile_data["email"],
                full_name=profile_data.get("name", ""),
                picture=profile_data.get("picture")
            )
