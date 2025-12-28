from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from app.schemas.user import UserResponse


class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    page_size: int


class SystemStatsResponse(BaseModel):
    total_users: int
    active_users: int
    total_trades: int
    total_bots: int
    system_status: str


class SystemHealthResponse(BaseModel):
    status: str
    services: List[Dict[str, Any]]
    uptime: float


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    logs: List[AuditLogResponse]
    total: int
    page: int
    page_size: int


class RoleResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PermissionResponse(BaseModel):
    id: uuid.UUID
    name: str
    category: str
    description: Optional[str] = None

    model_config = {"from_attributes": True}

