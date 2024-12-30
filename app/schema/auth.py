from typing import Optional, Any
from pydantic import BaseModel

class StandardResponse(BaseModel):
    status: bool
    data: Optional[Any] = None
    message: str