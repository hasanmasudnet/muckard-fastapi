"""
Unified Event Publisher
Routes events to Kafka or RabbitMQ based on event type
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Lazy imports to handle cases where modules might not be available
try:
    from app.services.events.factory import get_event_publisher as get_kafka_publisher
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logger.warning("Kafka publisher not available - Kafka events will be skipped")

try:
    from app.utils.rabbitmq_client import get_rabbitmq_client
    RABBITMQ_AVAILABLE = True
except ImportError:
    RABBITMQ_AVAILABLE = False
    logger.warning("RabbitMQ client not available - RabbitMQ events will be skipped")

# Events that should go to Kafka (event streaming, audit, analytics)
KAFKA_EVENTS = {
    "user.created",
    "user.updated",
    "user.logged_in",
    "onboarding.completed",
    "kraken.key.connected",
    "kraken.key.disconnected",
    "kraken.key.updated",
    "bot.trade.executed",
    "bot.trade.skipped",
    "trade.executed",
}

# Events that should go to RabbitMQ (commands, real-time status, alerts)
RABBITMQ_EVENTS = {
    "bot.start",
    "bot.stop",
    "bot.trigger_trade",
    "bot.started",
    "bot.stopped",
    "bot.error",
    "kraken.key.test.failed",
}


class UnifiedEventPublisher:
    """Unified event publisher that routes to Kafka or RabbitMQ"""
    
    def __init__(self):
        self._kafka_publisher: Optional[Any] = None
        self._rabbitmq_client: Optional[Any] = None
    
    async def _get_kafka_publisher(self):
        """Lazy load Kafka publisher"""
        if not KAFKA_AVAILABLE:
            raise ImportError("Kafka publisher not available")
        if self._kafka_publisher is None:
            try:
                self._kafka_publisher = get_kafka_publisher()
            except Exception as e:
                logger.error(f"Failed to initialize Kafka publisher: {e}", exc_info=True)
                raise
        return self._kafka_publisher
    
    async def _get_rabbitmq_client(self):
        """Lazy load RabbitMQ client"""
        if not RABBITMQ_AVAILABLE:
            raise ImportError("RabbitMQ client not available")
        if self._rabbitmq_client is None:
            self._rabbitmq_client = await get_rabbitmq_client()
        return self._rabbitmq_client
    
    async def publish(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        """
        Publish an event to the appropriate messaging system
        
        Args:
            event_type: Type of event
            event_data: Event data dictionary
            
        Returns:
            bool: True if published successfully, False otherwise
        """
        try:
            if event_type in KAFKA_EVENTS:
                return await self._publish_to_kafka(event_type, event_data)
            elif event_type in RABBITMQ_EVENTS:
                return await self._publish_to_rabbitmq(event_type, event_data)
            else:
                logger.warning(f"Unknown event type: {event_type}, defaulting to Kafka")
                return await self._publish_to_kafka(event_type, event_data)
        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {e}", exc_info=True)
            return False
    
    async def _publish_to_kafka(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        """Publish event to Kafka"""
        try:
            # Check if Kafka is enabled
            try:
                from app.config import settings
                if not getattr(settings, 'KAFKA_ENABLED', True):
                    logger.warning(f"Kafka disabled, skipping {event_type}")
                    return False
            except Exception:
                # If we can't check settings, try to publish anyway
                pass
            
            kafka_publisher = await self._get_kafka_publisher()
            result = await kafka_publisher.publish(event_type, event_data)
            logger.debug(f"Published {event_type} to Kafka: {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to publish {event_type} to Kafka: {e}", exc_info=True)
            # Don't fail the request if Kafka is down - just log the error
            return False
    
    async def _publish_to_rabbitmq(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        """Publish event to RabbitMQ"""
        try:
            rabbitmq = await self._get_rabbitmq_client()
            await rabbitmq.publish(event_type, event_data)
            logger.debug(f"Published {event_type} to RabbitMQ")
            return True
        except Exception as e:
            logger.error(f"Failed to publish {event_type} to RabbitMQ: {e}", exc_info=True)
            return False


# Global instance
_event_publisher: Optional[UnifiedEventPublisher] = None


async def get_unified_event_publisher() -> UnifiedEventPublisher:
    """Get or create unified event publisher instance"""
    global _event_publisher
    if _event_publisher is None:
        _event_publisher = UnifiedEventPublisher()
    return _event_publisher

