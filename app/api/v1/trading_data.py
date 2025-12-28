from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.trading_data import TradingDataResponse, BalanceResponse, OHLCResponse, TradingPairsResponse, TickerData
from app.services.trading_data_service import TradingDataService
from app.api.deps import get_current_user
from app.schemas.user import UserResponse

router = APIRouter(prefix="/trading-data")


@router.get("/live", response_model=TradingDataResponse)
async def get_live_trading_data(
    pair: str = Query(..., description="Trading pair (e.g., BTC/USD)"),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get live trading data (cached)"""
    trading_service = TradingDataService(db)
    return await trading_service.get_live_data(current_user.id, pair)


@router.get("/pairs", response_model=TradingPairsResponse)
async def get_trading_pairs(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available trading pairs"""
    trading_service = TradingDataService(db)
    return await trading_service.get_available_pairs(current_user.id)


@router.get("/balance", response_model=BalanceResponse)
async def get_account_balance(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get account balance"""
    trading_service = TradingDataService(db)
    return await trading_service.get_balance(current_user.id)


@router.get("/ohlc", response_model=OHLCResponse)
async def get_ohlc_data(
    pair: str = Query(..., description="Trading pair"),
    interval: int = Query(60, description="Interval in minutes"),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get OHLC (Open, High, Low, Close) data"""
    trading_service = TradingDataService(db)
    return await trading_service.get_ohlc(current_user.id, pair, interval)


@router.get("/ticker", response_model=TickerData)
async def get_ticker_data(
    pair: str = Query(..., description="Trading pair"),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get ticker data"""
    trading_service = TradingDataService(db)
    return await trading_service.get_ticker(current_user.id, pair)

