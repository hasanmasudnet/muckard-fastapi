from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
import uuid


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    token: str
    new_password: str


class OTPRequest(BaseModel):
    email: EmailStr
    name: str


class OTPVerify(BaseModel):
    email: EmailStr
    otp_code: str
    name: str
    password: str


class OTPResend(BaseModel):
    email: EmailStr
    name: str


class OnboardingData(BaseModel):
    country: str
    state: str
    experience_level: str
    has_kraken_account: bool


class OnboardingResponse(BaseModel):
    message: str
    onboarding_completed: bool
    onboarding_completed_at: Optional[datetime] = None