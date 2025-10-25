"""
Database adapters for EvenAge.
Supports multiple databases with SQLite as local-first default.
"""

from evenage.database.base import DatabaseAdapter, DatabaseConfig
from evenage.database.factory import create_database_adapter

__all__ = ["DatabaseAdapter", "DatabaseConfig", "create_database_adapter"]
