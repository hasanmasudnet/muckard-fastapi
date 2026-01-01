from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import logging
from app.database import get_db
from app.schemas.user import UserCreate, UserResponse, Token, TokenRefresh, PasswordResetRequest, PasswordReset, OTPRequest, OTPVerify, OTPResend
from app.services.auth_service import AuthService
from app.api.deps import oauth2_scheme

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    auth_service = AuthService(db)
    return await auth_service.register_user(user_data)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login user and return JWT token"""
    auth_service = AuthService(db)
    return await auth_service.login_user(form_data.username, form_data.password)


@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Logout user (invalidate token)"""
    auth_service = AuthService(db)
    return await auth_service.logout_user(token)


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Get current authenticated user"""
    auth_service = AuthService(db)
    return await auth_service.get_current_user(token)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: Session = Depends(get_db)
):
    """Refresh access token"""
    auth_service = AuthService(db)
    return await auth_service.refresh_token(token_data.refresh_token)


@router.post("/forgot-password")
async def forgot_password(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request password reset"""
    auth_service = AuthService(db)
    return await auth_service.forgot_password(request.email)


@router.post("/reset-password")
async def reset_password(
    request: PasswordReset,
    db: Session = Depends(get_db)
):
    """Reset password with token"""
    auth_service = AuthService(db)
    return await auth_service.reset_password(request.token, request.new_password)


@router.post("/send-otp", status_code=status.HTTP_200_OK)
async def send_otp(
    request: OTPRequest,
    db: Session = Depends(get_db)
):
    """Send OTP code to email for registration"""
    logger.info(f"[SEND_OTP] Received request for email: {request.email}, name: {request.name}")
    try:
        auth_service = AuthService(db)
        result = await auth_service.send_otp_for_registration(request.email, request.name)
        logger.info(f"[SEND_OTP] Successfully processed OTP request for: {request.email}")
        return result
    except Exception as e:
        logger.error(f"[SEND_OTP] Error processing OTP request for {request.email}: {str(e)}", exc_info=True)
        raise


@router.post("/verify-otp", response_model=Token, status_code=status.HTTP_200_OK)
async def verify_otp(
    request: OTPVerify,
    db: Session = Depends(get_db)
):
    """Verify OTP code and complete registration"""
    auth_service = AuthService(db)
    user_data = UserCreate(
        email=request.email,
        name=request.name,
        password=request.password
    )
    return await auth_service.complete_registration_with_otp(user_data, request.otp_code)


@router.post("/resend-otp", status_code=status.HTTP_200_OK)
async def resend_otp(
    request: OTPResend,
    db: Session = Depends(get_db)
):
    """Resend OTP code to email"""
    auth_service = AuthService(db)
    return await auth_service.resend_otp(request.email, request.name)

