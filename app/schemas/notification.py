from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
import uuid


class NotificationCreate(BaseModel):
    type: str  # info, warning, error, success
    title: str
    message: str


class NotificationResponse(BaseModel):
    id: uuid.UUID
    type: str
    title: str
    message: str
    read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int
    unread_count: int


class NotificationBlastRequest(BaseModel):
    type: str
    title: str
    message: str
    user_ids: Optional[List[uuid.UUID]] = None  # None = all users


class NotificationTemplateResponse(BaseModel):
    id: uuid.UUID
    name: str
    type: str
    title: str
    message: str
    created_at: datetime

    model_config = {"from_attributes": True}

