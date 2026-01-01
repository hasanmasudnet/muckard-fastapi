"""Kafka event publisher implementation"""

from confluent_kafka import Producer
import json
import logging
from typing import Dict, Any
from app.services.events.event_publisher import EventPublisher
from app.config import settings


logger = logging.getLogger(__name__)


class KafkaEventPublisher(EventPublisher):
    """Kafka event publisher using confluent-kafka"""
    
    def __init__(self, config: dict):
        """
        Initialize Kafka producer
        
        Args:
            config: Kafka producer configuration dictionary
        """
        self.producer = Producer(config)
        self.logger = logging.getLogger(__name__)
        self.logger.info("KafkaEventPublisher initialized")
    
    async def publish(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        """
        Publish an event to Kafka
        
        Args:
            event_type: Type of event (e.g., "onboarding.completed")
            event_data: Event data dictionary
            
        Returns:
            bool: True if event queued successfully, False otherwise
        """
        topic = self._get_topic_for_event(event_type)
        message = json.dumps(event_data).encode('utf-8')
        
        try:
            self.producer.produce(
                topic,
                message,
                callback=self._delivery_callback
            )
            # Trigger delivery callbacks
            self.producer.poll(0)
            self.logger.debug(f"Event queued: {event_type} -> {topic}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to publish event {event_type}: {e}", exc_info=True)
            return False
    
    def _get_topic_for_event(self, event_type: str) -> str:
        """
        Map event types to Kafka topics
        
        Args:
            event_type: Type of event
            
        Returns:
            str: Kafka topic name
        """
        topic_map = {
            "onboarding.completed": settings.KAFKA_ONBOARDING_TOPIC,
        }
        return topic_map.get(event_type, "default")
    
    def _delivery_callback(self, err, msg):
        """
        Callback for message delivery confirmation
        
        Args:
            err: Error if delivery failed, None if successful
            msg: Message object
        """
        if err:
            self.logger.error(f"Message delivery failed: {err}")
        else:
            self.logger.info(f"Message delivered to {msg.topic()} [{msg.partition()}]")
    
    def flush(self, timeout: float = 10.0):
        """
        Flush pending messages (call on shutdown)
        
        Args:
            timeout: Maximum time to wait for flush
        """
        try:
            remaining = self.producer.flush(timeout)
            if remaining > 0:
                self.logger.warning(f"{remaining} messages not flushed within timeout")
            else:
                self.logger.info("All messages flushed successfully")
        except Exception as e:
            self.logger.error(f"Error flushing messages: {e}", exc_info=True)

