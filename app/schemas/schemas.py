from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List, Dict

class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None

class QueryRequest(BaseModel):
    query: str
    context: Optional[Dict] = None
