"""Event type definitions and schemas"""

from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any
import uuid


class OnboardingCompletedEvent(BaseModel):
    """Event published when user completes onboarding"""
    event_type: str = "onboarding.completed"
    user_id: uuid.UUID
    timestamp: datetime
    data: Dict[str, Any]  # country, state, experience_level, has_kraken_account

