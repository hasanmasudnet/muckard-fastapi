from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import settings
import sys
import os
import asyncio
import logging

# Add parent app to path for shared utilities
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# Add current directory to path for local service imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import routers from parent app (will be adapted later)
try:
    from app.api.v1 import kraken, trading_data, bot_status, dashboard, admin
    # Create router instances
    restapi_router = kraken.router  # Assuming this exists
    kraken_router = kraken.router
    trading_router = trading_data.router
    bot_status_router = bot_status.router
    dashboard_router = dashboard.router
    admin_router = admin.router
except ImportError:
    # Create placeholder routers if imports fail
    from fastapi import APIRouter
    restapi_router = APIRouter()
    kraken_router = APIRouter()
    trading_router = APIRouter()
    bot_status_router = APIRouter()
    dashboard_router = APIRouter()
    admin_router = APIRouter()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage service lifecycle"""
    # Startup
    logger.info("Starting Kraken Service...")
    
    # Initialize app state
    app.state.rabbitmq_consumer = None
    app.state.kafka_consumer = None
    
    # Start RabbitMQ consumer for bot result events
    logger.info("Initializing RabbitMQ consumer...")
    
    # Wrap entire RabbitMQ initialization in timeout to ensure we don't block forever
    async def init_rabbitmq():
        try:
            # Import from local services directory
            # Since we're running from kraken-service directory, services is a subdirectory
            from services import get_consumer
            consumer = await get_consumer()
            
            # Start with timeout to prevent hanging
            try:
                await asyncio.wait_for(consumer.start(timeout=5.0), timeout=10.0)
                app.state.rabbitmq_consumer = consumer
                logger.info("✅ RabbitMQ consumer started for bot result events")
            except asyncio.TimeoutError as e:
                logger.warning("⚠️  RabbitMQ consumer startup timed out. Consumer will retry in background.")
                app.state.rabbitmq_consumer = consumer  # Still set it so shutdown can handle it
            except Exception as e:
                logger.warning(f"⚠️  RabbitMQ consumer startup failed: {e}. Consumer will retry in background.")
                app.state.rabbitmq_consumer = consumer  # Still set it so shutdown can handle it
        except ImportError as e:
            logger.warning(f"⚠️  RabbitMQ consumer module not available: {e}. Continuing without RabbitMQ.")
        except Exception as e:
            logger.warning(f"⚠️  Failed to initialize RabbitMQ consumer: {e}. Continuing without RabbitMQ.")
    
    try:
        await asyncio.wait_for(init_rabbitmq(), timeout=15.0)
    except asyncio.TimeoutError:
        logger.warning("⚠️  RabbitMQ consumer initialization timed out (global timeout). Continuing without RabbitMQ.")
    except Exception as e:
        logger.warning(f"⚠️  RabbitMQ consumer initialization failed: {e}. Continuing without RabbitMQ.")
    
    # Start Kafka consumer for user.created and trade events
    logger.info("Initializing Kafka consumer...")
    
    # Wrap entire Kafka initialization in timeout to ensure we don't block forever
    async def init_kafka():
        try:
            from app.utils.kafka_consumer import get_kafka_consumer
            from app.config import settings as app_settings
            from confluent_kafka import KafkaException
            
            # Check if Kafka is enabled
            kafka_enabled = getattr(app_settings, 'KAFKA_ENABLED', False)
            if not kafka_enabled:
                logger.info("ℹ️  Kafka is disabled, skipping Kafka consumer startup")
                return
            
            from database import get_db
            # Import from local services directory
            from services import BotStatusService
            import uuid
            
            # Wrap Kafka consumer initialization in timeout
            try:
                kafka_consumer = await asyncio.wait_for(
                    get_kafka_consumer(),
                    timeout=5.0
                )
            except asyncio.TimeoutError as e:
                logger.warning("Kafka consumer initialization timed out. Continuing without Kafka.")
                kafka_consumer = None
            except (KafkaException, Exception) as e:
                logger.warning(f"Failed to initialize Kafka consumer: {e}. Continuing without Kafka.")
                kafka_consumer = None
            
            if kafka_consumer is not None:
                async def handle_user_created(event_type: str, message: dict):
                    """Handle user.created event from Kafka to initialize bot status"""
                    try:
                        db = next(get_db())
                        bot_status_service = BotStatusService(db)
                        user_id = uuid.UUID(message.get("user_id"))
                        await bot_status_service.initialize_bot_status_for_user(user_id)
                        logger.info(f"Initialized bot status for user {user_id}")
                    except Exception as e:
                        logger.error(f"Error handling user.created event: {e}", exc_info=True)
                    finally:
                        if 'db' in locals():
                            db.close()
                
                async def handle_trade_executed(event_type: str, message: dict):
                    """Handle bot.trade.executed event from Kafka"""
                    try:
                        db = next(get_db())
                        bot_status_service = BotStatusService(db)
                        await bot_status_service.update_status_from_event("bot.trade.executed", message)
                    except Exception as e:
                        logger.error(f"Error handling bot.trade.executed event: {e}", exc_info=True)
                    finally:
                        if 'db' in locals():
                            db.close()
                
                async def handle_trade_skipped(event_type: str, message: dict):
                    """Handle bot.trade.skipped event from Kafka"""
                    try:
                        db = next(get_db())
                        bot_status_service = BotStatusService(db)
                        await bot_status_service.update_status_from_event("bot.trade.skipped", message)
                    except Exception as e:
                        logger.error(f"Error handling bot.trade.skipped event: {e}", exc_info=True)
                    finally:
                        if 'db' in locals():
                            db.close()
                
                # Start consuming from Kafka topics (non-blocking)
                topics = [
                    (app_settings.KAFKA_USER_EVENTS_TOPIC, handle_user_created, "kraken-service", "user.created"),
                    (app_settings.KAFKA_TRADING_EVENTS_TOPIC, handle_trade_executed, "kraken-service", "bot.trade.executed"),
                    (app_settings.KAFKA_TRADING_EVENTS_TOPIC, handle_trade_skipped, "kraken-service", "bot.trade.skipped"),
                ]
                
                try:
                    # Start consuming in background (non-blocking - creates tasks and returns immediately)
                    # Give it a small timeout just in case, but it should return instantly
                    try:
                        await asyncio.wait_for(kafka_consumer.start_consuming(topics), timeout=1.0)
                    except asyncio.TimeoutError:
                        # This shouldn't happen, but if it does, continue anyway
                        logger.warning("⚠️  Kafka consumer start_consuming timed out (unexpected). Continuing anyway.")
                    app.state.kafka_consumer = kafka_consumer
                    logger.info("✅ Started Kafka consumers for user.created and trade events")
                except Exception as e:
                    logger.warning(f"⚠️  Failed to start Kafka consumers: {e}. Continuing without Kafka.")
                    # Set consumer anyway so shutdown can handle it
                    app.state.kafka_consumer = kafka_consumer
        except ImportError as e:
            logger.warning(f"⚠️  Kafka consumer not available: {e}. Continuing without Kafka.")
        except Exception as e:
            logger.warning(f"⚠️  Failed to start Kafka consumers: {e}. Continuing without Kafka.")
    
    try:
        await asyncio.wait_for(init_kafka(), timeout=15.0)
    except asyncio.TimeoutError:
        logger.warning("⚠️  Kafka consumer initialization timed out (global timeout). Continuing without Kafka.")
    except Exception as e:
        logger.warning(f"⚠️  Kafka consumer initialization failed: {e}. Continuing without Kafka.")
    
    # Always log successful service startup, even if some consumers failed
    logger.info("=" * 70)
    logger.info("✅ Kraken Service started successfully")
    logger.info(f"   - RabbitMQ Consumer: {'✅ Active' if app.state.rabbitmq_consumer else '⚠️  Not available'}")
    logger.info(f"   - Kafka Consumer: {'✅ Active' if app.state.kafka_consumer else '⚠️  Not available'}")
    logger.info("=" * 70)
    
    # CRITICAL: Always yield to allow service to start, even if consumers failed
    yield
    
    # Shutdown
    logger.info("Shutting down Kraken Service...")
    try:
        if hasattr(app.state, 'rabbitmq_consumer') and app.state.rabbitmq_consumer is not None:
            try:
                await app.state.rabbitmq_consumer.stop()
                logger.info("✅ RabbitMQ consumer stopped")
            except Exception as e:
                logger.warning(f"⚠️  Error stopping RabbitMQ consumer: {e}")
    except Exception as e:
        logger.warning(f"⚠️  Error during RabbitMQ consumer shutdown: {e}")
    
    try:
        if hasattr(app.state, 'kafka_consumer') and app.state.kafka_consumer is not None:
            try:
                await app.state.kafka_consumer.stop()
                logger.info("✅ Kafka consumer stopped")
            except Exception as e:
                logger.warning(f"⚠️  Error stopping Kafka consumer: {e}")
    except Exception as e:
        logger.warning(f"⚠️  Error during Kafka consumer shutdown: {e}")
    
    logger.info("✅ Kraken Service stopped")

app = FastAPI(title="muckard - kraken service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Match muckard-backend route pattern
app.include_router(restapi_router, prefix="/kraken/api/v1/restapi", tags=["Kraken REST API"])
app.include_router(kraken_router, prefix="/api/v1/kraken", tags=["Kraken Keys"])
app.include_router(trading_router, prefix="/api/v1/trading", tags=["Trading Data"])
app.include_router(bot_status_router, prefix="/api/v1/bot", tags=["Bot Status"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"])

@app.get("/kraken", tags=["Health Check"])
async def health_check():
    return {"status": "ok", "message": "Kraken service is running"}
