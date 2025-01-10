from fastapi import HTTPException
import requests
from app.core.config import settings
from jose import jwt

GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID

class SocialAuth:
    @staticmethod
    def verify_google_token(id_token: str):
        """
        Verify Google ID token using Google's token verification API.
        """
        url = "https://oauth2.googleapis.com/tokeninfo"
        response = requests.get(url, params={"id_token": id_token})
        
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        token_data = response.json()
        
        # Ensure the token was issued for your client
        if token_data["aud"] != GOOGLE_CLIENT_ID:
            raise HTTPException(status_code=401, detail="Token is not for this app")
        
        return token_data

    @staticmethod
    def verify_apple_token(id_token: str):
        # Get Apple's public keys
        response = requests.get("https://appleid.apple.com/auth/keys")
        apple_public_keys = response.json()["keys"]

        # Decode and verify the ID Token
        decoded_token = jwt.decode(
            id_token,
            apple_public_keys,
            algorithms=["RS256"],
            audience=settings.BUNDLE_ID_IOS  # Replace with your app's bundle ID
        )
        return decoded_token