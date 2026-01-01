from sqlalchemy.orm import Session
from datetime import datetime, timezone
from fastapi import HTTPException, status
import uuid
import logging
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, OnboardingData
from app.utils.security import verify_password, get_password_hash
from app.services.events.factory import get_event_publisher
from app.services.events.event_types import OnboardingCompletedEvent

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
        Complete user onboarding and publish event to Kafka
        
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
        
        # Publish event to Kafka (async, non-blocking)
        try:
            event_publisher = get_event_publisher()
            event = OnboardingCompletedEvent(
                user_id=user_id,
                timestamp=datetime.now(timezone.utc),
                data={
                    "country": onboarding_data.country,
                    "state": onboarding_data.state,
                    "experience_level": onboarding_data.experience_level,
                    "has_kraken_account": onboarding_data.has_kraken_account,
                }
            )
            
            # Publish event (async, doesn't block)
            await event_publisher.publish(
                event_type="onboarding.completed",
                event_data=event.model_dump()
            )
            logger.info(f"Onboarding completed event published for user {user_id}")
        except Exception as e:
            # Log error but don't fail the request
            logger.error(f"Failed to publish onboarding event: {e}", exc_info=True)
        
        return {
            "message": "Onboarding completed successfully",
            "onboarding_completed": True,
            "onboarding_completed_at": user.onboarding_completed_at.isoformat()
        }

