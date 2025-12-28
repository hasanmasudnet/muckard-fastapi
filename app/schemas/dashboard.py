from pydantic import BaseModel
from typing import List, Optional


class DashboardStatsResponse(BaseModel):
    total_trades: int
    active_bots: int
    monthly_return: float
    average_profit: float


class WinRateResponse(BaseModel):
    win_rate: float
    trend: str
    period: str


class RecentTradeResponse(BaseModel):
    id: str
    pair: str
    side: str
    amount: float
    price: float
    executed_at: Optional[str] = None
    status: str


class DashboardResponse(BaseModel):
    stats: DashboardStatsResponse
    win_rate: WinRateResponse
    recent_trades: List[RecentTradeResponse]
    active_bots_count: int

