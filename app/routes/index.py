from fastapi import APIRouter
from app.routes import auth, users
import logging

logger = logging.getLogger(__name__)

router = APIRouter()



    
# Health check route
@router.get("/health")
def health_check():
    try:
        return {"status": "ok", "message": "BoardAndGo flight Agent Active"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "error", "message": "Service is not available"}

router.include_router(auth.router, prefix="/auth", tags=["authentication"])
router.include_router(users.router, prefix="/users", tags=["users"])