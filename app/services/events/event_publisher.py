"""Abstract event publisher interface"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class EventPublisher(ABC):
    """Abstract event publisher - can be swapped between implementations"""
    
    @abstractmethod
    async def publish(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        """
        Publish an event
        
        Args:
            event_type: Type of event (e.g., "onboarding.completed")
            event_data: Event data dictionary
            
        Returns:
            bool: True if event published successfully, False otherwise
        """
        pass
    
    def flush(self, timeout: float = 10.0):
        """
        Flush pending messages (for implementations that buffer)
        
        Args:
            timeout: Maximum time to wait for flush
        """
        pass


class NoOpEventPublisher(EventPublisher):
    """No-op event publisher for development/testing when Kafka is disabled"""
    
    async def publish(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        """No-op implementation - does nothing"""
        return True

