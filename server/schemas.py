from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SignupRequest(BaseModel):
    real_name: str
    nickname: str
    email: str
    phone_number: str
    password: str
    password_confirm: str


class LoginRequest(BaseModel):
    email: str
    password: str


class VerifyPhoneRequest(BaseModel):
    phone_number: str
    code: str


class ForgotPasswordRequest(BaseModel):
    email: str


class UserResponse(BaseModel):
    id: int
    real_name: str
    nickname: str
    email: str
    phone_number: str
    profile_image_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    real_name: Optional[str] = None
    nickname: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class HistoryResponse(BaseModel):
    id: int
    title: str
    file_type: str
    file_url: str
    created_at: datetime

    class Config:
        from_attributes = True
