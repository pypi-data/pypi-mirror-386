"""
CLI commands for EvenAge.

Provides all CLI commands for project management.
"""

from .add import add
from .init import init
from .management import logs, ps, scale, stop
from .run import run, run_dev_alias

__all__ = [
    "add",
    "init",
    "logs",
    "ps",
    "run",
    "run_dev_alias",
    "scale",
    "stop",
]
