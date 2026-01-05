import aio_pika
import json
import logging
import asyncio
from typing import Callable, Optional, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)


class RabbitMQClient:
    """RabbitMQ client for async message publishing and consuming"""
    
    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self._connection_url = self._build_connection_url()
    
    def _build_connection_url(self) -> str:
        """Build RabbitMQ connection URL from settings"""
        user = getattr(settings, 'RABBITMQ_USER', 'guest')
        password = getattr(settings, 'RABBITMQ_PASSWORD', 'guest')
        host = getattr(settings, 'RABBITMQ_HOST', 'localhost')
        port = getattr(settings, 'RABBITMQ_PORT', 5672)
        vhost = getattr(settings, 'RABBITMQ_VHOST', '/')
        
        # URL encode vhost if needed
        if vhost != '/':
            vhost = vhost.replace('/', '%2F')
        
        return f"amqp://{user}:{password}@{host}:{port}{vhost}"
    
    async def connect(self, timeout: float = 5.0):
        """
        Establish connection to RabbitMQ with timeout
        
        Args:
            timeout: Connection timeout in seconds (default: 5.0)
        """
        if self.connection and not self.connection.is_closed:
            return
        
        try:
            # Wrap connection in timeout to prevent hanging
            self.connection = await asyncio.wait_for(
                aio_pika.connect_robust(self._connection_url),
                timeout=timeout
            )
            self.channel = await asyncio.wait_for(
                self.connection.channel(),
                timeout=timeout
            )
            logger.info("Connected to RabbitMQ")
        except asyncio.TimeoutError:
            logger.error(f"Connection to RabbitMQ timed out after {timeout} seconds")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    async def disconnect(self):
        """Close RabbitMQ connection"""
        if self.channel and not self.channel.is_closed:
            await self.channel.close()
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
        logger.info("Disconnected from RabbitMQ")
    
    async def publish(self, queue_name: str, message: Dict[str, Any], durable: bool = True):
        """
        Publish a message to a queue
        
        Args:
            queue_name: Name of the queue
            message: Message data (dict) to publish
            durable: Whether the queue should survive broker restarts
        """
        if not self.connection or self.connection.is_closed:
            await self.connect(timeout=5.0)
        
        try:
            # Declare queue
            queue = await self.channel.declare_queue(queue_name, durable=durable)
            
            # Serialize message
            message_body = json.dumps(message).encode()
            
            # Publish message
            await self.channel.default_exchange.publish(
                aio_pika.Message(message_body),
                routing_key=queue_name
            )
            logger.debug(f"Published message to queue '{queue_name}': {message}")
        except Exception as e:
            logger.error(f"Failed to publish message to queue '{queue_name}': {e}")
            raise
    
    async def consume(self, queue_name: str, callback: Callable, durable: bool = True, auto_ack: bool = False):
        """
        Consume messages from a queue
        
        Args:
            queue_name: Name of the queue
            callback: Async function to handle messages: async def callback(message: dict)
            durable: Whether the queue should survive broker restarts
            auto_ack: Whether to automatically acknowledge messages
        """
        if not self.connection or self.connection.is_closed:
            await self.connect(timeout=5.0)
        
        try:
            # Declare queue
            queue = await self.channel.declare_queue(queue_name, durable=durable)
            
            async def message_handler(message: aio_pika.IncomingMessage):
                async with message.process():
                    try:
                        # Deserialize message
                        message_body = json.loads(message.body.decode())
                        logger.debug(f"Received message from queue '{queue_name}': {message_body}")
                        
                        # Call callback
                        await callback(message_body)
                    except Exception as e:
                        logger.error(f"Error processing message from queue '{queue_name}': {e}")
                        if not auto_ack:
                            # Reject message and requeue
                            await message.nack(requeue=True)
                        raise
            
            # Start consuming
            await queue.consume(message_handler)
            logger.info(f"Started consuming from queue '{queue_name}'")
        except Exception as e:
            logger.error(f"Failed to consume from queue '{queue_name}': {e}")
            raise


# Global instance
_rabbitmq_client: Optional[RabbitMQClient] = None


async def get_rabbitmq_client(timeout: float = 5.0) -> RabbitMQClient:
    """
    Get or create RabbitMQ client instance with timeout
    
    Args:
        timeout: Connection timeout in seconds (default: 5.0)
    """
    global _rabbitmq_client
    if _rabbitmq_client is None:
        _rabbitmq_client = RabbitMQClient()
        await _rabbitmq_client.connect(timeout=timeout)
    return _rabbitmq_client

