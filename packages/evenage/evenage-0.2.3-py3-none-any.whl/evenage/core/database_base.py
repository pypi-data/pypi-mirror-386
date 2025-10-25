"""
Canonical database interfaces for EvenAge (Tier 0).

Expose adapter base types and the high-level DatabaseService from one place so
downstream code can import a single stable path.
"""
from evenage.database.base import (
	DatabaseAdapter as DatabaseAdapterBase,
	DatabaseConfig,
)
from evenage.database.models import DatabaseService

__all__ = [
	"DatabaseAdapterBase",
	"DatabaseConfig",
	"DatabaseService",
]
