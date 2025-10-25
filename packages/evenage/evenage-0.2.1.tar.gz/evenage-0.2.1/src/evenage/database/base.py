"""
Base database adapter interface.
"""

from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine


class DatabaseConfig(BaseModel):
    """Configuration for database adapters."""
    
    provider: str = "sqlite"  # Default to SQLite for local-first
    host: Optional[str] = None
    port: Optional[int] = None
    database: str = "evenage.db"
    username: Optional[str] = None
    password: Optional[str] = None
    pool_size: int = 5
    max_overflow: int = 10
    echo: bool = False


class DatabaseAdapter(ABC):
    """Base class for database adapters."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None
    
    @abstractmethod
    def get_connection_string(self) -> str:
        """Build connection string for the database."""
        pass
    
    def connect(self) -> None:
        """Initialize database connection."""
        connection_string = self.get_connection_string()
        
        self.engine = create_engine(
            connection_string,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            echo=self.config.echo,
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def get_session(self) -> Session:
        """Get a database session."""
        if not self.SessionLocal:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.SessionLocal()
    
    def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            session = self.get_session()
            session.execute("SELECT 1")
            session.close()
            return True
        except:
            return False
    
    def close(self) -> None:
        """Close database connections."""
        if self.engine:
            self.engine.dispose()
