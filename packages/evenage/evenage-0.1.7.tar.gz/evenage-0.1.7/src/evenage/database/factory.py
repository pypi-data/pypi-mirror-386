"""
Database adapter factory.
"""

from evenage.database.base import DatabaseAdapter, DatabaseConfig
from evenage.database.sqlite import SQLiteAdapter
from evenage.database.postgres import PostgreSQLAdapter
from evenage.database.mysql import MySQLAdapter


def create_database_adapter(config: DatabaseConfig) -> DatabaseAdapter:
    """
    Create a database adapter based on config.
    
    Supported providers:
    - sqlite (default, local-first)
    - postgresql/postgres
    - mysql
    """
    
    adapters = {
        "sqlite": SQLiteAdapter,
        "postgresql": PostgreSQLAdapter,
        "postgres": PostgreSQLAdapter,
        "mysql": MySQLAdapter,
    }
    
    adapter_class = adapters.get(config.provider.lower())
    if not adapter_class:
        raise ValueError(
            f"Unknown database provider: {config.provider}. "
            f"Supported: {', '.join(adapters.keys())}"
        )
    
    return adapter_class(config)
