from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: str
    bio: Optional[str] = None
    avatar: Optional[str] = None
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
