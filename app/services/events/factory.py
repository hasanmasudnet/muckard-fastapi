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
    try:
        # Check if Kafka is enabled
        kafka_enabled = getattr(settings, 'KAFKA_ENABLED', True)
        if not kafka_enabled:
            logger.info("Kafka disabled, using NoOpEventPublisher")
            return NoOpEventPublisher()
        
        # Get Kafka settings with defaults
        bootstrap_servers = getattr(settings, 'KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        security_protocol = getattr(settings, 'KAFKA_SECURITY_PROTOCOL', 'PLAINTEXT')
        
        # Build Kafka configuration
        kafka_config = {
            'bootstrap.servers': bootstrap_servers,
            'security.protocol': security_protocol,
        }
        
        # Add SASL authentication if configured
        sasl_mechanism = getattr(settings, 'KAFKA_SASL_MECHANISM', '')
        if sasl_mechanism:
            kafka_config.update({
                'sasl.mechanism': sasl_mechanism,
                'sasl.username': getattr(settings, 'KAFKA_SASL_USERNAME', ''),
                'sasl.password': getattr(settings, 'KAFKA_SASL_PASSWORD', ''),
            })
        
        logger.info(f"Creating KafkaEventPublisher with config: {bootstrap_servers}")
        return KafkaEventPublisher(kafka_config)
    except Exception as e:
        logger.error(f"Failed to create Kafka publisher, using NoOpEventPublisher: {e}", exc_info=True)
        return NoOpEventPublisher()

