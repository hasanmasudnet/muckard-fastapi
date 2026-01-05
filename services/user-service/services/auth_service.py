import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
import logging
from models.user import User
from schemas.user import UserCreate, UserResponse, Token
from utils.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from config import settings
from services.otp_service import OTPService
from app.utils.event_publisher import get_unified_event_publisher
import uuid

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication Agent - Service Layer"""
    
    def __init__(self, db: Session):
        self.db = db
        self.otp_service = OTPService(db)

    async def register_user(self, user_data: UserCreate) -> UserResponse:
        """Register a new user"""
        # Check if user exists
        existing_user = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create new user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            name=user_data.name,
            hashed_password=hashed_password
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        # Publish user.created event to Kafka (non-blocking - don't fail registration if Kafka is down)
        try:
            event_publisher = await get_unified_event_publisher()
            await event_publisher.publish("user.created", {
                "user_id": str(db_user.id),
                "email": db_user.email,
                "name": db_user.name,
                "created_at": db_user.created_at.isoformat()
            })
            logger.info(f"Published user.created event for user {db_user.id}")
        except Exception as e:
            # Log error but don't fail registration - event publishing is non-critical
            logger.warning(f"Failed to publish user.created event (non-critical): {e}")
            # Don't log full traceback for non-critical errors to reduce noise
        
        return UserResponse.model_validate(db_user)

    async def login_user(self, email: str, password: str) -> Token:
        """Login user and return JWT tokens"""
        user = self.db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)
        self.db.commit()

        # Create tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "type": "refresh"}
        )
        
        # Publish user.logged_in event to Kafka
        try:
            event_publisher = await get_unified_event_publisher()
            await event_publisher.publish("user.logged_in", {
                "user_id": str(user.id),
                "email": user.email,
                "login_at": user.last_login_at.isoformat()
            })
            logger.info(f"Published user.logged_in event for user {user.id}")
        except Exception as e:
            logger.error(f"Failed to publish user.logged_in event: {e}")

        return Token(
            access_token=access_token,
            refresh_token=refresh_token
        )

    async def get_current_user(self, token: str) -> UserResponse:
        """Get current user from JWT token"""
        try:
            payload = decode_token(token)
            user_id: str = payload.get("sub")
            token_type: str = payload.get("type")
            
            if user_id is None or token_type != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = self.db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )

        return UserResponse.model_validate(user)

    async def refresh_token(self, refresh_token: str) -> Token:
        """Refresh access token using refresh token"""
        try:
            payload = decode_token(refresh_token)
            token_type: str = payload.get("type")
            
            if token_type != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            user_id: str = payload.get("sub")
            user = self.db.query(User).filter(User.id == user_id).first()
            
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            # Create new tokens
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": str(user.id), "email": user.email},
                expires_delta=access_token_expires
            )
            
            # Optionally rotate refresh token
            new_refresh_token = create_refresh_token(
                data={"sub": str(user.id), "type": "refresh"}
            )
            
            return Token(
                access_token=access_token,
                refresh_token=new_refresh_token
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

    async def logout_user(self, token: str) -> dict:
        """Logout user (invalidate token)"""
        # TODO: Implement token blacklisting in Redis
        return {"message": "Logged out successfully"}

    async def forgot_password(self, email: str) -> dict:
        """Request password reset"""
        # TODO: Implement password reset email sending
        user = self.db.query(User).filter(User.email == email).first()
        if user:
            # Generate reset token and send email (future implementation)
            pass
        return {"message": "If the email exists, a password reset link has been sent"}

    async def reset_password(self, token: str, new_password: str) -> dict:
        """Reset password with token"""
        # TODO: Implement password reset with token validation
        return {"message": "Password reset not yet implemented"}
    
    async def send_otp_for_registration(self, email: str, name: str) -> dict:
        """
        Send OTP email for registration
        
        Args:
            email: User's email address
            name: User's name
            
        Returns:
            dict: Success message
        """
        logger.info(f"[AUTH_SERVICE] send_otp_for_registration called for email: {email}, name: {name}")
        
        # Check if user already exists
        existing_user = self.db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create and send OTP
        otp_record = await self.otp_service.create_otp(email, name)
        logger.info(f"[AUTH_SERVICE] OTP created successfully. OTP ID: {otp_record.id}")
        
        return {"message": "OTP sent to email successfully"}
    
    async def complete_registration_with_otp(
        self, 
        user_data: UserCreate, 
        otp_code: str
    ) -> Token:
        """
        Complete user registration after OTP verification
        
        Args:
            user_data: User registration data
            otp_code: 6-digit OTP code
            
        Returns:
            Token: JWT tokens for authenticated user
        """
        # Verify OTP
        is_valid = await self.otp_service.verify_otp(user_data.email, otp_code)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP code"
            )
        
        # Check if user already exists (double-check)
        existing_user = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            name=user_data.name,
            hashed_password=hashed_password
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        # Publish user.created event to Kafka
        try:
            event_publisher = await get_unified_event_publisher()
            await event_publisher.publish("user.created", {
                "user_id": str(db_user.id),
                "email": db_user.email,
                "name": db_user.name,
                "created_at": db_user.created_at.isoformat()
            })
            logger.info(f"Published user.created event for user {db_user.id}")
        except Exception as e:
            logger.error(f"Failed to publish user.created event: {e}")
        
        # Create tokens for immediate login
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        access_token = create_access_token(
            data={"sub": str(db_user.id), "email": db_user.email},
            expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(
            data={"sub": str(db_user.id), "type": "refresh"}
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token
        )
    
    async def resend_otp(self, email: str, name: str) -> dict:
        """
        Resend OTP code for registration
        
        Args:
            email: User's email address
            name: User's name
            
        Returns:
            dict: Success message
        """
        # Check if user already exists
        existing_user = self.db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Resend OTP
        await self.otp_service.resend_otp(email, name)
        
        return {"message": "OTP resent to email successfully"}

