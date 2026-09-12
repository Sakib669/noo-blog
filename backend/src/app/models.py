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

class UserUpdate(BaseModel):
    """Fields a user may change about their own profile."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    bio:       Optional[str] = Field(None, max_length=500)
    avatar:    Optional[str] = Field(None, max_length=500)
    # All optional → PATCH-style semantics: send only what you want to change.
    # We use PUT for the endpoint (a common-enough convention) but the
    # behaviour is "partial update", which is why every field defaults to None.


class PasswordChange(BaseModel):
    """Request body for changing a password."""
    current_password: str = Field(..., min_length=6)
    new_password:     str = Field(..., min_length=6)
    # Both required. We do NOT enforce complexity rules here — that's a
    # policy decision better made in one place (e.g. a validator).
    # min_length=6 mirrors the register schema so the rules stay consistent.


class PublicUserResponse(BaseModel):
    """
    The shape we return for a public user profile.
    Deliberately excludes email and password — those are private.
    """
    id: str
    username: str
    full_name: str
    bio: Optional[str] = None
    avatar: Optional[str] = None
    created_at: str