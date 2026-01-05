# Lazy imports - import only when accessed to avoid circular dependencies
# This allows the module to be imported even if some dependencies are missing

__all__ = [
    'KrakenService',
    'TradingDataService',
    'BotStatusService',
    'RabbitMQConsumer',
    'get_consumer'
]

# Use lazy loading - import on first access
def __getattr__(name):
    """Lazy import for services"""
    if name == 'KrakenService':
        from .kraken_service import KrakenService
        return KrakenService
    elif name == 'TradingDataService':
        from .trading_data_service import TradingDataService
        return TradingDataService
    elif name == 'BotStatusService':
        from .bot_status_service import BotStatusService
        return BotStatusService
    elif name == 'RabbitMQConsumer':
        from .rabbitmq_consumer import RabbitMQConsumer
        return RabbitMQConsumer
    elif name == 'get_consumer':
        from .rabbitmq_consumer import get_consumer
        return get_consumer
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

