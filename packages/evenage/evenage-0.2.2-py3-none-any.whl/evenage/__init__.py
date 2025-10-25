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

__version__ = "0.2.2"

# Core exports for user code (canonical base paths)
from evenage.core.agent_base import AgentBase as Agent
from evenage.core.message_bus_base import (
    MessageBusBase as MessageBus,
    TaskMessage,
    ResponseMessage,
)
from evenage.core.config import EvenAgeConfig

__all__ = [
    "Agent",
    "MessageBus",
    "TaskMessage",
    "ResponseMessage",
    "EvenAgeConfig",
]
