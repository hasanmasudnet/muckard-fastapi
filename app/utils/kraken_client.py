import httpx
import logging
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)


def validate_key_mode():
    """Warn if trading keys are used in development"""
    if settings.DEBUG and settings.KRAKEN_KEY_MODE == "trading":
        logger.warning("⚠️  WARNING: Trading keys are enabled in DEBUG mode!")
        logger.warning("   This is dangerous - trading keys should only be used in production")
        logger.warning("   Set KRAKEN_KEY_MODE=readonly for development")


class KrakenClient:
    """Kraken API client wrapper"""
    
    def __init__(self, api_key: str, api_secret: str):
        # Validate key mode on initialization
        validate_key_mode()
        
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = settings.KRAKEN_API_BASE_URL
        self.client = httpx.AsyncClient(timeout=30.0)

    async def test_connection(self) -> Dict[str, Any]:
        """Test API connection"""
        # TODO: Implement actual Kraken API connection test
        # This is a placeholder
        return {"status": "connected", "permissions": ["trading"]}

    async def get_balance(self) -> Dict[str, Any]:
        """Get account balance"""
        # TODO: Implement Kraken API balance fetch
        return {"USD": {"balance": 0.0, "available": 0.0}}

    async def get_ticker(self, pair: str) -> Dict[str, Any]:
        """Get ticker data for a pair"""
        # TODO: Implement Kraken API ticker fetch
        return {"pair": pair, "price": 0.0, "volume": 0.0}

    async def get_ohlc(self, pair: str, interval: int) -> Dict[str, Any]:
        """Get OHLC data"""
        # TODO: Implement Kraken API OHLC fetch
        return {"pair": pair, "interval": interval, "data": []}

    async def get_trading_pairs(self) -> list[str]:
        """Get available trading pairs"""
        # TODO: Implement Kraken API pairs fetch
        return ["BTC/USD", "ETH/USD", "XRP/USD"]

    async def validate_permissions(self) -> Dict[str, Any]:
        """Validate API key permissions"""
        # TODO: Implement permission validation
        # Should check that withdrawal permissions are NOT enabled
        return {"has_withdraw": False, "has_trade": True}

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

