"""Auth request/response schemas."""
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    refresh_token: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: str = "patient"  # SuperAdmin sets other roles


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    mfa_enabled: bool
    is_active: bool

    class Config:
        from_attributes = True
