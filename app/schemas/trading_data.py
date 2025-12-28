from pydantic import BaseModel
from typing import Dict, Any, List, Optional


class TradingDataResponse(BaseModel):
    pair: str
    price: float
    volume: float
    timestamp: int
    data: Dict[str, Any]


class BalanceResponse(BaseModel):
    currency: str
    balance: float
    available: float


class OHLCData(BaseModel):
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: float


class OHLCResponse(BaseModel):
    pair: str
    interval: int
    data: List[OHLCData]


class TickerData(BaseModel):
    pair: str
    ask: float
    bid: float
    last: float
    volume: float
    high: float
    low: float


class TradingPairsResponse(BaseModel):
    pairs: List[str]

