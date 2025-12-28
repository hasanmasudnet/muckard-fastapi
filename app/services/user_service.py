from sqlalchemy.orm import Session
from datetime import datetime, timezone
from fastapi import HTTPException, status
import uuid
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.utils.security import verify_password, get_password_hash


class UserService:
    """User Management Service"""
    
    def __init__(self, db: Session):
        self.db = db

    async def get_user_profile(self, user_id: uuid.UUID) -> UserResponse:
        """Get user profile"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return UserResponse.model_validate(user)

    async def update_user_profile(self, user_id: uuid.UUID, user_data: UserUpdate) -> UserResponse:
        """Update user profile"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if user_data.name is not None:
            user.name = user_data.name
        if user_data.email is not None:
            # Check if email already exists
            existing = self.db.query(User).filter(
                User.email == user_data.email,
                User.id != user_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
            user.email = user_data.email

        self.db.commit()
        self.db.refresh(user)
        return UserResponse.model_validate(user)

    async def change_password(self, user_id: uuid.UUID, old_password: str, new_password: str) -> dict:
        """Change user password"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if not verify_password(old_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password"
            )

        user.hashed_password = get_password_hash(new_password)
        self.db.commit()
        return {"message": "Password changed successfully"}

