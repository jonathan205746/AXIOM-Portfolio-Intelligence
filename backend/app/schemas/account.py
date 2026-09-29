"""Account management schemas."""

from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class AccountResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: str


class AccountUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    current_password: Optional[str] = Field(None, min_length=1, max_length=72)
    new_password: Optional[str] = Field(None, min_length=12, max_length=72)


class AccountDeletionRequest(BaseModel):
    password: str = Field(..., min_length=1, max_length=72)
    confirmation: Literal["DELETE"] = "DELETE"


class AccountDeletionResponse(BaseModel):
    message: str
    deleted_at: str