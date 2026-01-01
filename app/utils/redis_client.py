import redis
import json
from typing import Any, Optional
from app.config import settings
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
            # Test connection
            self.client.ping()
            self._connected = True
        except (redis.ConnectionError, redis.TimeoutError, Exception) as e:
            logger.warning(f"Redis not available: {str(e)}. Continuing without Redis cache.")
            self._connected = False
            self.client = None

    def _check_connection(self) -> bool:
        """Check if Redis is connected"""
        if not self._connected or not self.client:
            return False
        try:
            self.client.ping()
            return True
        except:
            self._connected = False
            return False

    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        if not self._check_connection():
            return None
        try:
            value = self.client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
        except Exception as e:
            logger.warning(f"Redis get error: {e}")
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis with optional TTL"""
        if not self._check_connection():
            return False
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            ttl = ttl or settings.CACHE_TTL
            return self.client.setex(key, ttl, value)
        except Exception as e:
            logger.warning(f"Redis set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        if not self._check_connection():
            return False
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.warning(f"Redis delete error: {e}")
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern"""
        if not self._check_connection():
            return 0
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
        except Exception as e:
            logger.warning(f"Redis invalidate_pattern error: {e}")
        return 0

    def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self._check_connection():
            return False
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.warning(f"Redis exists error: {e}")
            return False

