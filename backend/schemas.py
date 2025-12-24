from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    username: str

class UserResponse(BaseModel):
    id: int
    username: str
    message: Optional[str] = None
    
    class Config:
        from_attributes = True

class AuthResponse(BaseModel):
    authenticated: bool
    username: Optional[str] = None
    message: str
