import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import uuid
import logging
from datetime import datetime, timezone
from app.models.kraken_key import KrakenKey
from app.schemas.trading_data import TradingDataResponse, BalanceResponse, OHLCResponse, TradingPairsResponse, TickerData
from app.utils.kraken_client import KrakenClient
from app.utils.redis_client import RedisClient
from app.utils.vault_service import VaultService
from utils.rabbitmq_client import get_rabbitmq_client

logger = logging.getLogger(__name__)


class TradingDataService:
    """Trading Data Agent - Service Layer"""
    
    def __init__(self, db: Session):
        self.db = db
        self.redis = RedisClient()
        try:
            self.vault = VaultService()
        except ImportError:
            self.vault = None

    async def _get_active_key(self, user_id: uuid.UUID) -> tuple[KrakenKey, dict]:
        """Get active Kraken key for user"""
        key = self.db.query(KrakenKey).filter(
            KrakenKey.user_id == user_id,
            KrakenKey.is_active == True,
            KrakenKey.connection_status == "connected"
        ).first()

        if not key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active Kraken API key found. Please connect a key first."
            )

        # Retrieve from Vault
        if self.vault:
            try:
                secrets = self.vault.get_secret(key.key_name)
                return key, secrets
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to retrieve API keys: {str(e)}"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Vault service not available"
            )

    async def start_bot(self, user_id: uuid.UUID) -> dict:
        """
        Start bot for user by publishing bot.start command to RabbitMQ
        
        Args:
            user_id: User ID
            
        Returns:
            dict: Success message
        """
        # Get active key
        key, secrets = await self._get_active_key(user_id)
        
        # Publish bot.start command
        try:
            rabbitmq = await get_rabbitmq_client()
            await rabbitmq.publish("bot.start", {
                "user_id": str(user_id),
                "api_key": secrets["api_key"],
                "api_secret": secrets["api_secret"],
                "requested_at": datetime.now(timezone.utc).isoformat(),
            })
            logger.info(f"Published bot.start command for user {user_id}")
            return {
                "status": "started",
                "message": "Bot start command sent successfully",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to publish bot.start command: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to start bot: {str(e)}"
            )

    async def stop_bot(self, user_id: uuid.UUID) -> dict:
        """
        Stop bot for user by publishing bot.stop command to RabbitMQ
        
        Args:
            user_id: User ID
            
        Returns:
            dict: Success message
        """
        # Publish bot.stop command
        try:
            rabbitmq = await get_rabbitmq_client()
            await rabbitmq.publish("bot.stop", {
                "user_id": str(user_id),
                "requested_at": datetime.now(timezone.utc).isoformat(),
            })
            logger.info(f"Published bot.stop command for user {user_id}")
            return {
                "status": "stopped",
                "message": "Bot stop command sent successfully",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to publish bot.stop command: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to stop bot: {str(e)}"
            )

    async def trigger_trade(self, user_id: uuid.UUID) -> dict:
        """
        Trigger manual trade by publishing bot.trigger_trade command to RabbitMQ
        
        Args:
            user_id: User ID
            
        Returns:
            dict: Success message
        """
        # Get active key
        key, secrets = await self._get_active_key(user_id)
        
        # Publish bot.trigger_trade command
        try:
            rabbitmq = await get_rabbitmq_client()
            await rabbitmq.publish("bot.trigger_trade", {
                "user_id": str(user_id),
                "api_key": secrets["api_key"],
                "api_secret": secrets["api_secret"],
                "requested_at": datetime.now(timezone.utc).isoformat(),
            })
            logger.info(f"Published bot.trigger_trade command for user {user_id}")
            return {
                "status": "triggered",
                "message": "Trade trigger command sent successfully",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to publish bot.trigger_trade command: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to trigger trade: {str(e)}"
            )

    async def get_live_data(self, user_id: uuid.UUID, pair: str) -> TradingDataResponse:
        """Get live trading data (cached)"""
        cache_key = f"trading_data:{user_id}:{pair}"
        
        # Check cache
        cached = self.redis.get(cache_key)
        if cached:
            return TradingDataResponse(**cached)

        # Fetch from Kraken
        key, secrets = await self._get_active_key(user_id)
        kraken_client = KrakenClient(secrets["api_key"], secrets["api_secret"])
        
        try:
            ticker = await kraken_client.get_ticker(pair)
            data = TradingDataResponse(
                pair=pair,
                price=ticker.get("price", 0.0),
                volume=ticker.get("volume", 0.0),
                timestamp=int(ticker.get("timestamp", 0)),
                data=ticker
            )
            
            # Cache for 30 seconds
            self.redis.set(cache_key, data.model_dump(), ttl=30)
            return data
        finally:
            await kraken_client.close()

    async def get_available_pairs(self, user_id: uuid.UUID) -> TradingPairsResponse:
        """Get available trading pairs"""
        cache_key = "trading_pairs:all"
        
        # Check cache
        cached = self.redis.get(cache_key)
        if cached:
            return TradingPairsResponse(**cached)

        # Fetch from Kraken
        key, secrets = await self._get_active_key(user_id)
        kraken_client = KrakenClient(secrets["api_key"], secrets["api_secret"])
        
        try:
            pairs = await kraken_client.get_trading_pairs()
            data = TradingPairsResponse(pairs=pairs)
            
            # Cache for 1 hour
            self.redis.set(cache_key, data.model_dump(), ttl=3600)
            return data
        finally:
            await kraken_client.close()

    async def get_balance(self, user_id: uuid.UUID) -> BalanceResponse:
        """Get account balance"""
        cache_key = f"balance:{user_id}"
        
        # Check cache
        cached = self.redis.get(cache_key)
        if cached:
            return BalanceResponse(**cached)

        # Fetch from Kraken
        key, secrets = await self._get_active_key(user_id)
        kraken_client = KrakenClient(secrets["api_key"], secrets["api_secret"])
        
        try:
            balance_data = await kraken_client.get_balance()
            # Assuming USD balance for now
            data = BalanceResponse(
                currency="USD",
                balance=balance_data.get("USD", {}).get("balance", 0.0),
                available=balance_data.get("USD", {}).get("available", 0.0)
            )
            
            # Cache for 1 minute
            self.redis.set(cache_key, data.model_dump(), ttl=60)
            return data
        finally:
            await kraken_client.close()

    async def get_ohlc(self, user_id: uuid.UUID, pair: str, interval: int) -> OHLCResponse:
        """Get OHLC data"""
        cache_key = f"ohlc:{user_id}:{pair}:{interval}"
        
        # Check cache
        cached = self.redis.get(cache_key)
        if cached:
            return OHLCResponse(**cached)

        # Fetch from Kraken
        key, secrets = await self._get_active_key(user_id)
        kraken_client = KrakenClient(secrets["api_key"], secrets["api_secret"])
        
        try:
            ohlc_data = await kraken_client.get_ohlc(pair, interval)
            data = OHLCResponse(
                pair=pair,
                interval=interval,
                data=ohlc_data.get("data", [])
            )
            
            # Cache for 5 minutes
            self.redis.set(cache_key, data.model_dump(), ttl=300)
            return data
        finally:
            await kraken_client.close()

    async def get_ticker(self, user_id: uuid.UUID, pair: str) -> TickerData:
        """Get ticker data"""
        cache_key = f"ticker:{user_id}:{pair}"
        
        # Check cache
        cached = self.redis.get(cache_key)
        if cached:
            return TickerData(**cached)

        # Fetch from Kraken
        key, secrets = await self._get_active_key(user_id)
        kraken_client = KrakenClient(secrets["api_key"], secrets["api_secret"])
        
        try:
            ticker = await kraken_client.get_ticker(pair)
            data = TickerData(
                pair=pair,
                ask=ticker.get("ask", 0.0),
                bid=ticker.get("bid", 0.0),
                last=ticker.get("last", 0.0),
                volume=ticker.get("volume", 0.0),
                high=ticker.get("high", 0.0),
                low=ticker.get("low", 0.0)
            )
            
            # Cache for 30 seconds
            self.redis.set(cache_key, data.model_dump(), ttl=30)
            return data
        finally:
            await kraken_client.close()

