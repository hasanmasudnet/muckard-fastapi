"""
Kafka consumer utility for consuming events from Kafka topics
"""
import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Callable, Optional
from confluent_kafka import Consumer, KafkaError, KafkaException
from app.config import settings

logger = logging.getLogger(__name__)

# Thread pool for running blocking Kafka poll operations
_kafka_thread_pool = ThreadPoolExecutor(max_workers=5, thread_name_prefix="kafka-consumer")


class KafkaEventConsumer:
    """Kafka consumer for event streaming"""
    
    def __init__(self):
        self.consumer: Optional[Consumer] = None
        self.running = False
        self.consume_tasks = []
    
    def _create_consumer(self, group_id: str) -> Consumer:
        """Create a Kafka consumer instance"""
        config = {
            'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
            'group.id': group_id,
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': True,
        }
        
        # Add SASL authentication if configured
        if settings.KAFKA_SASL_MECHANISM:
            config.update({
                'security.protocol': settings.KAFKA_SECURITY_PROTOCOL,
                'sasl.mechanism': settings.KAFKA_SASL_MECHANISM,
                'sasl.username': settings.KAFKA_SASL_USERNAME,
                'sasl.password': settings.KAFKA_SASL_PASSWORD,
            })
        
        return Consumer(config)
    
    async def consume_topic(
        self,
        topic: str,
        handler: Callable[[str, Dict[str, Any]], None],
        group_id: str,
        event_type_filter: Optional[str] = None
    ):
        """
        Consume messages from a Kafka topic
        
        Args:
            topic: Kafka topic name
            handler: Async function to handle messages: async def handler(event_type: str, message: dict)
            group_id: Consumer group ID
            event_type_filter: Optional event type to filter (if None, handles all events in topic)
        """
        consumer = self._create_consumer(group_id)
        
        # Run subscribe in thread pool to avoid blocking (it may fetch metadata)
        loop = asyncio.get_event_loop()
        try:
            await asyncio.wait_for(
                loop.run_in_executor(_kafka_thread_pool, consumer.subscribe, [topic]),
                timeout=2.0
            )
        except asyncio.TimeoutError:
            logger.warning(f"Kafka subscribe() timed out for topic '{topic}', continuing anyway")
        except Exception as e:
            logger.warning(f"Kafka subscribe() failed for topic '{topic}': {e}, continuing anyway")
        
        logger.info(f"Started consuming from Kafka topic '{topic}' (group: {group_id})")
        
        try:
            while self.running:
                # Run blocking poll() in thread pool to avoid blocking event loop
                msg = await loop.run_in_executor(_kafka_thread_pool, consumer.poll, 1.0)
                
                if msg is None:
                    continue
                
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition, continue
                        continue
                    else:
                        logger.error(f"Kafka consumer error: {msg.error()}")
                        continue
                
                try:
                    # Deserialize message
                    message_data = json.loads(msg.value().decode('utf-8'))
                    event_type = message_data.get('event_type') or topic
                    
                    # Filter by event type if specified
                    if event_type_filter and event_type != event_type_filter:
                        continue
                    
                    # Call handler
                    await handler(event_type, message_data)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode Kafka message: {e}")
                except Exception as e:
                    logger.error(f"Error processing Kafka message: {e}", exc_info=True)
                    
        except asyncio.CancelledError:
            logger.info(f"Kafka consumer for topic '{topic}' cancelled")
        except Exception as e:
            logger.error(f"Error consuming from Kafka topic '{topic}': {e}", exc_info=True)
        finally:
            consumer.close()
            logger.info(f"Stopped consuming from Kafka topic '{topic}'")
    
    async def start_consuming(
        self,
        topics: list[tuple[str, Callable, str, Optional[str]]]
    ):
        """
        Start consuming from multiple topics
        
        Args:
            topics: List of tuples (topic, handler, group_id, event_type_filter)
        """
        self.running = True
        
        for topic, handler, group_id, event_type_filter in topics:
            task = asyncio.create_task(
                self.consume_topic(topic, handler, group_id, event_type_filter)
            )
            self.consume_tasks.append(task)
            logger.info(f"Started Kafka consumer task for topic '{topic}'")
    
    async def stop(self):
        """Stop all consumers"""
        self.running = False
        
        # Cancel all consume tasks
        for task in self.consume_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.consume_tasks:
            await asyncio.gather(*self.consume_tasks, return_exceptions=True)
        
        self.consume_tasks = []
        logger.info("Kafka consumers stopped")


# Global instance
_kafka_consumer: Optional[KafkaEventConsumer] = None


async def get_kafka_consumer() -> KafkaEventConsumer:
    """Get or create Kafka consumer instance"""
    global _kafka_consumer
    if _kafka_consumer is None:
        _kafka_consumer = KafkaEventConsumer()
    return _kafka_consumer

