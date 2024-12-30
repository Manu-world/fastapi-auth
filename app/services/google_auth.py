from fastapi import HTTPException
import requests
from app.core.config import settings

GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID

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

