from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid


class KrakenKeyCreate(BaseModel):
    api_key: str
    api_secret: str
    key_name: str


class KrakenKeyUpdate(BaseModel):
    key_name: Optional[str] = None
    is_active: Optional[bool] = None


class KrakenKeyResponse(BaseModel):
    id: uuid.UUID
    key_name: str
    is_active: bool
    connection_status: str
    last_tested_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class KrakenConnectionTest(BaseModel):
    status: str
    tested_at: Optional[datetime] = None
    message: Optional[str] = None

