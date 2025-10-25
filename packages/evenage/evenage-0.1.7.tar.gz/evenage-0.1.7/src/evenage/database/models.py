"""
Database models for EvenAge using SQLAlchemy.

Stores traces, job history, and agent metadata.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class AgentTrace(Base):
    """Store agent execution traces."""

    __tablename__ = "agent_traces"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(255), index=True, nullable=False)
    job_id = Column(String(255), index=True)
    agent_name = Column(String(255), index=True, nullable=False)
    status = Column(String(50), nullable=False)
    duration_ms = Column(Integer)
    tokens_used = Column(Integer)
    trace_id = Column(String(255), index=True)
    span_id = Column(String(255))
    parent_span_id = Column(String(255))
    attributes = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class Job(Base):
    """Store job execution history."""

    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(255), unique=True, index=True, nullable=False)
    pipeline_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)  # running, completed, failed, cancelled
    inputs = Column(JSON)
    outputs = Column(JSON)
    error = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime)


class TaskExecution(Base):
    """Store individual task executions."""

    __tablename__ = "task_executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(255), index=True, nullable=False)
    job_id = Column(String(255), index=True, nullable=False)
    task_name = Column(String(255), nullable=False)
    agent_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    input_data = Column(JSON)
    output_data = Column(JSON)
    error = Column(Text)
    duration_ms = Column(Integer)
    tokens_used = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


class AgentRegistry(Base):
    """Store agent registration and status."""

    __tablename__ = "agent_registry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_name = Column(String(255), unique=True, index=True, nullable=False)
    role = Column(String(255))
    status = Column(String(50))  # active, idle, error, offline
    metadata = Column(JSON)
    last_heartbeat = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class DatabaseService:
    """Database service for EvenAge."""

    def __init__(self, database_url: str):
        """
        Initialize database service.

        Args:
            database_url: PostgreSQL connection URL
        """
        self.engine = create_engine(database_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self) -> None:
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        """Get a database session (context manager)."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def save_trace(
        self,
        task_id: str,
        agent_name: str,
        status: str,
        duration_ms: int,
        tokens_used: int = 0,
        job_id: str | None = None,
        trace_id: str | None = None,
        attributes: dict | None = None,
    ) -> None:
        """Save an agent trace to the database."""
        with self.get_session() as session:
            trace = AgentTrace(
                task_id=task_id,
                job_id=job_id,
                agent_name=agent_name,
                status=status,
                duration_ms=duration_ms,
                tokens_used=tokens_used,
                trace_id=trace_id,
                attributes=attributes or {},
            )
            session.add(trace)

    def create_job(
        self,
        job_id: str,
        pipeline_name: str,
        inputs: dict | None = None,
    ) -> None:
        """Create a new job record."""
        with self.get_session() as session:
            job = Job(
                job_id=job_id,
                pipeline_name=pipeline_name,
                status="running",
                inputs=inputs or {},
            )
            session.add(job)

    def update_job_status(
        self,
        job_id: str,
        status: str,
        outputs: dict | None = None,
        error: str | None = None,
    ) -> None:
        """Update job status."""
        with self.get_session() as session:
            job = session.query(Job).filter_by(job_id=job_id).first()
            if job:
                job.status = status
                if outputs:
                    job.outputs = outputs
                if error:
                    job.error = error
                if status in ("completed", "failed", "cancelled"):
                    job.completed_at = datetime.utcnow()
