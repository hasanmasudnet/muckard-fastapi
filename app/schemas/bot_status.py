from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
import uuid


class BotStatusResponse(BaseModel):
    id: uuid.UUID
    last_execution_at: Optional[datetime] = None
    execution_status: str
    last_trade_count: int
    next_scheduled_at: Optional[datetime] = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class BotExecutionResponse(BaseModel):
    id: uuid.UUID
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    trade_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class BotHistoryResponse(BaseModel):
    executions: List[BotExecutionResponse]
    total: int


class BotPerformanceResponse(BaseModel):
    total_trades: int
    successful_trades: int
    failed_trades: int
    win_rate: float
    total_volume: float
    average_profit: Optional[float] = None

