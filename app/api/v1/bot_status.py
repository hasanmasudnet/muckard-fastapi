from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.bot_status import BotStatusResponse, BotHistoryResponse, BotPerformanceResponse
from app.services.bot_status_service import BotStatusService
from app.api.deps import get_current_user, require_admin
from app.schemas.user import UserResponse

router = APIRouter(prefix="/bot")


@router.get("/status", response_model=BotStatusResponse)
async def get_bot_status(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current bot status"""
    bot_service = BotStatusService(db)
    return await bot_service.get_status(current_user.id)


@router.get("/history", response_model=BotHistoryResponse)
async def get_bot_history(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get bot execution history"""
    bot_service = BotStatusService(db)
    return await bot_service.get_history(current_user.id, limit, offset)


@router.get("/trades")
async def get_bot_trades(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get bot trade history"""
    bot_service = BotStatusService(db)
    return await bot_service.get_trades(current_user.id, limit, offset)


@router.get("/performance", response_model=BotPerformanceResponse)
async def get_bot_performance(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get bot performance metrics"""
    bot_service = BotStatusService(db)
    return await bot_service.get_performance(current_user.id)


@router.post("/start")
async def start_bot(
    current_user: UserResponse = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Manually start bot (admin only)"""
    # TODO: Implement bot start functionality
    return {"message": "Bot start not yet implemented"}


@router.post("/stop")
async def stop_bot(
    current_user: UserResponse = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Stop bot execution (admin only)"""
    # TODO: Implement bot stop functionality
    return {"message": "Bot stop not yet implemented"}

