"""
SQLite adapter - Local-first default.
"""

from evenage.database.base import DatabaseAdapter, DatabaseConfig


class SQLiteAdapter(DatabaseAdapter):
    """SQLite database adapter."""
    
    def get_connection_string(self) -> str:
        """Build SQLite connection string."""
        return f"sqlite:///{self.config.database}"
