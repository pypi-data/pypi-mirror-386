"""
MySQL adapter.
"""

from evenage.database.base import DatabaseAdapter, DatabaseConfig


class MySQLAdapter(DatabaseAdapter):
    """MySQL database adapter."""
    
    def get_connection_string(self) -> str:
        """Build MySQL connection string."""
        host = self.config.host or "localhost"
        port = self.config.port or 3306
        user = self.config.username or "root"
        password = self.config.password or ""
        database = self.config.database
        
        if password:
            return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
        else:
            return f"mysql+pymysql://{user}@{host}:{port}/{database}"
