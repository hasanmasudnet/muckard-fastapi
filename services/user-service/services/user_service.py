import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from fastapi import HTTPException, status
import uuid
import logging
from models.user import User
from schemas.user import UserResponse, UserUpdate, OnboardingData
from utils.security import verify_password, get_password_hash
from app.utils.event_publisher import get_unified_event_publisher

logger = logging.getLogger(__name__)


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
        
        # Publish user.updated event to Kafka
        updated_fields = []
        if user_data.name is not None:
            updated_fields.append("name")
        if user_data.email is not None:
            updated_fields.append("email")
        
        if updated_fields:
            try:
                event_publisher = await get_unified_event_publisher()
                await event_publisher.publish("user.updated", {
                    "user_id": str(user_id),
                    "updated_fields": updated_fields,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                })
                logger.info(f"Published user.updated event for user {user_id}")
            except Exception as e:
                logger.error(f"Failed to publish user.updated event: {e}", exc_info=True)
        
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
    
    async def complete_onboarding(
        self, 
        user_id: uuid.UUID, 
        onboarding_data: OnboardingData
    ) -> dict:
        """
        Complete user onboarding and publish event to RabbitMQ
        
        Args:
            user_id: User ID
            onboarding_data: Onboarding form data
            
        Returns:
            dict: Success message with completion details
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update user with onboarding data
        user.country = onboarding_data.country
        user.state = onboarding_data.state
        user.experience_level = onboarding_data.experience_level
        user.onboarding_completed = True
        user.onboarding_completed_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(user)
        
        # Publish event to Kafka (onboarding.completed already handled by main app, but keep for consistency)
        try:
            event_publisher = await get_unified_event_publisher()
            await event_publisher.publish("onboarding.completed", {
                "user_id": str(user_id),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "country": onboarding_data.country,
                "state": onboarding_data.state,
                "experience_level": onboarding_data.experience_level,
                "has_kraken_account": onboarding_data.has_kraken_account,
            })
            logger.info(f"Published onboarding.completed event for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to publish onboarding event: {e}", exc_info=True)
        
        return {
            "message": "Onboarding completed successfully",
            "onboarding_completed": True,
            "onboarding_completed_at": user.onboarding_completed_at.isoformat()
        }

