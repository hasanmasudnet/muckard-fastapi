from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
import uuid


class SupportTicketCreate(BaseModel):
    subject: str
    description: str
    priority: str = "medium"  # low, medium, high, urgent


class SupportTicketUpdate(BaseModel):
    status: Optional[str] = None  # open, in_progress, resolved, closed
    priority: Optional[str] = None


class SupportTicketResponse(BaseModel):
    id: uuid.UUID
    subject: str
    description: str
    status: str
    priority: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SupportTicketListResponse(BaseModel):
    tickets: List[SupportTicketResponse]
    total: int
    page: int
    page_size: int


class SupportTicketStatsResponse(BaseModel):
    open: int
    in_progress: int
    resolved: int
    closed: int
    total: int


class SupportTicketRespond(BaseModel):
    response: str

