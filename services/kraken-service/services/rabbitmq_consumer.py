import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
import asyncio
import logging
from typing import Optional
from sqlalchemy.orm import Session
from database import get_db
from services.bot_status_service import BotStatusService
from utils.rabbitmq_client import RabbitMQClient, get_rabbitmq_client

logger = logging.getLogger(__name__)


class RabbitMQConsumer:
    """RabbitMQ consumer for bot result events"""
    
    def __init__(self):
        self.rabbitmq: Optional[RabbitMQClient] = None
        self.running = False
        self.consume_tasks = []

    async def start(self, timeout: float = 5.0):
        """
        Start consuming messages from RabbitMQ queues with timeout
        
        Args:
            timeout: Connection timeout in seconds (default: 5.0)
        """
        if self.running:
            logger.warning("RabbitMQ consumer is already running")
            return
        
        try:
            # Wrap connection in timeout to prevent hanging
            self.rabbitmq = await asyncio.wait_for(
                get_rabbitmq_client(timeout=timeout),
                timeout=timeout
            )
            self.running = True
            
            # Start consuming from bot result queues (only RabbitMQ events)
            # Note: bot.trade.executed and bot.trade.skipped are now in Kafka
            queues = [
                ("bot.started", self._handle_bot_started),
                ("bot.stopped", self._handle_bot_stopped),
                ("bot.error", self._handle_bot_error),
            ]
            
            for queue_name, handler in queues:
                task = asyncio.create_task(
                    self._consume_queue(queue_name, handler)
                )
                self.consume_tasks.append(task)
                logger.info(f"Started consumer task for queue '{queue_name}'")
            
            logger.info("RabbitMQ consumer started successfully")
        except asyncio.TimeoutError:
            logger.warning(f"RabbitMQ connection timed out after {timeout} seconds. Consumer will retry in background.")
            self.running = True
            # Start consumers in background with retry logic
            queues = [
                ("bot.started", self._handle_bot_started),
                ("bot.stopped", self._handle_bot_stopped),
                ("bot.error", self._handle_bot_error),
            ]
            for queue_name, handler in queues:
                task = asyncio.create_task(
                    self._consume_queue(queue_name, handler)
                )
                self.consume_tasks.append(task)
        except Exception as e:
            logger.warning(f"Failed to start RabbitMQ consumer: {e}. Consumer will retry in background.")
            self.running = True
            # Start consumers in background with retry logic
            queues = [
                ("bot.started", self._handle_bot_started),
                ("bot.stopped", self._handle_bot_stopped),
                ("bot.error", self._handle_bot_error),
            ]
            for queue_name, handler in queues:
                task = asyncio.create_task(
                    self._consume_queue(queue_name, handler)
                )
                self.consume_tasks.append(task)

    async def stop(self):
        """Stop consuming messages"""
        self.running = False
        
        # Cancel all consume tasks
        for task in self.consume_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self.consume_tasks:
            await asyncio.gather(*self.consume_tasks, return_exceptions=True)
        
        self.consume_tasks = []
        logger.info("RabbitMQ consumer stopped")

    async def _consume_queue(self, queue_name: str, handler):
        """Consume messages from a queue with retry logic"""
        retry_delay = 1.0  # Start with 1 second delay
        max_retry_delay = 60.0  # Max 60 seconds between retries
        
        while self.running:
            try:
                # Ensure RabbitMQ client is connected
                if self.rabbitmq is None:
                    try:
                        self.rabbitmq = await asyncio.wait_for(
                            get_rabbitmq_client(timeout=5.0),
                            timeout=5.0
                        )
                        logger.info(f"Connected to RabbitMQ, starting consumer for '{queue_name}'")
                        retry_delay = 1.0  # Reset retry delay on success
                    except (asyncio.TimeoutError, Exception) as e:
                        logger.warning(f"Failed to connect to RabbitMQ for queue '{queue_name}': {e}. Retrying in {retry_delay}s...")
                        await asyncio.sleep(retry_delay)
                        retry_delay = min(retry_delay * 2, max_retry_delay)  # Exponential backoff
                        continue
                
                # consume() registers the consumer and runs indefinitely
                # The handler will be called for each message
                await self.rabbitmq.consume(queue_name, handler, durable=True, auto_ack=False)
                # If consume returns (shouldn't happen normally), wait a bit and retry
                await asyncio.sleep(1)
                retry_delay = 1.0  # Reset retry delay on successful consume
            except asyncio.CancelledError:
                logger.info(f"Consume task for queue '{queue_name}' cancelled")
                break
            except Exception as e:
                logger.warning(f"Error consuming from queue '{queue_name}': {e}. Retrying in {retry_delay}s...")
                # Reset connection on error
                self.rabbitmq = None
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_retry_delay)  # Exponential backoff

    async def _handle_bot_started(self, message: dict):
        """Handle bot.started event"""
        try:
            db = next(get_db())
            bot_status_service = BotStatusService(db)
            await bot_status_service.update_status_from_event("bot.started", message)
        except Exception as e:
            logger.error(f"Error handling bot.started event: {e}", exc_info=True)
        finally:
            if 'db' in locals():
                db.close()

    async def _handle_bot_stopped(self, message: dict):
        """Handle bot.stopped event"""
        try:
            db = next(get_db())
            bot_status_service = BotStatusService(db)
            await bot_status_service.update_status_from_event("bot.stopped", message)
        except Exception as e:
            logger.error(f"Error handling bot.stopped event: {e}", exc_info=True)
        finally:
            if 'db' in locals():
                db.close()

    async def _handle_bot_error(self, message: dict):
        """Handle bot.error event"""
        try:
            db = next(get_db())
            bot_status_service = BotStatusService(db)
            await bot_status_service.update_status_from_event("bot.error", message)
        except Exception as e:
            logger.error(f"Error handling bot.error event: {e}", exc_info=True)
        finally:
            if 'db' in locals():
                db.close()


# Global consumer instance
_consumer: Optional[RabbitMQConsumer] = None


async def get_consumer() -> RabbitMQConsumer:
    """Get or create RabbitMQ consumer instance"""
    global _consumer
    if _consumer is None:
        _consumer = RabbitMQConsumer()
    return _consumer

