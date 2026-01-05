import sys
import os
# Add parent directory to path to import from app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
try:
    from app.utils.rabbitmq_client import RabbitMQClient, get_rabbitmq_client
except ImportError:
    # Fallback: import directly
    import aio_pika
    import json
    import logging
    from typing import Callable, Optional, Dict, Any
    from config import settings
    
    logger = logging.getLogger(__name__)
    
    class RabbitMQClient:
        """RabbitMQ client for async message publishing and consuming"""
        
        def __init__(self):
            self.connection: Optional[aio_pika.Connection] = None
            self.channel: Optional[aio_pika.Channel] = None
            self._connection_url = self._build_connection_url()
        
        def _build_connection_url(self) -> str:
            user = getattr(settings, 'RABBITMQ_USER', 'guest')
            password = getattr(settings, 'RABBITMQ_PASSWORD', 'guest')
            host = getattr(settings, 'RABBITMQ_HOST', 'localhost')
            port = getattr(settings, 'RABBITMQ_PORT', 5672)
            vhost = getattr(settings, 'RABBITMQ_VHOST', '/')
            if vhost != '/':
                vhost = vhost.replace('/', '%2F')
            return f"amqp://{user}:{password}@{host}:{port}{vhost}"
        
        async def connect(self):
            if self.connection and not self.connection.is_closed:
                return
            try:
                self.connection = await aio_pika.connect_robust(self._connection_url)
                self.channel = await self.connection.channel()
                logger.info("Connected to RabbitMQ")
            except Exception as e:
                logger.error(f"Failed to connect to RabbitMQ: {e}")
                raise
        
        async def disconnect(self):
            if self.channel and not self.channel.is_closed:
                await self.channel.close()
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
        
        async def publish(self, queue_name: str, message: Dict[str, Any], durable: bool = True):
            if not self.connection or self.connection.is_closed:
                await self.connect()
            try:
                queue = await self.channel.declare_queue(queue_name, durable=durable)
                message_body = json.dumps(message).encode()
                await self.channel.default_exchange.publish(
                    aio_pika.Message(message_body),
                    routing_key=queue_name
                )
            except Exception as e:
                logger.error(f"Failed to publish message: {e}")
                raise
    
    _rabbitmq_client: Optional[RabbitMQClient] = None
    
    async def get_rabbitmq_client() -> RabbitMQClient:
        global _rabbitmq_client
        if _rabbitmq_client is None:
            _rabbitmq_client = RabbitMQClient()
            await _rabbitmq_client.connect()
        return _rabbitmq_client

__all__ = ['RabbitMQClient', 'get_rabbitmq_client']

