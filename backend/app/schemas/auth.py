from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

import re


class RegisterRequest(BaseModel):
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    password: str = Field(..., min_length=8)
    first_name: str
    last_name: Optional[str] = None
    city: Optional[str] = None

    @model_validator(mode="after")
    def require_phone_or_email(self):
        if not self.phone and not self.email:
            raise ValueError("Phone or email is required")
        if self.phone and not re.fullmatch(r"\+?\d{7,15}", self.phone):
            raise ValueError("Phone must contain 7-15 digits, optionally starting with +")
        return self


class LoginRequest(BaseModel):
    phone: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    phone: str
    email: Optional[str] = None
    first_name: str
    last_name: Optional[str] = None
    role: str
    city: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LogoutRequest(BaseModel):
    refresh_token: str


class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    city: Optional[str] = None


class MessageResponse(BaseModel):
    message: str


class FcmTokenRequest(BaseModel):
    token: str
    device_info: Optional[str] = None


class PasswordResetRequest(BaseModel):
    phone: str


class PasswordResetConfirm(BaseModel):
    phone: str
    code: str
    new_password: str
