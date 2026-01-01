"""Factory for creating event publisher instances"""

import logging
from app.config import settings
from app.services.events.event_publisher import EventPublisher, NoOpEventPublisher
from app.services.events.kafka_publisher import KafkaEventPublisher


logger = logging.getLogger(__name__)


def get_event_publisher() -> EventPublisher:
    """
    Factory function to create event publisher based on configuration
    
    Returns:
        EventPublisher: Configured event publisher instance
    """
    if not settings.KAFKA_ENABLED:
        logger.info("Kafka disabled, using NoOpEventPublisher")
        return NoOpEventPublisher()
    
    # Build Kafka configuration
    kafka_config = {
        'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
        'security.protocol': settings.KAFKA_SECURITY_PROTOCOL,
    }
    
    # Add SASL authentication if configured
    if settings.KAFKA_SASL_MECHANISM:
        kafka_config.update({
            'sasl.mechanism': settings.KAFKA_SASL_MECHANISM,
            'sasl.username': settings.KAFKA_SASL_USERNAME,
            'sasl.password': settings.KAFKA_SASL_PASSWORD,
        })
    
    logger.info(f"Creating KafkaEventPublisher with config: {settings.KAFKA_BOOTSTRAP_SERVERS}")
    return KafkaEventPublisher(kafka_config)

