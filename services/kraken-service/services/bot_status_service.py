import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException, status
from typing import List
import uuid
import logging
from datetime import datetime, timezone
from app.models.bot_status import BotStatus
from app.models.bot_execution import BotExecution
from app.models.trade import Trade
from app.schemas.bot_status import BotStatusResponse, BotExecutionResponse, BotHistoryResponse, BotPerformanceResponse
from utils.rabbitmq_client import get_rabbitmq_client
from app.utils.event_publisher import get_unified_event_publisher

logger = logging.getLogger(__name__)


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

    async def update_status_from_event(self, event_type: str, event_data: dict) -> None:
        """
        Update bot status from RabbitMQ event
        
        Args:
            event_type: Type of event (bot.started, bot.stopped, bot.trade.executed, bot.error)
            event_data: Event data dictionary
        """
        try:
            user_id = uuid.UUID(event_data.get("user_id"))
        except (ValueError, TypeError):
            logger.error(f"Invalid user_id in event {event_type}: {event_data.get('user_id')}")
            return

        bot_status = self.db.query(BotStatus).filter(BotStatus.user_id == user_id).first()
        
        if not bot_status:
            bot_status = BotStatus(user_id=user_id, execution_status="idle")
            self.db.add(bot_status)

        if event_type == "bot.started":
            bot_status.execution_status = "running"
            bot_status.last_execution_at = datetime.fromisoformat(event_data.get("started_at", datetime.now(timezone.utc).isoformat()).replace('Z', '+00:00'))
            logger.info(f"Updated bot status to running for user {user_id}")
            
        elif event_type == "bot.stopped":
            bot_status.execution_status = "stopped"
            stopped_at = event_data.get("stopped_at")
            if stopped_at:
                bot_status.last_execution_at = datetime.fromisoformat(stopped_at.replace('Z', '+00:00'))
            logger.info(f"Updated bot status to stopped for user {user_id}")
            
        elif event_type == "bot.trade.executed":
            # Create trade record
            trade = Trade(
                user_id=user_id,
                kraken_trade_id=event_data.get("trade_id", ""),
                pair=event_data.get("pair", ""),
                side=event_data.get("side", "buy"),
                amount=float(event_data.get("amount", 0.0)),
                price=float(event_data.get("price", 0.0)),
                executed_at=datetime.fromisoformat(event_data.get("executed_at", datetime.now(timezone.utc).isoformat()).replace('Z', '+00:00')),
                status="executed"
            )
            self.db.add(trade)
            
            # Update bot status
            bot_status.last_execution_at = trade.executed_at
            bot_status.last_trade_count += 1
            
            # Publish trade.executed event to Kafka
            try:
                event_publisher = await get_unified_event_publisher()
                await event_publisher.publish("trade.executed", {
                    "user_id": str(user_id),
                    "trade_id": str(trade.id),
                    "kraken_trade_id": event_data.get("trade_id", ""),
                    "pair": event_data.get("pair", ""),
                    "side": event_data.get("side", "buy"),
                    "amount": float(event_data.get("amount", 0.0)),
                    "price": float(event_data.get("price", 0.0)),
                    "executed_at": trade.executed_at.isoformat(),
                    "source": "bot"
                })
                logger.info(f"Published trade.executed event for user {user_id}, trade {trade.id}")
            except Exception as e:
                logger.error(f"Failed to publish trade.executed event: {e}", exc_info=True)
            
            logger.info(f"Created trade record for user {user_id}, trade {trade.id}")
            
        elif event_type == "bot.trade.skipped":
            # Just log for analytics, no database update needed
            logger.info(f"Trade skipped for user {user_id}: {event_data.get('reason', 'unknown')}")
            
        elif event_type == "bot.error":
            # Update bot status to failed
            bot_status.execution_status = "failed"
            logger.error(f"Bot error for user {user_id}: {event_data.get('error', 'unknown error')}")
        
        bot_status.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(bot_status)

    async def initialize_bot_status_for_user(self, user_id: uuid.UUID) -> None:
        """
        Initialize bot status when user is created
        
        Args:
            user_id: User ID
        """
        bot_status = self.db.query(BotStatus).filter(BotStatus.user_id == user_id).first()
        
        if not bot_status:
            bot_status = BotStatus(user_id=user_id, execution_status="idle")
            self.db.add(bot_status)
            self.db.commit()
            logger.info(f"Initialized bot status for user {user_id}")

