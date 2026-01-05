"""Onboarding API endpoints"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
import logging
from database import get_db
from schemas.user import OnboardingData, OnboardingResponse
from services.user_service import UserService
from api.deps import get_current_user
from schemas.user import UserResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=OnboardingResponse, status_code=status.HTTP_200_OK)
async def complete_onboarding(
    onboarding_data: OnboardingData,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Complete user onboarding
    
    Saves onboarding data to database and publishes event to RabbitMQ
    """
    logger.info(f"Onboarding completion request for user: {current_user.id}")
    
    user_service = UserService(db)
    result = await user_service.complete_onboarding(current_user.id, onboarding_data)
    
    logger.info(f"Onboarding completed successfully for user: {current_user.id}")
    return OnboardingResponse(**result)

