from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from fastapi import HTTPException, status
import uuid
from app.models.trade import Trade
from app.models.bot_status import BotStatus
from app.schemas.dashboard import DashboardResponse, DashboardStatsResponse, WinRateResponse, RecentTradeResponse


class DashboardService:
    """Dashboard Service - Aggregates data for user dashboard"""
    
    def __init__(self, db: Session):
        self.db = db

    async def get_dashboard_data(self, user_id: uuid.UUID) -> DashboardResponse:
        """Get all dashboard data"""
        # Get stats
        total_trades = self.db.query(Trade).filter(Trade.user_id == user_id).count()
        active_bots = self.db.query(BotStatus).filter(
            BotStatus.user_id == user_id,
            BotStatus.execution_status == "running"
        ).count()
        
        # Calculate monthly return (placeholder)
        monthly_return = 0.0
        average_profit = 0.0
        
        stats = DashboardStatsResponse(
            total_trades=total_trades,
            active_bots=active_bots,
            monthly_return=monthly_return,
            average_profit=average_profit
        )
        
        # Get win rate
        successful_trades = self.db.query(Trade).filter(
            Trade.user_id == user_id,
            Trade.status == "executed"
        ).count()
        win_rate = (successful_trades / total_trades * 100) if total_trades > 0 else 0.0
        
        win_rate_data = WinRateResponse(
            win_rate=win_rate,
            trend="up",  # TODO: Calculate trend
            period="30d"
        )
        
        # Get recent trades
        recent_trades = self.db.query(Trade).filter(
            Trade.user_id == user_id
        ).order_by(desc(Trade.created_at)).limit(5).all()
        
        recent_trades_data = [
            RecentTradeResponse(
                id=str(t.id),
                pair=t.pair,
                side=t.side,
                amount=t.amount,
                price=t.price,
                executed_at=t.executed_at.isoformat() if t.executed_at else None,
                status=t.status
            )
            for t in recent_trades
        ]
        
        return DashboardResponse(
            stats=stats,
            win_rate=win_rate_data,
            recent_trades=recent_trades_data,
            active_bots_count=active_bots
        )

