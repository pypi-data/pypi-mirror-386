"""
PostgreSQL adapter.
"""

from evenage.database.base import DatabaseAdapter, DatabaseConfig


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL database adapter."""
    
    def get_connection_string(self) -> str:
        """Build PostgreSQL connection string."""
        host = self.config.host or "localhost"
        port = self.config.port or 5432
        user = self.config.username or "postgres"
        password = self.config.password or ""
        database = self.config.database
        
        if password:
            return f"postgresql://{user}:{password}@{host}:{port}/{database}"
        else:
            return f"postgresql://{user}@{host}:{port}/{database}"
