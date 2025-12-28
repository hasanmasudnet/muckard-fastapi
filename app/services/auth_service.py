from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token
from app.utils.security import verify_password, get_password_hash, create_access_token, create_refresh_token, decode_token
from app.config import settings
import uuid


class AuthService:
    """Authentication Agent - Service Layer"""
    
    def __init__(self, db: Session):
        self.db = db

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

