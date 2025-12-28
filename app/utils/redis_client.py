import redis
import json
from typing import Any, Optional
from app.config import settings


class RedisClient:
    """Redis client for caching operations"""
    
    def __init__(self):
        self.client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            decode_responses=True
        )

    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        value = self.client.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis with optional TTL"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        ttl = ttl or settings.CACHE_TTL
        return self.client.setex(key, ttl, value)

    def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        return bool(self.client.delete(key))

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern"""
        keys = self.client.keys(pattern)
        if keys:
            return self.client.delete(*keys)
        return 0

    def exists(self, key: str) -> bool:
        """Check if key exists"""
        return bool(self.client.exists(key))

