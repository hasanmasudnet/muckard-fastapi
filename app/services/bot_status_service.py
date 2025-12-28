from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException, status
from typing import List
import uuid
from app.models.bot_status import BotStatus
from app.models.bot_execution import BotExecution
from app.models.trade import Trade
from app.schemas.bot_status import BotStatusResponse, BotExecutionResponse, BotHistoryResponse, BotPerformanceResponse


class BotStatusService:
    """Bot Status Agent - Service Layer"""
    
    def __init__(self, db: Session):
        self.db = db

    async def get_status(self, user_id: uuid.UUID) -> BotStatusResponse:
        """Get current bot status"""
        bot_status = self.db.query(BotStatus).filter(BotStatus.user_id == user_id).first()
        
        if not bot_status:
            # Create default status
            bot_status = BotStatus(user_id=user_id, execution_status="idle")
            self.db.add(bot_status)
            self.db.commit()
            self.db.refresh(bot_status)
        
        return BotStatusResponse.model_validate(bot_status)

    async def get_history(self, user_id: uuid.UUID, limit: int, offset: int) -> BotHistoryResponse:
        """Get bot execution history"""
        executions = self.db.query(BotExecution).filter(
            BotExecution.user_id == user_id
        ).order_by(desc(BotExecution.started_at)).offset(offset).limit(limit).all()
        
        total = self.db.query(BotExecution).filter(BotExecution.user_id == user_id).count()
        
        return BotHistoryResponse(
            executions=[BotExecutionResponse.model_validate(ex) for ex in executions],
            total=total
        )

    async def get_trades(self, user_id: uuid.UUID, limit: int, offset: int) -> dict:
        """Get bot trade history"""
        trades = self.db.query(Trade).filter(
            Trade.user_id == user_id
        ).order_by(desc(Trade.created_at)).offset(offset).limit(limit).all()
        
        total = self.db.query(Trade).filter(Trade.user_id == user_id).count()
        
        return {
            "trades": trades,
            "total": total,
            "page": offset // limit + 1,
            "page_size": limit
        }

    async def get_performance(self, user_id: uuid.UUID) -> BotPerformanceResponse:
        """Get bot performance metrics"""
        trades = self.db.query(Trade).filter(Trade.user_id == user_id).all()
        
        total_trades = len(trades)
        successful_trades = len([t for t in trades if t.status == "executed"])
        failed_trades = total_trades - successful_trades
        
        win_rate = (successful_trades / total_trades * 100) if total_trades > 0 else 0.0
        total_volume = sum(t.amount * t.price for t in trades if t.status == "executed")
        
        return BotPerformanceResponse(
            total_trades=total_trades,
            successful_trades=successful_trades,
            failed_trades=failed_trades,
            win_rate=win_rate,
            total_volume=total_volume,
            average_profit=None  # TODO: Calculate from trade data
        )

