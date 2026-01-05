import sys
import os
# Add parent directory to path to import from app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
try:
    from app.utils.redis_client import RedisClient
except ImportError:
    # Fallback: create a simple RedisClient wrapper
    import redis
    import json
    from typing import Any, Optional
    from config import settings
    import logging
    
    logger = logging.getLogger(__name__)
    
    class RedisClient:
        """Redis client for caching operations"""
        
        def __init__(self):
            self.client = None
            self._connected = False
            try:
                self.client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2
                )
                self.client.ping()
                self._connected = True
            except Exception as e:
                logger.warning(f"Redis not available: {str(e)}")
                self._connected = False
                self.client = None
        
        def get(self, key: str) -> Optional[Any]:
            if not self._connected or not self.client:
                return None
            try:
                value = self.client.get(key)
                if value:
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return value
            except Exception:
                pass
            return None
        
        def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
            if not self._connected or not self.client:
                return False
            try:
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                ttl = ttl or settings.CACHE_TTL
                return self.client.setex(key, ttl, value)
            except Exception:
                return False
        
        def delete(self, key: str) -> bool:
            if not self._connected or not self.client:
                return False
            try:
                return bool(self.client.delete(key))
            except Exception:
                return False

__all__ = ['RedisClient']

