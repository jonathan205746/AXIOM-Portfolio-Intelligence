"""Authentication schemas."""

from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1, max_length=72)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    email: EmailStr
    password: str = Field(..., min_length=12, max_length=72)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str
    user: "UserResponse"


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    code: str = Field(..., pattern=r"^\d{6}$")
    new_password: str = Field(..., min_length=12, max_length=72)


class AccountDeletionRequest(BaseModel):
    password: str = Field(..., min_length=1, max_length=72)


TokenResponse.model_rebuild()


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str


class TokenPayload(BaseModel):
    sub: str
    username: str
    type: Literal["access", "refresh"]
    iat: int
    exp: int
    jti: Optional[str] = None


class RefreshTokenPayload(TokenPayload):
    type: Literal["refresh"] = "refresh"