"""
EvenAge - A transparent, Docker-native, observable, distributed agent framework.

EvenAge is a superset of CrewAI that removes excessive abstractions and introduces:
- Real distributed runtime with Redis message bus
- Docker-first execution model
- Full OpenTelemetry observability
- Local Prometheus metrics
- Explicit agent-to-agent communication
- Pluggable storage, queues, and LLMs
"""

__version__ = "0.2.0"

# Core exports for user code
from evenage.core.agent import Agent
from evenage.core.message_bus import MessageBus, TaskMessage, ResponseMessage
from evenage.core.config import EvenAgeConfig

__all__ = [
    "Agent",
    "MessageBus",
    "TaskMessage",
    "ResponseMessage",
    "EvenAgeConfig",
]
