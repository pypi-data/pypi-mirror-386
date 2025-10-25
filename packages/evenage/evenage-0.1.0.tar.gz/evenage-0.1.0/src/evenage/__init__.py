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

__version__ = "0.1.0"

from evenage.core.agent import Agent
from evenage.core.task import Task
from evenage.core.controller import Controller
from evenage.core.config import EvenAgeConfig, ProjectConfig

__all__ = [
    "Agent",
    "Task",
    "Controller",
    "EvenAgeConfig",
    "ProjectConfig",
]
